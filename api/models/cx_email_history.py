from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship

from . import Base



class CxEmailHistory(Base):
    __tablename__ = "cx_email_history"
    # Columns
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    cx_email_id = Column(Integer, ForeignKey("cx_email.id"), index=True)
    user_id = Column(String(20))
    action_code = Column(Integer)
    reg_date = Column(DateTime)

    company_info = relationship("CompanyInfo", backref="cx_email_history")
    cx_email = relationship("CxEmail", backref="cx_email_history")


    @property
    def serialize(self):
        return {
            "id": self.id,
            "companyKey": self.company_key,
            "cxEmailId": self.cx_email_id,
            "userId": self.user_id,
            "status": self.action_code,
            "reg_date": self.reg_date
        }