from dataclasses import dataclass

from client.mysql import MySQLClient
from client.redis import RedisClient
from client.groxy import LLMProxyClient
from client.aws import S3Client



@dataclass
class MCPArgs:
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
    llm_proxy_client: LLMProxyClient
    s3_client: S3Client

    # agent result
    lang: str = None
    lang_detected: str = None
    language_message: str = None

    # groxy args
    question: str = None
    reference: dict = None
    system_message: str = None
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

    # for mcp
    mcp_server: str = None
    mcp_token: str = None
    mcp_allowed_tools: list | None = None
    is_mcp: bool = True

    # filesearch
    store_name: str | None = None
