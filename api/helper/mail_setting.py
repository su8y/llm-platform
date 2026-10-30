import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession

from domain.mail_setting import MailSettingDomain, SmtpSettingDomain
from module.MailReceiver.imap_source import ImapConfig, ImapSource
from module.MailReceiver.ses_source import SesConfig, SesSource
from payload.mail_setting import upsertMailSettingPayload, deleteMailSettingPayload, upsertSmtpSettingPayload
from queries.mail_receive_setting import MailReceiveSettingQuery
from queries.mail_smtp_setting import MailSmtpSettingQuery
from client.smtp import SMTPClient
from utils.constants import MAIL_SOURCE_IMAP, MAIL_SOURCE_SES, MAIL_SOURCE_LIST, MAIL_RECEIVE_MIN_INTERVAL_SEC
from utils.crypto import decrypt_text, encrypt_text
from utils.date import get_utc_now
from utils.error import AppError, DataError, ForbiddenError

PUBLIC_FIELDS = [
    "id", "source_type", "is_active", "poll_interval_sec",
    "imap_host", "imap_port", "imap_use_ssl", "imap_username", "imap_folder", "imap_last_uid",
    "ses_region", "ses_bucket", "ses_prefix", "ses_access_key", "ses_last_modified",
    "last_polled_at", "last_success_at", "last_error", "received_count", "reg_date", "update_date",
]


def helper_mail_setting_check_master(user_info: dict) -> None:
    if user_info.get("user_auth") != 1:
        raise ForbiddenError("Only master can manage mail receive settings")


def helper_mail_setting_make_domain_data(payload: upsertMailSettingPayload, user_info: dict) -> MailSettingDomain:
    if payload.source_type not in MAIL_SOURCE_LIST:
        raise DataError(f"sourceType must be one of {MAIL_SOURCE_LIST}")
    if payload.poll_interval_sec < MAIL_RECEIVE_MIN_INTERVAL_SEC:
        raise DataError(f"pollIntervalSec must be >= {MAIL_RECEIVE_MIN_INTERVAL_SEC}")
    if payload.source_type == MAIL_SOURCE_IMAP:
        if not payload.imap_host or not payload.imap_username:
            raise DataError("imapHost and imapUsername are required")
        if payload.imap_port is None:
            payload.imap_port = 993 if payload.imap_use_ssl else 143
    if payload.source_type == MAIL_SOURCE_SES and (not payload.ses_region or not payload.ses_bucket):
        raise DataError("sesRegion and sesBucket are required")
    return MailSettingDomain(company_key=user_info["company_key"], now=get_utc_now(), **payload.model_dump())


async def helper_mail_setting_merge_secrets(db: AsyncSession, query: MailReceiveSettingQuery, domain_data: MailSettingDomain) -> None:
    """요청에 비밀번호/시크릿이 비어 있으면 저장된 값을 이어 쓴다 (수정 화면에서 비밀번호를 다시 입력하지 않아도 됨)."""
    domain_data.existing_row = await query.get_by_company(db, domain_data.company_key, domain_data.source_type)
    row = domain_data.existing_row
    if row:
        if not domain_data.imap_password:
            domain_data.imap_password = decrypt_text(row.get("imap_password_enc"))
        if not domain_data.ses_secret_key:
            domain_data.ses_secret_key = decrypt_text(row.get("ses_secret_key_enc"))
    if domain_data.source_type == MAIL_SOURCE_IMAP and not domain_data.imap_password:
        raise DataError("imapPassword is required")


def helper_mail_setting_build_source_config(domain_data: MailSettingDomain) -> ImapConfig | SesConfig:
    if domain_data.source_type == MAIL_SOURCE_IMAP:
        return ImapConfig(
            host=domain_data.imap_host, port=domain_data.imap_port, use_ssl=domain_data.imap_use_ssl,
            username=domain_data.imap_username, password=domain_data.imap_password, folder=domain_data.imap_folder or "INBOX",
        )
    return SesConfig(
        region=domain_data.ses_region, bucket=domain_data.ses_bucket, prefix=domain_data.ses_prefix or "",
        access_key=domain_data.ses_access_key, secret_key=domain_data.ses_secret_key,
    )


async def helper_mail_setting_test_connection(domain_data: MailSettingDomain) -> None:
    config = helper_mail_setting_build_source_config(domain_data)
    if domain_data.source_type == MAIL_SOURCE_IMAP:
        domain_data.test_result = await ImapSource.test_connection(config)
    else:
        domain_data.test_result = await SesSource.test_connection(config)


async def helper_mail_setting_upsert(db: AsyncSession, query: MailReceiveSettingQuery, domain_data: MailSettingDomain) -> None:
    values = {
        "company_key": domain_data.company_key,
        "source_type": domain_data.source_type,
        "is_active": domain_data.is_active,
        "poll_interval_sec": domain_data.poll_interval_sec,
        "imap_host": domain_data.imap_host, "imap_port": domain_data.imap_port, "imap_use_ssl": domain_data.imap_use_ssl,
        "imap_username": domain_data.imap_username, "imap_password_enc": encrypt_text(domain_data.imap_password),
        "imap_folder": domain_data.imap_folder or "INBOX",
        "ses_region": domain_data.ses_region, "ses_bucket": domain_data.ses_bucket, "ses_prefix": domain_data.ses_prefix,
        "ses_access_key": domain_data.ses_access_key, "ses_secret_key_enc": encrypt_text(domain_data.ses_secret_key),
        "update_date": domain_data.now,
    }
    row = domain_data.existing_row
    reset_checkpoint = bool(row) and domain_data.source_type == MAIL_SOURCE_IMAP and (
        row.get("imap_host") != domain_data.imap_host or row.get("imap_username") != domain_data.imap_username
        or (row.get("imap_folder") or "INBOX") != (domain_data.imap_folder or "INBOX")
    )
    if row:
        await query.update(db, row["id"], values, reset_checkpoint=reset_checkpoint)
    else:
        values["reg_date"] = domain_data.now
        await query.insert(db, values)
    domain_data.existing_row = await query.get_by_company(db, domain_data.company_key, domain_data.source_type)


def helper_mail_setting_make_public(row: dict | None) -> dict | None:
    """자격증명은 절대 내려보내지 않는다. 저장 여부만 알려준다."""
    if not row:
        return None
    data = {key: row.get(key) for key in PUBLIC_FIELDS}
    data["hasImapPassword"] = bool(row.get("imap_password_enc"))
    data["hasSesSecretKey"] = bool(row.get("ses_secret_key_enc"))
    return data


async def helper_mail_setting_delete(db: AsyncSession, query: MailReceiveSettingQuery, user_info: dict, payload: deleteMailSettingPayload) -> None:
    if payload.source_type not in MAIL_SOURCE_LIST:
        raise DataError(f"sourceType must be one of {MAIL_SOURCE_LIST}")
    await query.delete(db, user_info["company_key"], payload.source_type)


# ---------- SMTP 발신 설정 ----------
SMTP_PUBLIC_FIELDS = ["id", "is_active", "smtp_host", "smtp_port", "smtp_use_ssl", "smtp_use_tls", "smtp_username", "from_address", "from_name", "last_test_at", "last_error", "reg_date", "update_date"]
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def helper_smtp_setting_make_domain_data(payload: upsertSmtpSettingPayload, user_info: dict) -> SmtpSettingDomain:
    if not payload.smtp_host.strip():
        raise DataError("smtpHost is required")
    if not (1 <= payload.smtp_port <= 65535):
        raise DataError("smtpPort must be 1..65535")
    if not EMAIL_PATTERN.match(payload.from_address.strip()):
        raise DataError("fromAddress must be a valid email address")
    if payload.smtp_use_ssl and payload.smtp_use_tls:
        payload.smtp_use_tls = False       # implicit TLS 면 STARTTLS 는 무의미
    return SmtpSettingDomain(company_key=user_info["company_key"], now=get_utc_now(), **payload.model_dump())


async def helper_smtp_setting_merge_secrets(db: AsyncSession, query: MailSmtpSettingQuery, domain_data: SmtpSettingDomain) -> None:
    domain_data.existing_row = await query.get_by_company(db, domain_data.company_key)
    if domain_data.existing_row and not domain_data.smtp_password:
        domain_data.smtp_password = decrypt_text(domain_data.existing_row.get("smtp_password_enc"))
    if domain_data.smtp_username and not domain_data.smtp_password:
        raise DataError("smtpPassword is required when smtpUsername is set")


def smtp_config_from_row(row: dict) -> dict:
    """저장 행 → SMTPClient 설정 dict (비밀번호 복호화 포함)."""
    return {
        "host": row["smtp_host"], "port": row["smtp_port"], "use_ssl": bool(row["smtp_use_ssl"]), "use_tls": bool(row["smtp_use_tls"]),
        "username": row.get("smtp_username"), "password": decrypt_text(row.get("smtp_password_enc")),
        "from_address": row["from_address"], "from_name": row.get("from_name"),
    }


def helper_smtp_setting_build_config(domain_data: SmtpSettingDomain) -> dict:
    return {
        "host": domain_data.smtp_host.strip(), "port": domain_data.smtp_port, "use_ssl": domain_data.smtp_use_ssl, "use_tls": domain_data.smtp_use_tls,
        "username": domain_data.smtp_username or None, "password": domain_data.smtp_password,
        "from_address": domain_data.from_address.strip(), "from_name": domain_data.from_name,
    }


async def helper_smtp_setting_test_connection(db: AsyncSession, query: MailSmtpSettingQuery, domain_data: SmtpSettingDomain) -> None:
    try:
        domain_data.test_result = await SMTPClient.test_connection(helper_smtp_setting_build_config(domain_data))
        if domain_data.existing_row:
            await query.mark_result(db, domain_data.company_key, None, domain_data.now)
    except AppError as e:
        if domain_data.existing_row:
            await query.mark_result(db, domain_data.company_key, getattr(e, "message", str(e)), domain_data.now)
        raise


async def helper_smtp_setting_upsert(db: AsyncSession, query: MailSmtpSettingQuery, domain_data: SmtpSettingDomain) -> None:
    values = {
        "company_key": domain_data.company_key, "is_active": domain_data.is_active,
        "smtp_host": domain_data.smtp_host.strip(), "smtp_port": domain_data.smtp_port,
        "smtp_use_ssl": domain_data.smtp_use_ssl, "smtp_use_tls": domain_data.smtp_use_tls,
        "smtp_username": domain_data.smtp_username or None, "smtp_password_enc": encrypt_text(domain_data.smtp_password),
        "from_address": domain_data.from_address.strip(), "from_name": domain_data.from_name or None,
        "update_date": domain_data.now,
    }
    if domain_data.existing_row:
        await query.update(db, domain_data.existing_row["id"], values)
    else:
        values["reg_date"] = domain_data.now
        await query.insert(db, values)
    domain_data.existing_row = await query.get_by_company(db, domain_data.company_key)


def helper_smtp_setting_make_public(row: dict | None) -> dict | None:
    if not row:
        return None
    data = {key: row.get(key) for key in SMTP_PUBLIC_FIELDS}
    data["hasSmtpPassword"] = bool(row.get("smtp_password_enc"))
    return data
