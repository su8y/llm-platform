from sqlalchemy import Column, Integer, String, Boolean

from . import Base



class PlanInfo(Base):
    """metadata table for plan"""
    __tablename__ = "plan_info"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plan_name = Column(String(40))
    plan_price = Column(Integer)
    init_credit = Column(Integer)
    max_token = Column(Integer, default=None, nullable=True)
    model = Column(String(100))
    is_show = Column(Boolean)

    @property
    def serialize(self):
        return {
            "id": self.id,
            "plan_name": self.plan_name,
            "plan_price": self.plan_price,
            "init_credit": self.init_credit,
            "max_token": self.max_token,
            "model": self.model,
            "is_show": self.is_show,
        }