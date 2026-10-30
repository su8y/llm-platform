from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func, Boolean
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship

from . import Base



class EmailSendHistory(Base):
    __tablename__ = "email_send_history"
    # Columns
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_key = Column(String(40), index=True, nullable=False)
    message_id = Column(String(255), nullable=True)
    subject = Column(String(255), nullable=True)
    from_mail = Column(LONGTEXT, nullable=True)
    from_name = Column(LONGTEXT, nullable=True)
    to_mail = Column(LONGTEXT, nullable=True)
    to_name = Column(LONGTEXT, nullable=True)
    cc_mail = Column(LONGTEXT, nullable=True)
    cc_name = Column(LONGTEXT, nullable=True)
    bcc_mail = Column(LONGTEXT, nullable=True)
    bcc_name = Column(LONGTEXT, nullable=True)
    received_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    keyword = Column(String(255), nullable=True)
    comment = Column(LONGTEXT, nullable=True)
    manager = Column(String(255), nullable=True)
    html_s3_key = Column(String(255), nullable=True)
    attachments = Column(LONGTEXT, nullable=True)
    company = Column(String(255), nullable=True)
    in_reply_to = Column(String(255), nullable=True)
    references = Column(LONGTEXT, nullable=True)
    cid_images = Column(LONGTEXT, nullable=True)
    last_content_for_llm = Column(LONGTEXT, nullable=True)
    is_error = Column(Boolean, server_default="1")
    is_bounce = Column(Boolean, server_default="0")
    bounce_type = Column(LONGTEXT, nullable=True)
    bounce_sub_type = Column(LONGTEXT, nullable=True)
    bounced_recipients = Column(LONGTEXT, nullable=True)
    is_on = Column(Boolean, server_default="1")
    is_show = Column(Boolean, server_default="1")

    company_info = relationship("CompanyInfo", backref="cx_email")



    @property
    def serialize(self):
        return {
            "id": self.id,
            "company_key": self.company_key,
            "message_id": self.message_id,
            "subject": self.subject,
            "from_mail": self.from_mail,
            "from_name": self.from_name,
            "to_mail": self.to_mail,
            "to_name": self.to_name,
            "cc_mail": self.cc_mail,
            "cc_name": self.cc_name,
            "received_at": self.received_at,
            "keyword": self.keyword,
            "comment": self.comment,
            "manager": self.manager,
            "html_s3_key": self.html_s3_key,
            "attachments": self.attachments,
            "company": self.company
        }