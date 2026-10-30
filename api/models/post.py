
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text, and_, or_, func
from sqlalchemy.orm import relationship

from . import Base



class Post(Base):
    __tablename__ = "post"
    # Columns
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    post_category_id = Column(Integer, ForeignKey("post_category.id"), nullable=True)
    title = Column(String(256), nullable=True)
    content = Column(Text, nullable=True) #토큰 제한에 맞춰 string 길이 제한해줄 것
    image_url = Column(Text, nullable=True, default=False)
    reg_date = Column(DateTime)
    update_date = Column(DateTime)
    content_admin = Column(Text, nullable=True)
    is_show = Column(Boolean, default=True)
    is_on = Column(Boolean, default=True)
    use_count = Column(Integer, default=0)
    lang = Column(String(5), default="ko")
    source = Column(String(500))
    author = Column(String(30))
    category_depth_1_id = Column(Integer, ForeignKey("post_category.id"), nullable=True)
    category_depth_2_id = Column(Integer, ForeignKey("post_category.id"), nullable=True)
    is_temp = Column(Boolean, nullable=True, default=None)
    is_update = Column(Boolean, default=False)
    is_markdown = Column(Boolean, default=False)
    sitemap_id = Column(Integer, default=None, nullable=True)

    company = relationship("CompanyInfo", backref="post")
    post_category = relationship("PostCategory", foreign_keys=[post_category_id])
    category_depth_1 = relationship('PostCategory', foreign_keys=[category_depth_1_id])
    category_depth_2 = relationship('PostCategory', foreign_keys=[category_depth_2_id])

    @property
    def serialize(self):
        return {
            "id": self.id,
            "company_key": self.company_key,
            "company_name": self.company.company_name,
            "vector_db_index": self.company.vector_db_index,
            "vector_db_namespace": self.company.vector_db_namespace,
            "post_category_id": self.post_category_id,
            "post_category_name": self.post_category.name if self.post_category else None,
            "post_category_depth": self.post_category.depth if self.post_category else None,
            "post_category_parent_id": self.post_category.parent_id if self.post_category else None,
            "title": self.title,
            "content": self.content,
            "image_url": self.image_url,
            "reg_date": self.reg_date,
            "update_date": self.update_date,
            "content_admin": self.content_admin,
            "is_show": self.is_show,
            "is_on": self.is_on,
            "lang": self.lang,
            "source": self.source,
            "use_count": self.use_count,
            "author": self.author,
            "is_temp": self.is_temp,
            "is_update": self.is_update,
            "category_depth_1_id": self.category_depth_1_id if self.category_depth_1 else None,
            "category_depth_1_name": self.category_depth_1.name if self.category_depth_1 else None,
            "category_depth_2_id": self.category_depth_2_id if self.category_depth_2 else None,
            "category_depth_2_name": self.category_depth_2.name if self.category_depth_2 else None
        }
