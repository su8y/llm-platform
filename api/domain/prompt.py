from pydantic import BaseModel
from datetime import datetime

from utils.date import get_utc_now



class insertPromptDomain(BaseModel):
    user_id: str
    company_key: str
    prompt_name: str
    prompt: str
    comment: str
    reg_date: datetime = get_utc_now()
    

class getVersionDomain(BaseModel):
    company_key: str
    

class getPromptDomain(BaseModel):
    company_key: str
    prompt_id: int


class getGreetingsDomain(BaseModel):
    company_key: str

    greetings: str | None = None
    
    
class updateGreetingsDomain(BaseModel):
    company_key: str
    greetings: str
