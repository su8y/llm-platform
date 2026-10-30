from typing import Optional

from pydantic import ConfigDict, BaseModel, Field
from datetime import datetime

from client.groxy import LLMProxyClient
from client.mysql import MySQLClient
from client.pinecone import PineconeClient
from client.milvus import MilvusClient
from client.redis import RedisClient
from client.aws import S3Client

from utils.date import get_utc_now



class chatDomain(BaseModel):
    service: str
    vendor: str
    model: str | None = None
    question: str
    answer_id: str
    session_key: str
    company_key: str
    plan_info_id: int
    credit_available: int
    info: dict
    start_time: float
    lang: str | None = None
    vector_db_index: str | None = None
    vector_db_namespace: str | None = None
    vector_db_embedding_model: str | None = None
    llm_proxy_client: LLMProxyClient | None = None
    main_db_client: MySQLClient | None = None
    vector_db_client: PineconeClient | MilvusClient | None = None
    memory_db_client: RedisClient | None = None
    s3_client: S3Client | None = None
    is_mcp: bool | None = None
    mcp_token: str | None = None
    store_name: str | None = None
    file_id: int | None = None
    on_llm_platform_system: bool | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class getChatTitleDomain(BaseModel):
    service: str
    vendor: str | None = None
    model: str | None = None
    session_key: str
    user_id: str
    company_key: str
    question: str|None = None
    title: str = ""
    current_date:datetime = get_utc_now()

    row: list|None = None


class GetMcpToolsDomain(BaseModel):
    session_key: str
    answer_id: str

    history_data: list | None = None
    response: dict | None = None


class retrievalDomain(BaseModel):
    # temp ==========
    user_id: str
    server_stage: str
    # ===============
    refer_ids: list[str] | None = None
    parser_ids: list[str] | None = None
    email_ids: list[str] | None = None
    sitemap_ids: list[str] | None = None
    question_id_str: str | None = None

    mcp_tools: list[str | dict] | None = None
    question: str | None = None
    retrieval_data: list | None = None


class getConversationHistoryDomain(BaseModel):
    session_key: str
    is_mcp: bool | None = None
    conversation_history: list|None = None


class getConversationHistoryTitleDomain(BaseModel):
    company_key: str
    asker_id: str
    manager_id: str | None = None
    issue_status: str | None = None
    page: int = 1
    per_page: int = 15
    start_date: datetime | None = None
    end_date: datetime | None = None
    timezone: str | None = None
    start_date_local: datetime | None = None

    session_list: list | None = None
    session_count: int | None = None
    chat_history_rows: list | None = None
    rows: list|None = None
    is_mcp: Optional[bool] = Field(False, alias="is_mcp")


class getGreetingsDomain(BaseModel):
    company_key: str

    greetings: str|None = None


class getCreditDomain(BaseModel):
    company_key: str

    credit: int|None = None


class newChatDomain(BaseModel):
    user_id: str
    session_key: str

    identity: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None


class updateConversationHistoryDomain(BaseModel):
    id: str
    session_key: str
    rating: int | None = None
    memo: str | None = None

    history_data: list | None = None


class setHistoryDomain(BaseModel):
    session_key: str
    user_id: str

    conversation_history: list | None = None
    access_token: str | None = None
    refresh_token: str | None = None
