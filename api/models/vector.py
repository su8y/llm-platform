from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, text, Boolean
from sqlalchemy.orm import relationship

from . import Base



class Vector(Base):
    __tablename__ = "vector"
    # Columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    upload_file_id = Column(Integer, ForeignKey("upload_file.id"))
    post_id = Column(Integer, ForeignKey("post.id"))
    page = Column(Integer, nullable=True)
    chunk = Column(Integer, nullable=True)
    data_type = Column(String(256), nullable=True)
    is_on = Column(Boolean, nullable=True)
    is_show = Column(Boolean, nullable=True)
    
    company_info = relationship("CompanyInfo", backref="vector")
    upload_file = relationship("UploadFile", backref="vector")

    @property
    def serialize(self):
        return {
            "id": self.id,
            "company_key": self.company_key,
            "upload_file_id": self.upload_file_id,
            "post_id": self.post_id,
            "page": self.page,
            "chunk": self.chunk,
            "data_type": self.data_type,
            "is_on": self.is_on,
            "is_show": self.is_show,
        }