from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.dialects.mysql import LONGTEXT

from . import Base


class MailReceiveSetting(Base):
    """회사별 메일 수신 설정. 자격증명(password, aws_secret_key)은 utils.crypto 로 암호화해 저장한다."""
    __tablename__ = "mail_receive_setting"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_key = Column(String(40), index=True, nullable=False)
    source_type = Column(String(10), nullable=False)                      # imap | ses
    is_active = Column(Boolean, default=True, server_default="1")
    poll_interval_sec = Column(Integer, default=60, server_default="60")

    # IMAP
    imap_host = Column(String(255), nullable=True)
    imap_port = Column(Integer, nullable=True)
    imap_use_ssl = Column(Boolean, default=True, server_default="1")
    imap_username = Column(String(255), nullable=True)
    imap_password_enc = Column(LONGTEXT, nullable=True)
    imap_folder = Column(String(255), default="INBOX", server_default="INBOX")
    imap_uidvalidity = Column(Integer, nullable=True)
    imap_last_uid = Column(Integer, default=0, server_default="0")

    # SES (수신 규칙이 S3 에 저장한 원문 MIME 을 폴링)
    ses_region = Column(String(40), nullable=True)
    ses_bucket = Column(String(255), nullable=True)
    ses_prefix = Column(String(255), nullable=True)
    ses_access_key = Column(String(255), nullable=True)
    ses_secret_key_enc = Column(LONGTEXT, nullable=True)
    ses_last_modified = Column(DateTime, nullable=True)                   # 마지막으로 처리한 객체의 LastModified(UTC)

    last_polled_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_error = Column(LONGTEXT, nullable=True)
    received_count = Column(Integer, default=0, server_default="0")
    reg_date = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    update_date = Column(DateTime, nullable=True)
