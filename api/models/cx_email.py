from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, func, Boolean
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship

from . import Base



class CxEmail(Base):
    __tablename__ = "cx_email"
    # Columns
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_id = Column(String(255), nullable=True)
    subject = Column(String(255), nullable=True)
    from_mail = Column(String(255), nullable=True)
    from_name = Column(String(255), nullable=True)
    to_mail = Column(String(255), nullable=True)
    to_name = Column(String(255), nullable=True)
    cc_mail = Column(LONGTEXT, nullable=True)
    cc_name = Column(LONGTEXT, nullable=True)
    received_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    content = Column(LONGTEXT, nullable=True)
    references = Column(LONGTEXT, nullable=True)
    status = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.now, server_default=func.now())
    company = Column(String(255), nullable=True)
    keyword = Column(String(255), nullable=True)
    last_content = Column(LONGTEXT, nullable=True)
    comment = Column(LONGTEXT, nullable=True)
    manager = Column(String(255), nullable=True)
    answering_content = Column(LONGTEXT, nullable=True)
    company_key = Column(String(40), nullable=False)
    html_s3_key = Column(String(255), nullable=True)
    attachments = Column(LONGTEXT, nullable=True)
    to_name_list = Column(LONGTEXT, nullable=True)  # 수신자 이름 목록(list repr)
    to_mail_list = Column(LONGTEXT, nullable=True)  # 수신자 주소 목록(list repr)
    cid_images = Column(LONGTEXT, nullable=True)
    issue_status = Column(Integer, server_default="0")
    has_temp = Column(Boolean, server_default="0")

    company_info = relationship("CompanyInfo", backref="cx_email")
    user_info = relationship("UserInfo", backref="cx_email")



    @property
    def serialize(self):
        return {
            "id": self.id,
            "message_id": self.message_id,
            "subject": self.subject,
            "from_mail": self.from_mail,
            "from_name": self.from_name,
            "to_mail": self.to_mail,
            "to_name": self.to_name,
            "cc_mail": self.cc_mail,
            "cc_name": self.cc_name,
            "received_at": self.received_at,
            "processed_at": self.processed_at,
            "content": self.content,
            "references": self.references,
            "status": self.status,
            "created_at": self.created_at,
            "company": self.company,
            "keyword": self.keyword,
            "last_content": self.last_content,
            "comment": self.comment,
            "manager": self.manager,
            "answering_content": self.answering_content,
            "company_key": self.company_key,
            "html_s3_key": self.html_s3_key,
            "attachments": self.attachments,
            "manager_id": self.manager_id
        }