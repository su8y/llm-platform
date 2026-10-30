from pydantic import BaseModel, Field
from typing import Optional



class getMembersPayload(BaseModel):
	page: Optional[int] = Field(1, alias="page")
	per_page: Optional[int] = Field(20, alias="perPage")
	local_timezone: Optional[str] = Field("Asia/Seoul", alias="localTimeZone")
	status: Optional[str] = Field(None, alias="status")
	user_id: Optional[str] = Field(None, alias="userId")
	department: Optional[str] = Field(None, alias="department")
	email_address: Optional[str] = Field(None, alias="emailAddress")
	auth_name: Optional[str] = Field(None, alias="authName")
	start_date: Optional[str] = Field(None, alias="startDate")
	end_date: Optional[str] = Field(None, alias="endDate")
	
	
class changeAuthPayload(BaseModel):
	user_id: str = Field(..., alias="userId")
	auth_name: str = Field(..., alias="authName")


class changeLangPayload(BaseModel):
	user_id: str = Field(..., alias="userId")
	lang: str = Field(..., alias="lang")


class inviteMemberPayload(BaseModel):
	email_address: str = Field(..., alias="emailAddress")
	local_timezone: str = Field("Asia/Seoul", alias="localTimeZone")
	lang: str = Field(..., alias="lang")


class reInviteMemberPayload(BaseModel):
	email_address: str = Field(..., alias="emailAddress")
	local_timezone: str = Field("Asia/Seoul", alias="localTimeZone")
	lang: str = Field(..., alias="lang")


class acceptQueryParams(BaseModel):
	acceptance: str


class deleteUserPayload(BaseModel):
	user_id: str = Field(..., alias="userId")
	invite_history_id: str = Field(..., alias="inviteHistoryId")
