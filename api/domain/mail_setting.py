from datetime import datetime

from pydantic import BaseModel


class MailSettingDomain(BaseModel):
    company_key: str
    source_type: str
    is_active: bool = True
    poll_interval_sec: int = 60

    imap_host: str | None = None
    imap_port: int | None = None
    imap_use_ssl: bool = True
    imap_username: str | None = None
    imap_password: str | None = None          # 평문(요청에서만 존재). 저장 시 암호화
    imap_folder: str | None = "INBOX"

    ses_region: str | None = None
    ses_bucket: str | None = None
    ses_prefix: str | None = None
    ses_access_key: str | None = None
    ses_secret_key: str | None = None         # 평문(요청에서만 존재)

    existing_row: dict | None = None
    test_result: dict | None = None
    now: datetime | None = None


class SmtpSettingDomain(BaseModel):
    company_key: str
    is_active: bool = True
    smtp_host: str
    smtp_port: int = 587
    smtp_use_ssl: bool = False
    smtp_use_tls: bool = True
    smtp_username: str | None = None
    smtp_password: str | None = None        # 평문(요청에서만). 저장 시 암호화
    from_address: str
    from_name: str | None = None

    existing_row: dict | None = None
    test_result: dict | None = None
    now: datetime | None = None
