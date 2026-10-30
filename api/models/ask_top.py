from sqlalchemy import Column,Integer, String, ForeignKey, DateTime
from . import Base



class AskTop(Base):
    __tablename__ = "ask_top"
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_key = Column(String(100), ForeignKey("company_info.company_key"))
    rank1 = Column(String(100))
    rank1_count = Column(Integer)
    rank2 = Column(String(100))
    rank2_count = Column(Integer)
    rank3 = Column(String(100))
    rank3_count = Column(Integer)
    created_at = Column(DateTime)
    date_type = Column(String(20))
    question_count = Column(Integer)
    

    @property
    def serialize(self):
        return {
            "company_key": self.company_key,
            "rank1": self.rank1,
            "rank1_count": self.rank1_count,
            "rank2": self.rank2,
            "rank2_count": self.rank2_count,
            "rank3": self.rank3,
            "rank3_count": self.rank3_count,
            "created_at": self.created_at,
            "date_type": self.date_type,
            "question_count": self.question_count
        }