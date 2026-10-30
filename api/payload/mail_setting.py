from pydantic import BaseModel, Field


class upsertMailSettingPayload(BaseModel):
    source_type: str = Field(..., alias="sourceType", description="imap | ses")
    is_active: bool = Field(True, alias="isActive")
    poll_interval_sec: int = Field(60, alias="pollIntervalSec")

    imap_host: str | None = Field(None, alias="imapHost")
    imap_port: int | None = Field(None, alias="imapPort")
    imap_use_ssl: bool = Field(True, alias="imapUseSsl")
    imap_username: str | None = Field(None, alias="imapUsername")
    imap_password: str | None = Field(None, alias="imapPassword", description="비우면 기존 값 유지")
    imap_folder: str | None = Field("INBOX", alias="imapFolder")

    ses_region: str | None = Field(None, alias="sesRegion")
    ses_bucket: str | None = Field(None, alias="sesBucket")
    ses_prefix: str | None = Field(None, alias="sesPrefix")
    ses_access_key: str | None = Field(None, alias="sesAccessKey")
    ses_secret_key: str | None = Field(None, alias="sesSecretKey", description="비우면 기존 값 유지")


class testMailSettingPayload(upsertMailSettingPayload):
    """저장 전 연결 테스트. 비밀번호를 비우면 저장된 값으로 테스트한다."""


class deleteMailSettingPayload(BaseModel):
    source_type: str = Field(..., alias="sourceType")


class upsertSmtpSettingPayload(BaseModel):
    is_active: bool = Field(True, alias="isActive")
    smtp_host: str = Field(..., alias="smtpHost")
    smtp_port: int = Field(587, alias="smtpPort")
    smtp_use_ssl: bool = Field(False, alias="smtpUseSsl", description="465 implicit TLS")
    smtp_use_tls: bool = Field(True, alias="smtpUseTls", description="STARTTLS")
    smtp_username: str | None = Field(None, alias="smtpUsername")
    smtp_password: str | None = Field(None, alias="smtpPassword", description="비우면 기존 값 유지")
    from_address: str = Field(..., alias="fromAddress")
    from_name: str | None = Field(None, alias="fromName")


class testSmtpSettingPayload(upsertSmtpSettingPayload):
    """저장 전 접속 테스트. 비밀번호를 비우면 저장된 값으로 테스트한다."""
