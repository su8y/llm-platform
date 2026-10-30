from datetime import datetime

from dataclasses import dataclass

from client.mysql import MySQLClient
from client.pinecone import PineconeClient
from client.groxy import LLMProxyClient
from client.aws import S3Client



@dataclass
class LLMEmailArgs:
    # session info
    id: int
    service: str
    session_key: str
    company_key: str
    user_id: str
    current_time: datetime
    action_code: int

    
    # vendor, model info
    vendor: str
    model: str
    
    # client
    main_db_client: MySQLClient
    vector_db_client: PineconeClient
    llm_proxy_client: LLMProxyClient
    s3_client: S3Client
    
    # vector db info
    vector_db_index: str
    vector_db_namespace: str
    vector_db_embedding_model: str
    
    # agent result
    lang: str = None
    language_message: str = None

    # groxy args
    reference:str = None
    question: str = None
    system_message: str = None
    system_message_placeholder: dict = None
    retrieval_data: list = None
    email_rag_data: list = None
    conversation_history: list = None
    temperature: float = None
    callback: object = None
    callback_args: dict = None
    
    # extra args
    info: dict = None
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