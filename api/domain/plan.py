from pydantic import BaseModel
from datetime import datetime



class GetCurrentPlanDomain(BaseModel):
    company_key: str
    params_current_credit: int|None = None

    credit_info: dict | None = None
    file_credit_info: dict | None = None
