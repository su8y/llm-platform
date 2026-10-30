from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from . import Base



class PaymentHistory(Base):
    """metadata table for plan"""
    __tablename__ = "payment_history"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True) # is Primary key need to?
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    user_id = Column(String(20), ForeignKey("user_info.user_id"))
    plan_info_id = Column(Integer, ForeignKey("plan_info.id"))
    plan_period = Column(Integer)
    reg_date = Column(DateTime)
    type = Column(String(20))
    success = Column(Boolean)
    card_number = Column(Integer)
    approval = Column(Boolean)
    actual_payment_amount = Column(Integer)

    company = relationship("CompanyInfo", backref="payment_history")
    plan_info = relationship("PlanInfo", backref="payment_history")
    user = relationship("UserInfo", backref="payment_history")


    @property
    def serialize(self):
        return {
            "id": self.id,
            "company_key": self.company_key,
            "user_id": self.user_id,
            "plan_info_id": self.plan_info_id,
            "plan_period": self.plan_period,
            "reg_date": self.reg_date,
            "card_number": self.card_number,
            "type": self.type,
            "success": self.success,
            "approval": self.approval,
        }