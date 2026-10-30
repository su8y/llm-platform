from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship

from . import Base



class CxEmailReferences(Base):
    __tablename__ = "cx_email_references"
    # Columns
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_message_id = Column(String(255), index=True, nullable=True)
    message_id = Column(String(255), index=True, nullable=True)
    created_at = Column(DateTime, nullable=False)


    @property
    def serialize(self):
        return {
            "id": self.id,
            "firstMessageId": self.first_message_id,
            "messageId": self.message_id,
            "createdAt": self.created_at
        }