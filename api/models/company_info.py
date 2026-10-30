from uuid import uuid4

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship

from . import Base



class CompanyInfo(Base):
    __tablename__ = "company_info"
    # columns
    company_key = Column(String(40), primary_key=True, default=lambda: str(uuid4()).replace("-", ""))
    company_name = Column(String(20), unique=True, nullable=False)
    company_url = Column(String(50), unique=True)
    master_id = Column(String(20), nullable=False)
    reg_date = Column(DateTime)
    status = Column(Integer, default=0)
    plan_info_id = Column(Integer, ForeignKey("plan_info.id"), nullable=True)
    credit_available = Column(Integer, default=0, server_default="0")
    vector_db_index = Column(String(40), nullable=False, default="llm-platform", server_default="llm-platform")
    vector_db_namespace = Column(String(40), nullable=False, default=lambda: str(uuid4()).replace("-", ""))
    greetings = Column(Text, nullable=True, default=None)
    lang = Column(String(5))
    trial_expired_day_cnt = Column(Integer, nullable=True)
    expired_date = Column(DateTime, nullable=True)
    parser_credit_available = Column(Integer, default=0, server_default="0")
    email_available = Column(Boolean, default=False, server_default="0")
    mcp_token = Column(String(64), nullable=True)
    mcp_server = Column(String(3000), nullable=True)
    mcp_allowed_tools = Column(LONGTEXT, nullable=True)
    email_from_address = Column(String(100), nullable=True)
    email_from_name = Column(String(100), nullable=True)
    store_name = Column(String(300), nullable=True)
    on_llm_platform_system = Column(Boolean, default=True, server_default="1")

    plan = relationship("PlanInfo", backref="company_info")

    @property
    def serialize(self):
        return {
            "company_key": self.company_key,
            "company_name": self.company_name,
            "master_id": self.master_id,
            "reg_date": self.reg_date,
            "status": self.status,
            "credit_available": self.credit_available,
            "parser_credit_available": self.parser_credit_available,
            "plan_info_id": self.plan_info_id,
            "model": self.plan.model if self.plan_info_id else None,
            "vector_db_index": self.vector_db_index,
            "vector_db_namespace": self.vector_db_namespace,
            "greetings": self.greetings,
            "lang": self.lang,
            "trial_expired_day_cnt": self.trial_expired_day_cnt,
            "expired_date": self.expired_date,
            "mcp_token": self.mcp_token,
            "email_available": self.email_available,
            "email_from_address": self.email_from_address,
            "email_from_name": self.email_from_name,
            "store_name": self.store_name,
            "on_llm_platform_system": self.on_llm_platform_system
        }
