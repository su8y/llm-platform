from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship

from . import Base



class EmailCidImages(Base):
    __tablename__ = "email_cid_images"
    # columns
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content_id = Column(String(255), unique=True, nullable=True)
    s3_key = Column(String(500), nullable=True)
    content_type = Column(String(100), nullable=True)
    size = Column(Integer, nullable=True)
    filename = Column(String(255), nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)