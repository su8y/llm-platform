from pydantic import BaseModel
from datetime import datetime



class getChatHistoryDomain(BaseModel):
    company_key: str
    page: int
    per_page: int  
    timezone: str
    asker_id: str | None = None
    manager_id: str | None = None
    issue_status: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    start_date_local: datetime | None = None
    is_mcp: bool | None = None
    
    session_list: list | None = None
    session_count: int | None = None
    chat_history_rows: list | None = None
    rows: list | None = None
    issue_count: int | None = None
    
    
class getChatHistoryDetailHeadDomain(BaseModel):
    company_key: str
    session_key: str
    timezone: str | None = None
    
    rows: list | None = None
    reformed_rows: list | None =None
    rating: int | None = None
    id_list: list | None = None
    
    
class getChatHistoryDetailTailDomain(BaseModel):
    company_key: str
    session_key: str
    page: int | None = None
    per_page: int | None = None
    
    rows: list | None = None
    reformed_rows: dict | None =None
    count: int | None = None
    
    
class getChatRatingDomain(BaseModel):
    company_key: str
    period: str
    timezone: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    start_date_local: datetime | None = None
    end_date_local: datetime | None = None
    
    rows: list | None = None
    reformed_rows: dict | None = None
    
    
class getChatCountDomain(BaseModel):
    company_key: str
    period: str
    timezone: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    start_date_local: datetime | None = None
    end_date_local: datetime | None = None
    
    rows: list | None = None
    reformed_rows: dict | None = None
    

class updateChatHistoryDomain(BaseModel):
    company_key: str
    session_key: str
    manager_id: str | None = None
    issue_status: str | None = None
    rating: int | None = None
    assessor_id: str | None = None
    
    update_result: list[dict] | None = None
