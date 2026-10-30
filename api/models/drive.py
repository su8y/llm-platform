from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship

from . import Base


class Drive(Base):
    __tablename__ = "drive"
    # Columns
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_key = Column(String(40), ForeignKey("company_info.company_key"))
    filename = Column(String(256), nullable=True)
    filetype = Column(String(256), nullable=True)
    filesize = Column(Integer, default=0)
    unit_count = Column(Integer, nullable=True,default=None)
    thumnail_s3_path = Column(String(256), nullable=True, default=None)
    reg_date = Column(DateTime)
    update_date = Column(DateTime)
    upload_user_id = Column(String(20), ForeignKey("user_info.user_id"), nullable=True)
    drive_path_id = Column(Integer, ForeignKey("drive_path.id"), nullable=True)
    upload_file_id = Column(Integer, ForeignKey("upload_file.id"), nullable=True)
    is_on = Column(Boolean, default=False) # RAG 사용여부. vector db에 저장 완료되면 True로 변경
    is_show = Column(Boolean, default=True)
    status = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False, server_default="0")
    will_be_deleted_date = Column(DateTime, nullable=True)
    error_page = Column(Text, nullable=True, default=None)

    company_info = relationship("CompanyInfo", backref="drive")
    user_info = relationship("UserInfo", backref="drive")
    drive_path = relationship("DrivePath", backref="drive")
    upload_file = relationship("UploadFile", backref="drive")


    @property
    def serialize(self):
        return {
            "id": self.id,
            "company_key": self.company_key,
            "filename": self.filename,
            "filetype": self.filetype,
            "reg_date": self.reg_date,
            "update_date": self.update_date,
            "upload_user_id": self.upload_user_id,
            "drive_path_id": self.drive_path_id,
            "upload_file_id": self.upload_file_id,
            "is_on": self.is_on,
            "is_show": self.is_show,
            "status": self.status,
            "thumnail_s3_path": self.thumnail_s3_path,
            "filesize": self.filesize
        }