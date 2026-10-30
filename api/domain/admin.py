from pydantic import BaseModel
from datetime import datetime



class getMembersDomain(BaseModel):
    company_key: str
    page: int | None = None
    per_page: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    filters: dict | None = None
    
    row: list[dict] | None = None
    count: int | None = None
    reform_row: list[dict] | None = None
    

class getAuthNameDomain(BaseModel):
    company_key: str
    
    rows: list[dict] | None = None
    

class changeAuthDomain(BaseModel):
    user_id: str
    auth_name: str
    company_key: str
    
    user_auth: int | None = None # auth table id


class changeLangDomain(BaseModel):
    user_id: str
    lang: str
    

class inviteMemberDomain(BaseModel):
    company_key: str
    user_id: str
    lang: str
    local_timezone: str
    email_addresses_list: list[str]
    invite_date: datetime
    
    user_auth: int | None = None # auth table id
    insert_data: list[dict] | tuple[dict] | None = None
    mail_data: list[dict] | tuple[dict] | None = None
    
    mail_response: list[dict] | dict | None = None


class reInviteMemberDomain(BaseModel):
    company_key: str
    user_id: str
    lang: str
    email_address: str
    local_timezone: str
    invite_date: datetime
    
    user_auth: int | None = None # auth table id
    insert_data: dict | None = None
    mail_data: dict | None = None
    
    mail_response: dict | None = None
    

class acceptDomain(BaseModel):
    acceptance: str
    
    auth_key: str | None = None
    row: dict | None = None
    
    redirect_url: str | None = None

    
class deleteUserDomain(BaseModel):
    user_id: str
    invite_history_id: str
    company_key: str
    
    
    
    
    