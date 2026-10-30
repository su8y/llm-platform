from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.dialects.mysql import LONGTEXT

from . import Base


class MailSmtpSetting(Base):
    """회사별 SMTP 발신 설정(회사당 1행). 비밀번호는 utils.crypto 로 암호화해 저장한다."""
    __tablename__ = "mail_smtp_setting"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_key = Column(String(40), index=True, nullable=False, unique=True)
    is_active = Column(Boolean, default=True, server_default="1")
    smtp_host = Column(String(255), nullable=False)
    smtp_port = Column(Integer, nullable=False, default=587, server_default="587")
    smtp_use_ssl = Column(Boolean, default=False, server_default="0")      # 465 implicit TLS
    smtp_use_tls = Column(Boolean, default=True, server_default="1")       # STARTTLS
    smtp_username = Column(String(255), nullable=True)
    smtp_password_enc = Column(LONGTEXT, nullable=True)
    from_address = Column(String(255), nullable=False)
    from_name = Column(String(255), nullable=True)
    last_test_at = Column(DateTime, nullable=True)
    last_error = Column(LONGTEXT, nullable=True)
    reg_date = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    update_date = Column(DateTime, nullable=True)
