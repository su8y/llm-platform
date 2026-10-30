from sqlalchemy import Column, Integer, String, DateTime, and_, Text, Boolean, ForeignKey, or_, text
from sqlalchemy.orm import relationship

from . import Base



class InquireHistory(Base):

    """history table for inquire"""
    __tablename__ = "inquire_history"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(40))
    email_address = Column(String(100))
    company_name = Column(String(40), nullable=True)
    purpose_0 = Column(Boolean, default=False, server_default="0")
    purpose_1 = Column(Boolean, default=False, server_default="0")
    purpose_2 = Column(Boolean, default=False, server_default="0")
    purpose_3 = Column(Boolean, default=False, server_default="0")
    purpose_4 = Column(Boolean, default=False, server_default="0")
    purpose_5 = Column(Boolean, default=False, server_default="0")
    purpose_0_content = Column(Text, nullable=True)
    reg_date = Column(DateTime, nullable=False)
    is_success_to_send = Column(Boolean, default=True, server_default="1")
    is_complete = Column(Boolean, default=False, server_default="0")
    lang = Column(String(5))

    @property
    def serialize(self):
        result = {
            "id": self.id,
            "name": self.name,
            "email_address": self.email_address,
            "company_name": self.company_name,
            "purpose_0": self.purpose_0,
            "purpose_1": self.purpose_1,
            "purpose_2": self.purpose_2,
            "purpose_3": self.purpose_3,
            "purpose_4": self.purpose_4,
            "purpose_0_content": self.purpose_0_content,
            "reg_date": self.reg_date,
            "is_success_to_send": self.is_success_to_send,
            "is_complete": self.is_complete,
            "lang": self.lang
        }
        return result