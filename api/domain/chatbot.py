from pydantic import ConfigDict, BaseModel
from datetime import datetime

from client.groxy import LLMProxyClient
from client.mysql import MySQLClient
from client.pinecone import PineconeClient
from client.milvus import MilvusClient
from client.redis import RedisClient
from client.aws import S3Client

from utils.date import get_utc_now



class checkChatbotKeyDomain(BaseModel):
    chatbot_key: str

    is_live: bool = False


class chatDomain(BaseModel):
    service: str
    vendor: str
    model: str | None = None
    question: str
    answer_id: str
    session_key: str
    company_key: str
    credit_available: int
    info: dict
    start_time: float
    vector_db_index: str | None = None
    vector_db_namespace: str | None = None
    vector_db_embedding_model: str | None = None
    llm_proxy_client: LLMProxyClient | None = None
    main_db_client: MySQLClient | None = None
    vector_db_client: PineconeClient | MilvusClient | None = None
    memory_db_client: RedisClient | None = None
    s3_client: S3Client | None = None
    is_mcp: bool = False
    lang: str | None = None
    store_name: str | None = None
    file_id: int | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class getConversationHistoryDomain(BaseModel):
    session_key: str

    history_data: list = []
    answer_ids: list = []
    ratings_list: list = []

    reform_data: list = []
