from sqlalchemy import Column, Boolean, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from . import Base



class UserAuth(Base):
    __tablename__ = "user_auth"
    id = Column(Integer, primary_key=True, nullable=False)
    common = Column(Boolean, default=False, server_default="0")
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    auth_name = Column(String(20), nullable=False)
    auth_account_manage = Column(Boolean, default=False, server_default="0")
    auth_plan_manage = Column(Boolean, default=False, server_default="0")
    auth_reference_view = Column(Boolean, default=False, server_default="0")
    auth_reference_write = Column(Boolean, default=False, server_default="0")
    auth_reference_category_manage = Column(Boolean, default=False, server_default="0")
    auth_reference_language_all = Column(Boolean, default=False, server_default="0")
    auth_prompt_manage = Column(Boolean, default=False, server_default="0")
    auth_playground_use = Column(Boolean, default=True, server_default="1")
    auth_email_use = Column(Boolean, default=False, server_default="0")
    auth_email_view = Column(Boolean, default=False, server_default="0")

    company = relationship("CompanyInfo", backref="auth")
    
    @property
    def serialize(self):
        return {
            "id": self.id,
			"company_key": self.company_key,
            "company_name": self.company.company_name,
            "auth_name": self.auth_name,
            "auth_account_manage": self.auth_account_manage,
            "auth_plan_manage": self.auth_plan_manage,
            "auth_reference_view": self.auth_reference_view,
            "auth_reference_write": self.auth_reference_write,
            "auth_reference_category_manage": self.auth_reference_category_manage,
            "auth_reference_language_all": self.auth_reference_language_all,
            "auth_prompt_manage": self.auth_prompt_manage,
            "auth_playground_use": self.auth_playground_use,
            "auth_email_use": self.auth_email_use,
            "auth_email_view": self.auth_email_view,
        }