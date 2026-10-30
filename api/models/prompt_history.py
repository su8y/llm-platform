from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from . import Base



class PromptHistory(Base):
    __tablename__ = "prompt_history"
    
    # Columns
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    prompt_name = Column(String(100), nullable=True)
    prompt = Column(Text, nullable=False)
    reg_date = Column(DateTime)
    comment = Column(Text, nullable=True)
    writer = Column(String(30), nullable=True)

    company = relationship("CompanyInfo", backref="prompt")
    
    @property
    def serialize(self):
        return {
            "id": self.id,
            "company_key": self.company_key,
            "prompt_name": self.prompt_name,
            "reg_date": self.reg_date,
            "prompt": self.prompt,
            "comment": self.comment,
            "writer": self.writer
        }