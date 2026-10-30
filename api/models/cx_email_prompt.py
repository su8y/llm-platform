from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, func, Boolean
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship

from . import Base



class CxEmailPrompt(Base):
    __tablename__ = "cx_email_prompt"
    # Columns
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_key = Column(String(40), index=True, nullable=False)
    prompt_name = Column(String(100), nullable=True)
    prompt = Column(LONGTEXT, nullable=False)
    reg_date = Column(DateTime, nullable=False)
    comment = Column(LONGTEXT, nullable=True)
    writer = Column(String(30), nullable=True)


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