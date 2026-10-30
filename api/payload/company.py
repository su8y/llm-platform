from pydantic import BaseModel, Field
from typing import Optional



class chargeCreditPayload(BaseModel):
    charge_credit: int = Field(..., alias="chargeCredit")


class updatePlanPayload(BaseModel):
    plan_name: str = Field(..., alias="planName")