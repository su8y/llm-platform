from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, text
from sqlalchemy.orm import relationship

from . import Base




class DrivePath(Base):
    __tablename__ = "drive_path"
    # Columns
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey("drive_path.id"), nullable=True, default=None) # 상위 디렉토리 id. self foreign key
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    name = Column(String(256), nullable=True) # 디렉토리 명 정도로 생각하자.
    depth = Column(Integer, nullable=True) # 디렉토리 깊이. root 기점으로 몇 뎁스인지 파악. 그래야 디렉토리들을 위치에 맞게 잘 관리할 수 있다.
    reg_date = Column(DateTime)
    update_date = Column(DateTime)

    company_info = relationship("CompanyInfo", backref="drive_path")



    @property
    def serialize(self):
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "company_key": self.company_key,
            "name": self.name,
            "depth": self.depth,
            "reg_date": self.reg_date,
            "update_date": self.update_date,
        }