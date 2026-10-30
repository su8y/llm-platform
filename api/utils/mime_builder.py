"""발신 MIME 조립. SES raw 발송과 SMTP 발송이 같은 메시지를 만들도록 한 곳에 둔다."""
import mimetypes
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, make_msgid


def format_address(address: str, name: str | None = None) -> str:
    if not name:
        return address
    if any(ord(char) > 127 for char in name):
        return f"{Header(name, 'utf-8').encode()} <{address}>"
    return formataddr((name, address))


def build_raw_message(
    from_address: str, to_address_list: list[str], subject: str, body_html: str,
    attachments: list[dict] | None = None, cc_address_list: list[str] | None = None, bcc_address_list: list[str] | None = None,
    in_reply_to: str | None = None, references: list[str] | None = None, image_data: list[dict] | None = None,
    from_name: str | None = None, reply_to: str | None = None, message_id: str | None = None,
) -> MIMEMultipart:
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = format_address(from_address, from_name)
    msg["To"] = ", ".join(to_address_list)
    if cc_address_list:
        msg["Cc"] = ", ".join(cc_address_list)
    if bcc_address_list:
        msg["Bcc"] = ", ".join(bcc_address_list)
    if reply_to and reply_to != from_address:
        msg["Reply-To"] = reply_to
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = " ".join(references)
    if message_id:
        msg["Message-ID"] = message_id

    alt_part = MIMEMultipart("alternative")
    alt_part.attach(MIMEText(body_html, "html", "utf-8"))
    msg.attach(alt_part)

    for image in image_data or []:
        mime_subtype = image.get("mimeType", "image/png").split("/")[-1]
        image_part = MIMEBase("image", mime_subtype)
        image_part.set_payload(image["image"])
        image_part.add_header("Content-ID", f'<{image["cid"]}>')
        image_part.add_header("Content-Disposition", "inline", filename=image["filename"])
        image_part.add_header("Content-Transfer-Encoding", "base64")
        msg.attach(image_part)

    for file in attachments or []:
        filename = file.get("filename", "attachment")
        content_type, _ = mimetypes.guess_type(filename)
        if content_type is None:
            content_type = file.get("content_type", "application/octet-stream")
        part = MIMEApplication(file["file_data"], _subtype=content_type.split("/")[-1])
        part.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(part)
    return msg


def new_message_id(from_address: str) -> str:
    """SMTP 발송은 서버가 Message-ID 를 주지 않으므로 직접 만든다. 스레드 추적(references)에 쓰인다."""
    domain = from_address.split("@")[-1] if "@" in from_address else "llm-platform.local"
    return make_msgid(domain=domain)
