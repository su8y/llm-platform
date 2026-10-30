from sqlalchemy import Column, Integer, String, ForeignKey, DateTime

from . import Base



class UploadFile(Base):
    __tablename__ = "upload_file"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    s3_path = Column(String(300))
    filename = Column(String(100))
    reg_date = Column(DateTime)
    post_id = Column(Integer, ForeignKey("post.id"), nullable=True)
    drive_id = Column(Integer, ForeignKey("drive.id"), nullable=True)
    filetype = Column(String(10), nullable=True)
    document_name = Column(String(300), nullable=True)

    @property
    def serialize(self):
        return {
            "id": self.id,
            "s3_path": self.s3_path,
            "filename": self.filename,
            "reg_date": self.reg_date,
            "post_id": self.post_id,
            "drive_id": self.drive_id,
            "filetype": self.filetype,
            "document_name": self.document_name
        }
