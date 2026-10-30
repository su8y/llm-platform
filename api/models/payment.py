from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, text
from sqlalchemy.orm import relationship

from . import Base



class Payment(Base):
    """payment table"""
    __tablename__ = "payment"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    plan_info_id = Column(Integer, ForeignKey("plan_info.id"))
    payment_history_id = Column(Integer, ForeignKey("payment_history.id"))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    payment_date = Column(String(10))
    payment_period = Column(Integer)
    payment_status = Column(String(32), default="complete")
    change_type = Column(String(16), default="system") #system, user
    use_credit = Column(Integer)
    reg_date = Column(DateTime)
    apply_type = Column(String(10), default=None, nullable=True)
    is_target_renewal = Column(Boolean, default=False) # true: pay per month, false: pay per year
    attempt_count = Column(Integer, default=0) # if 5 times, judge will not pay. change plan_info_id -> 8

    company = relationship("CompanyInfo", backref="payment")
    plan = relationship("PlanInfo", backref="payment")
    payment_history = relationship("PaymentHistory", backref="payment")

    @property
    def serialize(self):
        return {
            "id": self.id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "payment_date": self.payment_date,
            "payment_period": self.payment_period,
            "payment_status": self.payment_status,
            "change_type": self.change_type,
            "use_credit": self.use_credit,
            "is_target_renewal": self.is_target_renewal,
            "company_key": self.company_key,
            "credit_available": self.company.credit_available,
            "plan_info_id": self.plan_info_id,
            "init_credit": self.plan.init_credit,
            "plan_name": self.plan.plan_name,
        }