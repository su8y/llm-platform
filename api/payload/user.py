from pydantic import ConfigDict, BaseModel, Field
from typing import Optional



class UserRegisterPayload(BaseModel):
    user_id: str = Field(..., alias="user_id", description="User ID")
    user_password: str = Field(..., alias="user_password", description="User Password")
    email_address: str = Field(..., alias="email_address", description="Email Address")
    company_name: str = Field(..., alias="company_name", description="Company Name")
    invitation_key: Optional[str] = Field(None, alias="invitationKey", description="Invitation Key")
    phone_number: Optional[str] = Field(None, alias="phone_number", description="Phone Number")
    department: Optional[str] = Field(None, alias="department", description="Department")
    lang: Optional[str] = Field(None, alias="lang", description="Language")

    model_config = ConfigDict(populate_by_name=True)


class getRegisterInfoQueryParams(BaseModel):
    invitation_key: str = Field(..., alias="invitationKey", description="Invitation Key")

    model_config = ConfigDict(populate_by_name=True)


class certificateQueryParams(BaseModel):
    certification: str = Field(..., alias="certification", description="Certification")

    model_config = ConfigDict(populate_by_name=True)


class UserLoginPayload(BaseModel):
    user_id: str = Field(..., alias="user_id", description="User ID")
    user_password: str = Field(..., alias="user_password", description="User Password")
    user_num: Optional[str] = Field(None, alias="user_num", description="User Number")

    model_config = ConfigDict(populate_by_name=True)


class UserFindPasswordPayload(BaseModel):
    user_id: str = Field(..., alias="userId", description="User ID")
    lang: str = Field(..., alias="lang", description="Language")


class checkValidationFindPasswordQueryParams(BaseModel):
    acceptance: str = Field(..., alias="acceptance", description="Acceptance")

    model_config = ConfigDict(populate_by_name=True)


class UserChangePasswordPayload(BaseModel):
    user_password: str = Field(..., alias="userPassword", description="User Password")
    acceptance: str = Field(..., alias="acceptance", description="Acceptance")

    model_config = ConfigDict(populate_by_name=True)


class UserRefreshTokenPayload(BaseModel):
    refresh_token: str = Field(..., alias="refresh_token", description="Refresh Token")

    model_config = ConfigDict(populate_by_name=True)
