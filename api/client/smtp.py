import os
import logging
from dataclasses import dataclass
import aiosmtplib
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.utils import formataddr
from email.header import Header
from email.mime.multipart import MIMEMultipart as _MIMEMultipart

from utils.error import MailSourceError



@dataclass
class SMTPClient:
    _config = None

    @classmethod
    def set_config(cls):
        if not cls._config:
            cls._config = {
                "smtp_server" : os.getenv("SMTP_SERVER"),
                "smtp_port" : int(os.getenv("SMTP_PORT")),
                "smtp_user" : os.getenv("EMAIL_USER"),
                "smtp_password" : os.getenv("EMAIL_PASSWORD")
            }

        for key, value in cls._config.items():
            if value is None:
                raise MailSourceError(f"SMTP env is missing: {key}")


    @staticmethod
    def _smtp_kwargs(config: dict) -> dict:
        """config: host, port, use_ssl(465 implicit TLS), use_tls(STARTTLS), username, password"""
        return {"hostname": config["host"], "port": int(config["port"]), "use_tls": bool(config.get("use_ssl")), "timeout": 20}


    @classmethod
    async def _connect(cls, config: dict) -> aiosmtplib.SMTP:
        server = aiosmtplib.SMTP(**cls._smtp_kwargs(config))
        await server.connect()
        if config.get("use_tls") and not config.get("use_ssl"):
            try:
                await server.starttls()
            except aiosmtplib.SMTPException as e:
                if "already using TLS" not in str(e):
                    raise
        if config.get("username"):
            await server.login(config["username"], config.get("password") or "")
        return server


    @classmethod
    async def test_connection(cls, config: dict) -> dict:
        """접속·로그인만 확인한다. 자격증명은 메시지에 넣지 않는다."""
        try:
            server = await cls._connect(config)
            try:
                return {"ok": True, "host": config["host"], "port": int(config["port"]), "authenticated": bool(config.get("username"))}
            finally:
                try:
                    await server.quit()
                except Exception:
                    pass
        except aiosmtplib.SMTPAuthenticationError as e:
            raise MailSourceError(f"SMTP authentication failed: {e.code} {e.message}") from e
        except (aiosmtplib.SMTPException, OSError) as e:
            raise MailSourceError(f"SMTP connection failed: {e}") from e


    @classmethod
    async def send_raw(cls, config: dict, message: _MIMEMultipart, sender: str, recipients: list[str]) -> None:
        """조립된 MIME 을 설정된 SMTP 서버로 보낸다."""
        try:
            server = await cls._connect(config)
            try:
                await server.send_message(message, sender=sender, recipients=recipients)
            finally:
                try:
                    await server.quit()
                except Exception:
                    pass
            logging.info(f"[client.smtp.SMTPClient.send_raw] ✅ sent to {len(recipients)} recipient(s)")
        except aiosmtplib.SMTPAuthenticationError as e:
            logging.error(f"[client.smtp.SMTPClient.send_raw] 🔴 authentication failed: {e.code}")
            raise MailSourceError(f"SMTP authentication failed: {e.code} {e.message}") from e
        except aiosmtplib.SMTPRecipientsRefused as e:
            logging.error(f"[client.smtp.SMTPClient.send_raw] 🔴 recipients refused: {e}")
            raise MailSourceError(f"SMTP recipients refused: {e}") from e
        except (aiosmtplib.SMTPException, OSError) as e:
            logging.error(f"[client.smtp.SMTPClient.send_raw] 🔴 {e}")
            raise MailSourceError(f"SMTP send failed: {e}") from e


    @classmethod
    async def send_email(cls, data):
        try:
            cls.set_config()

            message = MIMEMultipart("alternative")
            message["Reply-To"] = data.get("from")
            message["To"] = ", ".join(data.get("to")) if isinstance(data.get("to"), list) else data.get("to")
            message["Subject"] = data.get("subject")
            display_name = data.get('from_name', 'LLM Platform support team')
            if any(ord(char) > 127 for char in display_name):  # check not ASCII
                encoded_name = Header(display_name, 'utf-8').encode()
                message["From"] = f"{encoded_name} <{cls._config['smtp_user']}>"
            else:
                message["From"] = formataddr((display_name, cls._config['smtp_user']))

            if data.get("cc"):
                message["Cc"] = ", ".join(data.get("cc"))

            msg_alternative = MIMEMultipart("alternative")
            if data.get("is_html"):
                html_part = MIMEText(data.get("content"), "html", "utf-8")
                msg_alternative.attach(html_part)
            else:
                text_part = MIMEText(data.get("content"), "plain", "utf-8")
                msg_alternative.attach(text_part)
            message.attach(msg_alternative)

            if data.get("attachments"):
                for filename, file_content in data.get("attachments"):
                    cls._attach_file(message, file_content, filename)
                    logging.info(f"success to add file on attachments: {filename}")

            recipients = data.get("to") if isinstance(data.get("to"), list) else [data.get("to")]
            if data.get("cc"):
                recipients.extend(data.get("cc"))
            if data.get("bcc"):
                recipients.extend(data.get("bcc"))

            logging.info(f"address to send: {recipients}")
            async with aiosmtplib.SMTP(hostname=cls._config["smtp_server"], port=cls._config["smtp_port"]) as server:
                try:
                    await server.starttls()
                except aiosmtplib.SMTPException as e:
                    if "already using TLS" in str(e):
                        logging.info("TLS already active, skipping starttls()")
                    else:
                        logging.error(f"[client.smtp.send_email] aiosmtplib.SMTPException: {str(e)}")
                        raise e
                await server.login(cls._config["smtp_user"], cls._config["smtp_password"])
                await server.send_message(message, recipients=recipients)
            logging.info("success to send")

        except aiosmtplib.SMTPAuthenticationError as e:
            err_message = f"[client.smtp.send_email] aiosmtplib.SMTPAuthenticationError: Fail to get SMTP auth - check account and password: {str(e)}"
            logging.error(err_message)
            raise Exception(err_message)
        except aiosmtplib.SMTPRecipientsRefused as e:
            err_message = f"[client.smtp.send_email] aiosmtplib.SMTPRecipientsRefused: to_email address reject to receive email. {str(e)}"
            logging.error(err_message)
            raise Exception(err_message)
        except Exception as e:
            err_message = f"[client.smtp.send_email] Exception: Fail to send EMAIL: {str(e)}"
            logging.error(err_message)
            raise Exception(err_message)


    @classmethod
    def _attach_file(cls, message: MIMEMultipart, file_content: bytes, filename: str):
        content_type, encoding = mimetypes.guess_type(filename)

        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'

        main_type, sub_type = content_type.split('/', 1)

        if main_type == 'text':
            attachment = MIMEText(file_content.decode('utf-8'), _subtype=sub_type)
        elif main_type == 'image':
            attachment = MIMEImage(file_content, _subtype=sub_type)
        elif main_type == 'audio':
            attachment = MIMEAudio(file_content, _subtype=sub_type)
        else:
            attachment = MIMEApplication(file_content, _subtype=sub_type)

        attachment.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(attachment)