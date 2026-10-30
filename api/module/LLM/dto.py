from dataclasses import dataclass

from client.mysql import MySQLClient
from client.redis import RedisClient
from client.pinecone import PineconeClient
from client.groxy import LLMProxyClient
from client.aws import S3Client



@dataclass
class LLMArgs:
    # session info
    service: str
    session_key: str
    company_key: str

    # vendor, model info
    vendor: str
    model: str

    # client
    main_db_client: MySQLClient
    memory_db_client: RedisClient
    vector_db_client: PineconeClient
    llm_proxy_client: LLMProxyClient
    s3_client: S3Client

    # vector db info
    vector_db_index: str
    vector_db_namespace: str
    vector_db_embedding_model: str

    # file_id
    file_id: int = None

    # is_mcp
    is_mcp: bool = False

    # system prompt
    on_llm_platform_system: bool = True

    # agent result
    lang: str = None
    lang_detected: str = None
    language_message: str = None

    # groxy args
    question: str = None
    reference: dict = None
    system_message: str | None = None
    system_message_placeholder: dict = None
    retrieval_data: list = None
    conversation_history: list = None
    temperature: float = None
    callback: object = None
    callback_args: dict = None

    # extra args
    info: dict = None
    time_info: dict = None
    chat_info: dict = None
    info_eagle: dict = None
    filename: str = None
    redis_save: bool = True
    streaming: bool = True
    start_time: float = None

    # for callback
    message: str = None
    credit_available: int = None
    answer_id: str = None

    # filesearch
    store_name: str | None = None
