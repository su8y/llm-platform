from pydantic import BaseModel, Field
from typing import Optional



class EmailRAGListPayload(BaseModel):
    manager: Optional[str] = Field(None, alias="manager", description="manager")
    subject: Optional[str] = Field(None, alias="subject", description="subject")
    to: Optional[str] = Field(None, alias="to", description="receiver")
    start_date: Optional[str] = Field(None, alias="startDate", description="startDateForSentTime")
    end_date: Optional[str] = Field(None, alias="endDate", description="endDateForSentTime")
    page: Optional[int] = Field(1, alias="page", description="page number")
    per_page: Optional[int] = Field(20, alias="perPage", description="page size")


class EmailRAGDetailPayload(BaseModel):
    id: int = Field(..., alias="id", description="id which user click")
