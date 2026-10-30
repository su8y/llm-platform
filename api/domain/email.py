from datetime import datetime
from pydantic import ConfigDict, BaseModel
from fastapi import UploadFile

from client.aws import S3Client
from client.pinecone import PineconeClient
from client.groxy import LLMProxyClient
from client.mysql import MySQLClient
from client.milvus import MilvusClient



class InboxListDomain(BaseModel):
    company_key: str
    page: int = 1
    per_page: int = 10
    subject: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    from_: str | None = None
    manager: str | None = None
    status: str | None = None

    rows: list | None = None
    count: int = 0
    reform_rows: list | None = None


class GetInboxDomain(BaseModel):
    id: int
    company_key: str

    row: dict | None = None
    reform_row: dict | None = None


class UpdateCompanyDomain(BaseModel):
    id: int
    company_key: str
    company: str


class GetInboxHistoryDomain(BaseModel):
    id: int
    company_key: str

    response: list | None = None


class GetManagerListDomain(BaseModel):
    company_key: str

    response: list | None = None


class SetManagerDomain(BaseModel):
    id: int
    company_key: str
    user_id: str
    manager_id: str
    action_code: int
    current_time: datetime


class ChangeStatusDomain(BaseModel):
    id: int
    user_id: str
    company_key: str
    status: str
    current_time: datetime
    action_code: int | None = None
    manager_id: str | None = None


class UpdateReceiveCommentDomain(BaseModel):
    id: int
    user_id: str
    company_key: str
    comment: str
    current_time: datetime
    action_code: int


class InitAnswerDomain(BaseModel):
    id: int
    user_id: str
    company_key: str
    current_time: datetime

    has_row: bool | None = None
    company_email_address: str | None = None
    company_email_name:str | None = None
    cx_email_row: dict | None = None


class CreateEmailContentDomain(BaseModel):
    id: int
    service: str
    vendor: str
    model: str
    action_code: int
    current_time: datetime
    user_id: str

    question: str | None = None
    session_key: str | None = None
    company_key: str | None = None
    credit_available: int = 0
    start_time: float | None = None
    status: str | None = None

    vector_db_index: str | None = None
    vector_db_namespace: str | None = None
    vector_db_embedding_model: str | None = None
    llm_proxy_client: LLMProxyClient | None = None
    main_db_client: MySQLClient | None = None
    vector_db_client: PineconeClient | MilvusClient | None = None
    s3_client: S3Client | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class GetSendInfoDomain(BaseModel):
    cx_email_id: int
    company_key: str

    response: dict | None = None


class SaveSendInfoDomain(BaseModel):
    id: int # for save history
    cx_email_id: int
    user_id: str
    company_key: str
    current_time: datetime
    action_code: int | None = None

    company_email_address: str | None = None
    company_email_name: str | None = None
    to_mail: list[str] | None = None
    to_name: list[str] | None = None
    cc_mail: list[str] | None = None
    cc_name: list[str] | None = None
    bcc_mail: list[str] | None = None
    bcc_name: list[str] | None = None
    subject: str | None = None
    answering_content: str | None = None
    comment: str | None = None
    attachments: list[dict] | None = None

    ex_row: dict | None = None


class SaveAttachDomain(BaseModel):
    attachments: list[UploadFile] | UploadFile
    company_key: str

    response: list = []


class CheckHasThreadDomain(BaseModel):
    id: int

    received_references_rows: dict | None = None
    sent_rows: dict | None = None


class SendEmailDomain(BaseModel):
    id: int
    company_key: str
    server_stage: str
    reply_to: list | str | None = None
    reply_to_name: list | str | None = None
    reply_cc: list | str | None = None
    reply_cc_name: list | str | None = None
    reply_bcc: list | str | None = None
    reply_bcc_name: list | str | None = None
    reply_from: list | str | None = None
    reply_from_name: list | str | None = None
    keyword: str | None = None
    reply_subject: str | None = None
    received_subject: str | None = None
    email_html: str | None = None
    from_message_id: str | None = None
    references: list | None = None
    manager_id: str | None = None
    comments: str | None = None
    content: str | None = None
    vector_db_index: str | None = None
    vector_db_namespace: str | None = None
    received_at: datetime | None = None
    current_time: datetime | None = None
    company: str | None = None
    image_info: list | None = None
    user_id: str | None = None
    action_code: int | None = None
    attachments: str | None = None
    attachments_info_for_ses: list = []
    smtp_config: dict | None = None            # 회사 SMTP 발신 설정(있으면 SES 대신 SMTP 로 발송)

    first_message_id: str | None = None

    cid_and_image: list | None = []
    cid_images: str | None = None
    s3_bucket: str | None = None
    s3_key: str | None = None
    row_id: int | None = None
    to_message_id: str | None = None

    is_over_token: bool | None = None
    vector_table_datas: list | None = []
    vector_ids: list | str = []
    vector_content: str | None = None
    vector_values: list | str = []
    vector_metadatas: list | dict = []
    llm_content: str | None = None
    response: dict | None = None


class DeleteSentEmailDomain(BaseModel):
    email_send_history_id: int | list[int]
    company_key: str
    vector_db_index: str
    vector_db_namespace: str
    server_stage: str

    is_soft_deletion: bool = True
    vector_id: list[int] | None = None
    target_delete_ids: list[str] | None = None
    vector_metadata: list[dict] | None = None
    target_update_metadata: list[dict] | None = None


class GetSESBounceDomain(BaseModel):
    message_id: str | None = None
    is_bounce: bool = False
    bounce_type: str | None = None
    bounce_sub_type: str | None = None
    bounced_recipients: str | dict | None = None


class UploadBase64Domain(BaseModel):
    company_key: str
    image: list
    current_date: datetime

    insert_rows: list = []
    response: list = []

class GetDashboardChartDomain(BaseModel):
    company_key: str
    start_date: datetime
    end_date: datetime
    current_date: datetime
    diff_date: int
    client_timezone: str

    row: dict = {}
    response: dict = {}

class GetDashboardLineDomain(BaseModel):
    company_key: str
    start_date: datetime
    start_date_local: datetime
    end_date: datetime
    end_date_local: datetime
    client_timezone: str

    cx_email_row: dict = {}
    email_send_history_row: dict = {}
    response: dict = {}

class GetDashboardManagerCntDomain(BaseModel):
    company_key: str
    start_date: datetime
    end_date: datetime

    row: dict = {}
    response: dict = {}
