from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

from . import Base



class DomainInfo(Base):
    __tablename__ = "domain_info"
    # columns
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    domain = Column(String(100), unique=True)
    reg_date = Column(DateTime)
    update_date = Column(DateTime)
    is_show = Column(Boolean)
    is_deleted = Column(Boolean, nullable=False, server_default="0")

    company_info = relationship("CompanyInfo", backref="domain_info")