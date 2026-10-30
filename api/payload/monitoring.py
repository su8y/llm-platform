from fastapi import Form
from pydantic import BaseModel, Field
from typing import Optional



class getChatHistoryPayload(BaseModel):
    page: Optional[int] = Field(1, alias="page")
    per_page: Optional[int] = Field(10, alias="per_page")
    start_date: Optional[str] = Field(None, alias="start_date")
    end_date: Optional[str] = Field(None, alias="end_date")
    asker_id: Optional[str] = Field(None, alias="asker_id")
    manager_id: Optional[str] = Field(None, alias="manager_id")
    issue_status: Optional[str] = Field(None, alias="issue_status")
    timezone: Optional[str] = Field("Asia/Seoul", alias="timezone")
    is_mcp: Optional[bool] = Field(None, alias="isMCP")
    

class getChatHistoryDetailHeadPayload(BaseModel):
    session_key: str = Field(..., alias="sessionKey")


class getChatHistoryDetailTailPayload(BaseModel):
    session_key: str = Field(..., alias="sessionKey")
    page: Optional[int] = Field(1, alias="page")
    per_page: Optional[int] = Field(1, alias="per_page")
    page_mode: Optional[bool] = Field(False, alias="pageMode")
    

class getChatRatingPayload(BaseModel):
    start_date: str = Field(..., alias="start_date")
    end_date: str = Field(..., alias="end_date")
    period: Optional[str] = Field("day", alias="period")
    timezone: Optional[str] = Field("Asia/Seoul", alias="timezone")
    

class getChatCountPayload(BaseModel):
    start_date: str = Field(..., alias="start_date")
    end_date: str = Field(..., alias="end_date")
    period: Optional[str] = Field("day", alias="period")
    timezone: Optional[str] = Field("Asia/Seoul", alias="timezone")
        

class updateChatHistoryPayload(BaseModel):
    session_key: str = Field(..., alias="sessionKey")
    manager_id: Optional[str] = Field(None, alias="manager_id")
    issue_status: Optional[str] = Field(None, alias="issue_status")
    rating: Optional[int] = Field(None, alias="rating")
    assessor_id: Optional[str] = Field(None, alias="assessor_id")


class getTopPayload(BaseModel):
    start_date: Optional[str] = Field(None, alias="start_date")
    end_date: Optional[str] = Field(None, alias="end_date")
    timezone: Optional[str] = Field("Asia/Seoul", alias="timezone")
