"""수신 설정 1건을 한 번 폴링해 새 메일을 cx_email 에 적재한다. IMAP/SES 공통."""
import logging
import re
from datetime import datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from client.aws import CX_S3_BUCKET_NAME, S3Client
from module.MailReceiver.imap_source import ImapConfig, ImapSource
from module.MailReceiver.parser import ParsedMail, parse_raw_mail
from module.MailReceiver.ses_source import SesConfig, SesSource
from queries.cx_email import CXEmailQuery
from queries.mail_receive_setting import MailReceiveSettingQuery
from utils.constants import EMAIL_RECIEVED, MAIL_RECEIVE_FETCH_LIMIT, MAIL_SOURCE_IMAP
from utils.crypto import decrypt_text
from utils.date import get_utc_now
from utils.error import AppError, DBError, MailSourceError


def build_cx_email_values(mail: ParsedMail, company_key: str, html_s3_key: str | None, attachments: list[dict], now: datetime) -> dict:
    """cx_email 컬럼 포맷: 목록은 기존 조회 코드가 ast.literal_eval 로 읽으므로 list repr 로 저장한다."""
    return {
        "company_key": company_key,
        "message_id": mail.message_id[:255],
        "subject": (mail.subject or "(no subject)")[:255],
        "from_mail": mail.from_mail[:255],
        "from_name": (mail.from_name or mail.from_mail)[:255],
        "to_mail": (mail.to_mails[0] if mail.to_mails else "")[:255],
        "to_name": (mail.to_names[0] if mail.to_names else "")[:255],
        "to_mail_list": repr(mail.to_mails),
        "to_name_list": repr(mail.to_names),
        "cc_mail": repr(mail.cc_mails) if mail.cc_mails else None,
        "cc_name": repr(mail.cc_names) if mail.cc_names else None,
        "received_at": mail.received_at or now,
        "content": mail.text,
        "last_content": mail.last_content or mail.text,
        "html_s3_key": html_s3_key,
        "attachments": repr(attachments) if attachments else None,
        "references": mail.references,
        "status": EMAIL_RECIEVED,
    }


class MailReceiveService:
    def __init__(self, s3_client: S3Client | None = None):
        self.s3_client = s3_client or S3Client()
        self.cx_email_query = CXEmailQuery()
        self.setting_query = MailReceiveSettingQuery()

    async def _store_to_s3(self, mail: ParsedMail, company_key: str) -> tuple[str | None, list[dict]]:
        folder = f"{company_key}/received/{uuid4().hex}"
        html_s3_key = None
        if mail.html:
            key = f"{folder}/body.html"
            await self.s3_client.put_object_to_s3(bucket_name=CX_S3_BUCKET_NAME, object_name=key, file_data=mail.html)
            html_s3_key = f"{CX_S3_BUCKET_NAME}:{key}"
        attachments = []
        for index, attachment in enumerate(mail.attachments):
            safe_name = re.sub(r"[\\/\x00-\x1f]", "_", attachment.filename).strip(". ") or f"attachment-{index}"
            key = f"{folder}/attachments/{safe_name}"
            await self.s3_client.put_object_to_s3(bucket_name=CX_S3_BUCKET_NAME, object_name=key, file_data=attachment.data)
            attachments.append({"filename": safe_name, "size": len(attachment.data), "s3Key": key, "contentType": attachment.content_type})
        return html_s3_key, attachments

    async def ingest_raw(self, db: AsyncSession, company_key: str, raw: bytes, fallback_id: str) -> bool:
        """원문 1건 적재. 같은 message_id 가 있으면 건너뛴다(중복 수집 방지). 반환: 적재 여부"""
        mail = parse_raw_mail(raw, fallback_id=fallback_id)
        if await self.cx_email_query.exists_message_id(db, company_key, mail.message_id):
            return False
        html_s3_key, attachments = await self._store_to_s3(mail, company_key)
        await self.cx_email_query.insert_received(db, build_cx_email_values(mail, company_key, html_s3_key, attachments, get_utc_now()))
        return True

    async def poll_setting(self, db: AsyncSession, setting: dict) -> int:
        """설정 1건 폴링. 소스 오류는 last_error 에 기록하고 raise 하지 않는다(다른 회사 수집을 막지 않기 위해)."""
        setting_id, company_key, now = setting["id"], setting["company_key"], get_utc_now()
        try:
            if setting["source_type"] == MAIL_SOURCE_IMAP:
                received = await self._poll_imap(db, setting, company_key, now)
            else:
                received = await self._poll_ses(db, setting, company_key, now)
            if received:
                logging.info(f"[module.MailReceiver.service.MailReceiveService.poll_setting] ✅ setting {setting_id}: received {received}")
            return received
        except (MailSourceError, DBError, AppError) as e:
            detail = getattr(e, "message", None) or str(e)
            logging.error(f"[module.MailReceiver.service.MailReceiveService.poll_setting] 🔴 setting {setting_id}: {detail}")
            await self.setting_query.mark_error(db, setting_id, detail, now)
            return 0
        except Exception as e:
            logging.error(f"[module.MailReceiver.service.MailReceiveService.poll_setting] 🔴 setting {setting_id}: Exception: {e}")
            await self.setting_query.mark_error(db, setting_id, f"Exception: {e}", now)
            return 0

    async def _poll_imap(self, db: AsyncSession, setting: dict, company_key: str, now: datetime) -> int:
        config = ImapConfig(
            host=setting["imap_host"], port=setting["imap_port"] or (993 if setting["imap_use_ssl"] else 143),
            use_ssl=bool(setting["imap_use_ssl"]), username=setting["imap_username"],
            password=decrypt_text(setting["imap_password_enc"]) or "", folder=setting["imap_folder"] or "INBOX",
        )
        last_uid = int(setting["imap_last_uid"] or 0)
        result = await ImapSource.fetch_new(config, last_uid, limit=MAIL_RECEIVE_FETCH_LIMIT)
        if setting["imap_uidvalidity"] and setting["imap_uidvalidity"] != result.uidvalidity and last_uid:
            # 메일함이 재생성돼 UID 가 무효. 처음부터 다시 읽되 message_id 중복은 걸러진다
            logging.warning(f"[module.MailReceiver.service.MailReceiveService._poll_imap] 🔁 UIDVALIDITY changed for setting {setting['id']}, reset checkpoint")
            result = await ImapSource.fetch_new(config, 0, limit=MAIL_RECEIVE_FETCH_LIMIT)
        received = 0
        for uid, raw in result.messages:
            if await self.ingest_raw(db, company_key, raw, fallback_id=f"imap-{setting['id']}-{result.uidvalidity}-{uid}"):
                received += 1
        await self.setting_query.update_imap_checkpoint(db, setting["id"], result.uidvalidity, result.last_uid, received, now)
        return received

    async def _poll_ses(self, db: AsyncSession, setting: dict, company_key: str, now: datetime) -> int:
        config = SesConfig(
            region=setting["ses_region"], bucket=setting["ses_bucket"], prefix=setting["ses_prefix"] or "",
            access_key=setting["ses_access_key"], secret_key=decrypt_text(setting["ses_secret_key_enc"]),
        )
        result = await SesSource.fetch_new(config, setting["ses_last_modified"], limit=MAIL_RECEIVE_FETCH_LIMIT)
        received = 0
        for key, raw, _modified in result.messages:
            if await self.ingest_raw(db, company_key, raw, fallback_id=f"ses-{key}"):
                received += 1
        await self.setting_query.update_ses_checkpoint(db, setting["id"], result.last_modified, received, now)
        return received
