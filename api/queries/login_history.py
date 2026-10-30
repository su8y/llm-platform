import logging

from sqlalchemy import Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from . import db
from utils.error import DBError
from utils.date import *




class LoginHistory(db.Model):
    __tablename__ = "login_history"
    __table_args__ = {'extend_existing': True}
    id = db.Column(Integer, primary_key=True, nullable=False)
    user_id = db.Column(String(20), ForeignKey("user_info.user_id"), nullable=False)
    login_time = db.Column(DateTime, nullable=False)
    logout_time = db.Column(DateTime, nullable=True)
    session_key = db.Column(String(40), nullable=True)
    ip_address = db.Column(String(20), nullable=True)
    form = db.Column(String(20), nullable=True)

    user = relationship("UserInfo", backref="login_history")

    @property
    def serialize(self):
        return {
			"id": self.id,
			"user_id": self.user_id,
			"login_time": adapt_timezone_datetime_to_datetime(self.login_time, "UTC"),
			"logout_time": adapt_timezone_datetime_to_datetime(self.logout_time, "UTC"),
			"session_key": self.session_key,
			"ip_address": self.ip_address,
			"form": self.form
		}