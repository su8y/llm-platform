from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.mysql import LONGTEXT

from . import Base



class CxEmailTemp(Base):
    __tablename__ = "cx_email_temp"
    # Columns
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cx_email_id = Column(Integer, ForeignKey("cx_email.id"), index=True)
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    user_id = Column(String(20))
    reg_date = Column(DateTime)
    update_date = Column(DateTime)
    from_mail = Column(LONGTEXT, nullable=True)
    from_name = Column(LONGTEXT, nullable=True)
    to_mail = Column(LONGTEXT, nullable=True)
    to_name = Column(LONGTEXT, nullable=True)
    cc_mail = Column(LONGTEXT, nullable=True)
    cc_name = Column(LONGTEXT, nullable=True)
    bcc_mail = Column(LONGTEXT, nullable=True)
    bcc_name = Column(LONGTEXT, nullable=True)
    subject = Column(String(255), nullable=True)
    answering_content = Column(LONGTEXT, nullable=True)
    comment = Column(LONGTEXT, nullable=True)
    attachments = Column(LONGTEXT, nullable=True)
    is_create = Column(Boolean, server_default="0")