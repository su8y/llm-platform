from pydantic import BaseModel, Field
from datetime import datetime

from utils.date import get_utc_now



class InsertEmailPromptDomain(BaseModel):
    company_key: str
    prompt: str
    prompt_name: str | None = None
    writer: str | None = None
    comment: str | None = None
    current_time: datetime = get_utc_now()
