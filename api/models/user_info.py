from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, text
from sqlalchemy.orm import relationship

from . import Base


class UserInfo(Base):
    __tablename__ = "user_info"
    user_id = Column(String(20), primary_key=True, nullable=False)
    user_password = Column(String(256), nullable=False)
    user_auth = Column(Integer, ForeignKey("user_auth.id"), default=3) #1이면 master, 2이면 관리자(CRUD), 3이면 단순 조회(READ)만 가능  
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    email_address = Column(String(100), nullable=False)
    invite_history_id = Column(Integer, ForeignKey("invite_history.id"), nullable=True)
    reg_date = Column(DateTime)
    last_login_date = Column(DateTime)
    find_key = Column(String(40), nullable=True)
    find_key_exp_date = Column(DateTime, nullable=True)
    department = Column(String(40), nullable=True)
    certifi = Column(Boolean, default=False)
    lang = Column(String(5))
    phone = Column(String(16))
    is_admin = Column(Boolean, default=False)
    newest_session_key = Column(String(40), nullable=True)

    company = relationship("CompanyInfo", backref="user")
    auth = relationship("UserAuth", backref="user")
    invite_history = relationship("InviteHistory", backref="user")
    
    @property
    def serialize(self):
        return {
            "user_id": self.user_id, #
            "user_password": self.user_password,
            "user_auth": self.user_auth,
            "email_address": self.email_address, #
            "reg_date": self.reg_date,
            "last_login_date": self.last_login_date,
            "find_key": self.find_key,
            "find_key_exp_date": self.find_key_exp_date,
            "department": self.department, #
            "invite_history_id": self.invite_history_id,
            "certifi": self.certifi,
            "phone": self.phone,
            "lang": self.lang,
            "company_key": self.company_key,
            "company_name": self.company.company_name, #
            "plan_info_id": self.company.plan_info_id,
            "credit_available": self.company.credit_available, #
            "vector_db_index": self.company.vector_db_index,
            "vector_db_namespace": self.company.vector_db_namespace,
            "master_id": self.company.master_id
        }