from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from . import Base



class PlanChangeHistory(Base):
    """metadata table for plan change history"""
    __tablename__ = "plan_change_history"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    plan_info_id = Column(Integer, ForeignKey("plan_info.id"))
    payment_id = Column(Integer)
    upgrade = Column(Boolean, default=False)
    reg_date = Column(DateTime)

    company = relationship("CompanyInfo", backref="plan_change_history")
    plan = relationship("PlanInfo", backref="plan_change_history")


    @property
    def serialize(self):
        return {
            "id": self.id,
            "company_key": self.company_key,
            "plan_info_id": self.plan_info_id,
            "payment_id": self.payment_id,
            "upgrade": self.upgrade,
            "reg_date": self.reg_date,
        }