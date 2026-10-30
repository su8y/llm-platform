from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text, text, and_, func
from sqlalchemy.orm import relationship

from . import Base



class PostCategory(Base):
    __tablename__ = "post_category"
    # Columns
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    name = Column(String(128))
    parent_id = Column(Integer, ForeignKey("post_category.id"))
    depth = Column(Integer)
    order = Column(Integer)
    reg_date = Column(DateTime)
    update_date = Column(DateTime)
    is_show = Column(Boolean, default=True)
    is_on = Column(Boolean, default=True)
    lang = Column(String(5), default="ko")

    company = relationship("CompanyInfo", backref="post_category")

    @property
    def serialize(self):
        return {
            "id": self.id,
            # "company_key": self.company_key,
            "name": self.name,
            "parent_id": self.parent_id,
            "depth": self.depth,
            "order": self.order,
            "reg_date": self.reg_date,
            "update_date": self.update_date,
            "is_show": self.is_show,
            "is_on": self.is_on,
            "lang": self.lang
        }