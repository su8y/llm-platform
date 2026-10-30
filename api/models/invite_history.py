from sqlalchemy import Column, Integer, String, DateTime, and_, Text, Boolean, ForeignKey, or_, text
from sqlalchemy.orm import relationship

from . import Base



class InviteHistory(Base):
    """history table for invite"""
    __tablename__ = "invite_history"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email_address_invite = Column(String(100))
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    auth_key = Column(String(40))
    auth_key_exp_date = Column(DateTime)
    invite_date = Column(DateTime)
    invite_url = Column(Text)
    success = Column(Boolean, default=None)
    accept = Column(Boolean, default=False)
    error_message = Column(Text, default=None)

    company = relationship("CompanyInfo", backref="inviteHistory")

    @property
    def serialize(self):
        result = {
            "id": self.id,
            "email_address_invite": self.email_address_invite,
            "company_key": self.company_key,
            "company_name": self.company.company_name,
            "auth_key": self.auth_key,
            "auth_key_exp_date": self.auth_key_exp_date,
            "invite_date": self.invite_date,
            "invite_url": self.invite_url,
            "success": self.success,
            "accept": self.accept
        }

        return result