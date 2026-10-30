from pydantic import BaseModel



class getCreditDomain(BaseModel):
    company_key: str

    credit: int|None = None