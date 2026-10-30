from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, text
from sqlalchemy.orm import relationship

from . import Base



class PasswordResetHistory(Base):
    """history table for invite"""
    __tablename__ = "password_reset_history"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100))
    find_key = Column(String(40))
    find_key_exp_date = Column(DateTime)
    reg_date = Column(DateTime)
    is_newest = Column(Boolean, default=True, server_default=text("1"))
    is_success = Column(Boolean, default=True, server_default=text("1"))

    user_info = relationship("UserInfo", backref="passwordResetHistory")


    @property
    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "find_key": self.find_key,
            "find_key_exp_date": self.find_key_exp_date,
            "reg_date": self.reg_date,
            "is_newest": self.is_newest
        }