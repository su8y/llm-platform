"""SMTP 발신 설정·MIME 조립 단위 테스트 (네트워크 없음)."""
import os
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, patch

os.environ.setdefault("SECRET_KEY", "unit-test-secret")

from utils.mime_builder import build_raw_message, format_address, new_message_id


class MimeBuilderTests(TestCase):
    def test_headers_threading_and_parts(self) -> None:
        msg = build_raw_message(
            from_address="cs@example.test", from_name="고객센터", to_address_list=["a@x.test"], cc_address_list=["c@x.test"],
            subject="Re: 문의", body_html="<p>답변</p>", attachments=[{"filename": "견적.pdf", "file_data": b"%PDF", "content_type": "application/pdf"}],
            in_reply_to="<q1@x.test>", references=["<root@x.test>", "<q1@x.test>"], reply_to="support@example.test",
            image_data=[{"cid": "img1", "image": "aGk=", "filename": "img1.png", "mimeType": "image/png"}], message_id="<m1@example.test>",
        )
        self.assertIn("<cs@example.test>", msg["From"]); self.assertIn("=?utf-8?", msg["From"])
        self.assertEqual(msg["To"], "a@x.test"); self.assertEqual(msg["Cc"], "c@x.test")
        self.assertEqual(msg["Reply-To"], "support@example.test")
        self.assertEqual(msg["In-Reply-To"], "<q1@x.test>"); self.assertEqual(msg["References"], "<root@x.test> <q1@x.test>")
        self.assertEqual(msg["Message-ID"], "<m1@example.test>")
        types = [part.get_content_type() for part in msg.walk()]
        self.assertIn("text/html", types); self.assertIn("image/png", types); self.assertIn("application/pdf", types)

    def test_reply_to_omitted_when_same_as_from(self) -> None:
        msg = build_raw_message(from_address="cs@example.test", to_address_list=["a@x.test"], subject="s", body_html="b", reply_to="cs@example.test")
        self.assertIsNone(msg["Reply-To"])
        self.assertEqual(format_address("cs@example.test", "Support"), "Support <cs@example.test>")
        self.assertTrue(new_message_id("cs@example.test").endswith("@example.test>"))


class SmtpSendHelperTests(IsolatedAsyncioTestCase):
    async def test_send_by_smtp_setting_uses_real_recipients_and_sets_message_id(self) -> None:
        from domain.email import SendEmailDomain
        from helper.email import helper_send_email_send_mail_by_smtp_setting

        domain = SendEmailDomain(
            id=1, company_key="ck", server_stage="docker", reply_to=["a@x.test"], reply_cc="c@x.test", reply_bcc=None,
            reply_from="support@example.test", reply_from_name="지원팀", reply_subject="Re: 문의", email_html="<p>hi</p>",
            from_message_id="q1@x.test", references=["<root@x.test>"],
            smtp_config={"host": "h", "port": 587, "use_ssl": False, "use_tls": True, "username": "u", "password": "p", "from_address": "cs@example.test", "from_name": None},
        )
        client = AsyncMock()
        await helper_send_email_send_mail_by_smtp_setting(client, domain)
        client.send_raw.assert_awaited_once()
        config, message = client.send_raw.await_args.args[0], client.send_raw.await_args.args[1]
        self.assertEqual(client.send_raw.await_args.kwargs["recipients"], ["a@x.test", "c@x.test"])
        self.assertEqual(client.send_raw.await_args.kwargs["sender"], "cs@example.test")
        self.assertIn("지원팀", str(message["From"]) if "=?utf-8?" not in message["From"] else "지원팀")  # 이름은 reply_from_name 으로 대체
        self.assertEqual(message["In-Reply-To"], "q1@x.test")
        self.assertTrue(domain.to_message_id and "@example.test" in domain.to_message_id)

    async def test_smtp_client_test_connection_wraps_errors(self) -> None:
        from client.smtp import SMTPClient
        from utils.error import MailSourceError

        with patch("client.smtp.aiosmtplib.SMTP") as smtp_cls:
            smtp_cls.return_value.connect = AsyncMock(side_effect=OSError("refused"))
            with self.assertRaises(MailSourceError):
                await SMTPClient.test_connection({"host": "h", "port": 587, "use_ssl": False, "use_tls": True, "username": None, "password": None})
