from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

from . import Base



class CreditHistory(Base):
    __tablename__ = "credit_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    credit_type = Column(Boolean) #1: fulfill, 0: use
    credit = Column(Integer)
    reg_date = Column(DateTime)
    after_credit_available = Column(Integer)
    payment_id = Column(Integer, ForeignKey("payment.id"))

    company = relationship("CompanyInfo", backref="credit_history")
    payment = relationship("Payment", backref="credit_history")

    @property
    def serialize(self):
        return {
            "company_key": self.company_key,
            "credit_type": self.credit_type,
            "credit": self.credit,
            "reg_date": self.reg_date,
            "after_credit_available": self.after_credit_available,
            "payment_id": self.payment_id
        }