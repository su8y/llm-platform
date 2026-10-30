from datetime import datetime
from pydantic import BaseModel

from utils.date import get_utc_now



class registerDomain(BaseModel):
    user_id: str
    company_name: str
    hashed_password: str
    email_address: str
    reg_date: datetime
    expired_date: datetime
    department: str | None = None
    lang: str | None = None
    phone: str | None = None
    invitation_key: str | None = None
    is_slave: bool | None = None
    user_auth: int | None = None
    server_stage: str | None = None
    company_key: str | None = None

    plan_info_id: int | None = None
    credit_available: int | None = None
    parser_credit_available: int | None = None
    vector_db_index: str | None = None
    vector_db_namespace: str | None = None
    store_name: str | None = None
    invite_history_id: int | None = 1
    certifi: bool | None = None
    is_admin: bool | None = None


class getRegisterInfoDomain(BaseModel):
    invitation_key: str


class certificateDomain(BaseModel):
    user_id: str
    company_key: str
    lang: str

    user_info_row:dict | None = None
    invite_history_id: int | None = None
    invite_date: datetime | None = get_utc_now()
    accept: bool | None = True
    success: bool | None = None

    redirect_url: str | None = None


class loginDomain(BaseModel):
    user_id: str
    user_password: str
    server_stage: str
    reg_date: datetime

    init_plan: dict | None = None
    company_key: str | None = None
    plan_info_id: int | None = None
    expired_date: datetime | None = None
    first_payment_id: int | None = None
    reg_date: datetime | None = None
    credit_type: bool | None = None
    credit: int | None = None

    access_token: str | None = None
    refresh_token: str | None = None


class getInfoDomain(BaseModel):
    user_id: str

    row: dict | None = None
    reform_row: dict | None = None


class findPasswordDomain(BaseModel):
    user_id: str
    server_stage: str
    lang: str
    current_date: datetime = get_utc_now()

    email_address: str | None = None
    company_name: str | None = None
    find_key: str | None = None
    redirect_url: str | None = None


class checkValidationFindPasswordDomain(BaseModel):
    query_base64: str
    find_key: str
    user_id: str
    server_stage: str
    current_date: datetime = get_utc_now()

    newest_row_id: int | None = None
    redirect_url: str | None = None


class changePasswordDomain(BaseModel):
    user_id: str
    user_password: str
    find_key: str
    current_date: datetime = get_utc_now()

    hashed_password: str | None = None
