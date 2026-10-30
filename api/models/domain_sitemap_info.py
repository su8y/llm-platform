from sqlalchemy import Column, Integer, String, DateTime, Boolean

from . import Base



class DomainSitemapInfo(Base):
    __tablename__ = "domain_sitemap_info"
    # columns
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    domain_id = Column(Integer, nullable=False)
    protocol = Column(String(10), nullable=True)
    domain = Column(String(100), nullable=True)
    path = Column(String(256), nullable=True)
    query = Column(String(1500), nullable=True)
    fragment = Column(String(256), nullable=True)
    input_url = Column(String(2100), nullable=True)
    url = Column(String(2100), nullable=True)
    title = Column(String(256), nullable=True)
    depth = Column(Integer, nullable=True)
    parent_id = Column(Integer, nullable=True)
    s3_path = Column(String(2100), nullable=True)
    reg_date = Column(DateTime)
    update_date = Column(DateTime)
    is_show = Column(Boolean, nullable=True, server_default="1")
    is_deleted = Column(Boolean, nullable=True, server_default="0")
    params = Column(String(256), nullable=True)