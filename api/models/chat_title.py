from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from . import Base



class ChatTitle(Base):
    __tablename__ = "chat_title"
    session_key = Column(String(40), primary_key=True)
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    title = Column(Text)
    reg_date = Column(DateTime)
    update_date = Column(DateTime)
    user_id = Column(String(20), ForeignKey("user_info.user_id"))

    company = relationship("CompanyInfo", backref="chat_title")
    user_info = relationship("UserInfo", backref="chat_title")

    @property
    def serialize(self):
        return {
            "session_key": self.session_key,
            "company_key": self.company_key,
            "title": self.title,
            "reg_date": self.reg_date,
            "update_date": self.update_date,
            "user_id": self.user_id
        }