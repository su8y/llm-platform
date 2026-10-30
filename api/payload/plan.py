from pydantic import BaseModel, Field
from typing import Optional



class insertPaymentPayload(BaseModel):
	company_key: str = Field(..., alias="companyKey")
	plan_id: str = Field(..., alias="planId")
	plan_period: str = Field(..., alias="planPeriod")
	type: str = Field(..., alias="type")
	card_number: str = Field(..., alias="cardNumber")
	actual_payment_amount: str = Field(..., alias="actualPaymentAmount")


class insertPlanPayload(BaseModel):
	company_key: str = Field(..., alias="companyKey")
	plan_id: str = Field(..., alias="planId")
	plan_period: str = Field(..., alias="planPeriod")
	payment_history_id: str = Field(..., alias="paymentHistoryId")
	payment_date: str = Field(..., alias="paymentDate")
	is_target_renewal: Optional[bool] = Field(False, alias="isTargetRenewal")
	local_timezone: str = Field(..., alias="localTimezone")
	start_date: str = Field(..., alias="startDate")
	

class getPlanHistoryPayload(BaseModel):
	page: Optional[int] = Field(1, alias="page")
	per_page: Optional[int] = Field(10, alias="perPage")
	plan_name: Optional[str] = Field(None, alias="planName")
	type: Optional[str] = Field(None, alias="type")


class getCurrentCreditParams(BaseModel):
	current_credit: Optional[str|int] = Field(None, alias="currentCredit")
	
	
class changePlanPayload(BaseModel):
	plan_id: str = Field(..., alias="planId")