"""메일 수신 수집기 단위 테스트: MIME 파서와 적재 서비스(외부 IO 는 가짜 객체)."""
import os
from email.message import EmailMessage
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, patch

os.environ.setdefault("SECRET_KEY", "unit-test-secret")

from module.MailReceiver.parser import parse_raw_mail
from utils.crypto import decrypt_text, encrypt_text


def build_mail(html: bool = False, attachment: bool = False, quoted: bool = False) -> bytes:
    message = EmailMessage()
    message["Message-ID"] = "<abc123@example.test>"
    message["Subject"] = "=?utf-8?b?7JWI64WV7ZWY7IS47JqU?="   # 안녕하세요
    message["From"] = "홍길동 <hong@example.test>"
    message["To"] = "CS <cs@company.test>, 담당자 <manager@company.test>"
    message["Cc"] = "cc@company.test"
    message["Date"] = "Wed, 29 Oct 2026 10:00:00 +0900"
    message["References"] = "<root@example.test>"
    body = "문의드립니다.\n제품이 안 켜져요."
    if quoted:
        body += "\n\n-----Original Message-----\nFrom: cs@company.test\n이전 답변 내용"
    if html:
        message.set_content(body)
        message.add_alternative(f"<html><body><p>{body.replace(chr(10), '<br>')}</p></body></html>", subtype="html")
    else:
        message.set_content(body)
    if attachment:
        message.add_attachment(b"%PDF-1.4 fake", maintype="application", subtype="pdf", filename="견적서.pdf")
    return message.as_bytes()


class ParserTests(TestCase):
    def test_parses_headers_addresses_and_body(self) -> None:
        mail = parse_raw_mail(build_mail(), fallback_id="fallback")
        self.assertEqual(mail.message_id, "abc123@example.test")
        self.assertEqual(mail.subject, "안녕하세요")
        self.assertEqual((mail.from_name, mail.from_mail), ("홍길동", "hong@example.test"))
        self.assertEqual(mail.to_mails, ["cs@company.test", "manager@company.test"])
        self.assertEqual(mail.to_names, ["CS", "담당자"])
        self.assertEqual(mail.cc_mails, ["cc@company.test"])
        self.assertEqual(mail.received_at.isoformat(), "2026-10-29T01:00:00")   # UTC naive
        self.assertIn("제품이 안 켜져요", mail.text)
        self.assertEqual(mail.references, "<root@example.test>")

    def test_html_and_attachment(self) -> None:
        mail = parse_raw_mail(build_mail(html=True, attachment=True), fallback_id="fallback")
        self.assertIn("<html>", mail.html)
        self.assertEqual(len(mail.attachments), 1)
        self.assertEqual(mail.attachments[0].filename, "견적서.pdf")
        self.assertEqual(mail.attachments[0].content_type, "application/pdf")

    def test_last_content_strips_quoted_thread(self) -> None:
        mail = parse_raw_mail(build_mail(quoted=True), fallback_id="fallback")
        self.assertIn("제품이 안 켜져요", mail.last_content)
        self.assertNotIn("이전 답변 내용", mail.last_content)

    def test_missing_message_id_uses_fallback(self) -> None:
        raw = build_mail().replace(b"Message-ID: <abc123@example.test>\n", b"")
        self.assertEqual(parse_raw_mail(raw, fallback_id="imap-1-7-42").message_id, "imap-1-7-42")


class CryptoTests(TestCase):
    def test_roundtrip_and_empty(self) -> None:
        self.assertEqual(decrypt_text(encrypt_text("p@ss")), "p@ss")
        self.assertIsNone(encrypt_text(""))
        self.assertIsNone(decrypt_text(None))


class ServiceTests(IsolatedAsyncioTestCase):
    async def test_ingest_skips_duplicate_and_stores_html_and_attachments(self) -> None:
        from module.MailReceiver.service import MailReceiveService

        s3 = AsyncMock()
        service = MailReceiveService(s3_client=s3)
        service.cx_email_query = AsyncMock()
        service.cx_email_query.exists_message_id.return_value = False
        service.cx_email_query.insert_received.return_value = 1

        inserted = await service.ingest_raw(db=None, company_key="ck", raw=build_mail(html=True, attachment=True), fallback_id="f")
        self.assertTrue(inserted)
        self.assertEqual(s3.put_object_to_s3.await_count, 2)            # body.html + 첨부 1
        values = service.cx_email_query.insert_received.await_args.args[1]
        self.assertEqual(values["company_key"], "ck")
        self.assertEqual(values["status"], "parsed")
        self.assertTrue(values["html_s3_key"].startswith("cx-email-html:ck/received/"))
        self.assertEqual(values["to_mail_list"], "['cs@company.test', 'manager@company.test']")
        self.assertIn("'s3Key'", values["attachments"])

        service.cx_email_query.exists_message_id.return_value = True
        self.assertFalse(await service.ingest_raw(db=None, company_key="ck", raw=build_mail(), fallback_id="f"))
        self.assertEqual(service.cx_email_query.insert_received.await_count, 1)

    async def test_poll_imap_records_error_without_raising(self) -> None:
        from module.MailReceiver.service import MailReceiveService
        from utils.error import MailSourceError

        service = MailReceiveService(s3_client=AsyncMock())
        service.setting_query = AsyncMock()
        setting = {"id": 7, "company_key": "ck", "source_type": "imap", "imap_host": "h", "imap_port": 993, "imap_use_ssl": True,
                   "imap_username": "u", "imap_password_enc": encrypt_text("p"), "imap_folder": "INBOX", "imap_last_uid": 0, "imap_uidvalidity": None}
        with patch("module.MailReceiver.service.ImapSource.fetch_new", AsyncMock(side_effect=MailSourceError("login failed"))):
            self.assertEqual(await service.poll_setting(db=None, setting=setting), 0)
        service.setting_query.mark_error.assert_awaited_once()
        self.assertIn("login failed", service.setting_query.mark_error.await_args.args[2])
