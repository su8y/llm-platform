from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from . import Base


class FileCreditHistory(Base):
    __tablename__ = "file_credit_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    type = Column(String(20))
    use_credit = Column(Integer, default=0)
    remain_credit = Column(Integer, default=0)
    charge_credit = Column(Integer, default=0)
    reg_date = Column(DateTime)
    reg_date_str = Column(String(10))
    drive_id = Column(Integer)

    company = relationship("CompanyInfo", backref="file_credit_history")

    @property
    def serialize(self):
        return {
            "id": self.id,
            "company_key": self.company_key,
            "type": self.type,
            "use_credit": self.use_credit,
            "remain_credit": self.remain_credit,
            "charge_credit": self.charge_credit,
            "reg_date": self.reg_date,
            "reg_date_str": self.reg_date_str,
            "drive_id": self.drive_id
        }
