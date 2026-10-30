from pydantic import BaseModel
from datetime import datetime



class EmailRAGListDomain(BaseModel):
    company_key: str
    page: int
    per_page: int
    manager: str|None = None
    subject: str|None = None
    to: str|None = None
    start_date: datetime|None = None
    end_date: datetime|None = None

    row: list|None = None
    row_count: int|None = None
    response: dict|None = None


class EmailRAGDetailDomain(BaseModel):
    company_key: str
    row_id: int

    row: dict | None = None
    response: dict | None = None
