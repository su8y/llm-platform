from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

from . import Base



class DomainSitemapLinkInfo(Base):
    __tablename__ = "domain_sitemap_link_info"
    # columns
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    depth = Column(Integer, nullable=True)
    parent_sitemap_id = Column(Integer, nullable=True)
    sitemap_id = Column(Integer, nullable=False)
    reg_date = Column(DateTime)
    update_date = Column(DateTime)

    company_info = relationship("CompanyInfo", backref="domain_sitemap_info")