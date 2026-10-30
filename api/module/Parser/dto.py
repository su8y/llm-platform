from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from client.aws import S3Client
from client.pinecone import PineconeClient
from client.groxy import LLMProxyClient
from client.rabbit import RabbitMQClient
from client.slack import SlackClient
from queries.company_info import CompanyInfoQuery
from queries.file_credit_history import FileCreditHistoryQuery
from queries.drive import DriveQuery
from queries.vector import VectorQuery
from queries.upload_file import UploadFileQuery




@dataclass
class sendArgs:
    db: AsyncSession
    cloud_storage_client: S3Client
    upload_file_query: UploadFileQuery
    drive_query: DriveQuery
    message_broker_client: RabbitMQClient
    # self.info: dict = info # = {"drive_ids": drive_ids, "file_data": data, "company_key": company_key, "stage": stage, "vector_db_index": vector_db_index, "vector_db_namespace": vector_db_namespace}
    drive_ids: list[int]
    file_data: list[dict]
    company_key: str
    stage: str
    vector_db_index: str
    vector_db_namespace: str
    queue_name: str
    init_from: str

    error_page: list | None = None
    all_page: int | None = None


@dataclass
class callbackArgs:
    db: AsyncSession
    s3_client: S3Client
    vector_db_client: PineconeClient
    llm_proxy_client: LLMProxyClient
    vector_query: VectorQuery
    drive_query: DriveQuery
    company_info_query: CompanyInfoQuery
    file_credit_query: FileCreditHistoryQuery
    status: str
    id: int
    company_key: str
    file_s3_path: str
    vector_db_index: str
    vector_db_namespace: str
    server_stage: str
    error_page: list | None = None
    # vector db info
    vector_ids: list[str] | None = None
    vector_values: list | None = None
    vector_metadatas: list | None = None


