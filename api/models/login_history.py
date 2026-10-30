from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from . import Base



class LoginHistory(Base):
    __tablename__ = "login_history"
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(String(20), ForeignKey("user_info.user_id"), nullable=False)
    login_time = Column(DateTime, nullable=False)
    logout_time = Column(DateTime, nullable=True)
    session_key = Column(String(40), nullable=True)
    ip_address = Column(String(20), nullable=True)
    form = Column(String(20), nullable=True)

    user = relationship("UserInfo", backref="login_history")

    @property
    def serialize(self):
        return {
			"id": self.id,
			"user_id": self.user_id,
			"login_time": self.login_time,
			"logout_time": self.logout_time,
			"session_key": self.session_key,
			"ip_address": self.ip_address,
			"form": self.form
		}