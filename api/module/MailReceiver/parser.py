"""원문 MIME → cx_email 적재용 dict. 표준 라이브러리만 사용(단위 테스트 가능)."""
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email import message_from_bytes, policy
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import getaddresses, parsedate_to_datetime

THREAD_SPLIT_PATTERNS = [
    r"-----Original Message-----",
    r"^On .+ wrote:$",
    r"^-{2,} ?원본 메일 ?-{2,}$",
    r"^From: .+$",
]


@dataclass
class ParsedAttachment:
    filename: str
    content_type: str
    data: bytes
    content_id: str | None = None


@dataclass
class ParsedMail:
    message_id: str
    subject: str
    from_name: str
    from_mail: str
    to_names: list[str] = field(default_factory=list)
    to_mails: list[str] = field(default_factory=list)
    cc_names: list[str] = field(default_factory=list)
    cc_mails: list[str] = field(default_factory=list)
    received_at: datetime | None = None
    text: str = ""
    html: str | None = None
    references: str | None = None
    in_reply_to: str | None = None
    attachments: list[ParsedAttachment] = field(default_factory=list)

    @property
    def last_content(self) -> str:
        """인용된 이전 스레드를 제외한 최신 본문."""
        text = self.text or ""
        for pattern in THREAD_SPLIT_PATTERNS:
            match = re.search(pattern, text, flags=re.MULTILINE)
            if match and match.start() > 0:
                text = text[:match.start()]
        return text.strip()


def _decode(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value))).strip()
    except Exception:
        return value.strip()


def _addresses(message: EmailMessage, header: str) -> tuple[list[str], list[str]]:
    raw = message.get_all(header, [])
    names, mails = [], []
    for name, mail in getaddresses(raw):
        if not mail:
            continue
        names.append(_decode(name) or mail)
        mails.append(mail.strip().lower())
    return names, mails


def _received_at(message: EmailMessage) -> datetime | None:
    value = message.get("Date")
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def _html_to_text(html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?</\1>", "", html)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&lt;", "<", text); text = re.sub(r"&gt;", ">", text); text = re.sub(r"&amp;", "&", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def parse_raw_mail(raw: bytes, fallback_id: str) -> ParsedMail:
    message: EmailMessage = message_from_bytes(raw, policy=policy.default)
    from_names, from_mails = _addresses(message, "From")
    to_names, to_mails = _addresses(message, "To")
    cc_names, cc_mails = _addresses(message, "Cc")

    text_body, html_body, attachments = "", None, []
    for part in message.walk():
        if part.is_multipart():
            continue
        content_type = part.get_content_type()
        disposition = (part.get("Content-Disposition") or "").lower()
        filename = part.get_filename()
        if filename or disposition.startswith("attachment") or content_type.startswith(("image/", "application/")):
            if not filename and not content_type.startswith("image/"):
                continue
            content_id = (part.get("Content-ID") or "").strip("<>") or None
            attachments.append(ParsedAttachment(
                filename=_decode(filename) or f"{content_id or 'inline'}.{content_type.split('/')[-1]}",
                content_type=content_type,
                data=part.get_payload(decode=True) or b"",
                content_id=content_id,
            ))
            continue
        if content_type == "text/plain" and not text_body:
            text_body = part.get_content().strip()
        elif content_type == "text/html" and html_body is None:
            html_body = part.get_content()
    if not text_body and html_body:
        text_body = _html_to_text(html_body)

    message_id = (message.get("Message-ID") or "").strip().strip("<>") or fallback_id
    return ParsedMail(
        message_id=message_id,
        subject=_decode(message.get("Subject")),
        from_name=from_names[0] if from_names else (from_mails[0] if from_mails else ""),
        from_mail=from_mails[0] if from_mails else "",
        to_names=to_names, to_mails=to_mails, cc_names=cc_names, cc_mails=cc_mails,
        received_at=_received_at(message),
        text=text_body, html=html_body,
        references=(message.get("References") or "").strip() or None,
        in_reply_to=(message.get("In-Reply-To") or "").strip().strip("<>") or None,
        attachments=attachments,
    )
