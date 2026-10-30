from pydantic import BaseModel
from datetime import datetime

from fastapi import UploadFile



class uploadFileDomain(BaseModel):
    server_stage: str
    company_key: str
    company_name: str
    parser_credit_available: int
    files: list[UploadFile]
    thumnail_s3_path: str | None = None
    reg_date: datetime
    update_date: datetime
    upload_user_id: str
    drive_path_id: int
    is_on: bool
    is_show: bool
    status: int
    vector_db_index: str
    vector_db_namespace: str
    queue_name: str
    debug_id: str
    store_name: str | None = None

    temp_s3_info: list | None = []
    filesearch_payload: dict | None = {}
    filesearch_response: dict | None = None

    page_count: int | None = None
    file_data: list[dict] = []
    drive_ids: list[int] = []
    parser_args: dict | None = None


class retryDomain(BaseModel):
    company_key: str
    file_ids: list[int] | int
    server_stage: str
    vector_db_index: str
    vector_db_namespace: str
    queue_name: str

    drive_rows: list[dict] | None = None
    error_page: list[int] | None = None

    # for parser send, callback
    drive_ids: list[int] | None = None
    id: int | None = None
    file_s3_path: str | None = None
    status: str | None = None


class makeDirectoryDomain(BaseModel):
    company_key: str
    dir_name: str
    parent_id: int
    reg_date: datetime
    update_date: datetime

    parent_depth: int | None = None


class GetStatusDomain(BaseModel):
    company_key: str
    file_id: int
    status: int
    current_time: datetime

    drive_row: dict | None = None
    update_status: int | None = None

    response: dict | None = None


class getPageDomain(BaseModel):
    company_key: str
    user_id: str
    parser_credit_available: int | None = None
    is_home: bool | None = None
    dir_id: int | None = None
    page: int | None = None
    per_page: int | None = None
    name: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_show: bool | None = True
    is_deleted: bool | None = False

    current_dir_id: int | None = None
    dir_in_current_page: list[dict] | None = None
    file_in_current_page: list[dict] | None = None

    reform_row: dict | None = None


class searchDomain(BaseModel):
    company_key: str
    is_on: bool | None = None
    is_show: bool | None = None
    filetype: str | None = None
    name: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    page: int
    per_page: int

    files: list[dict] | None = None
    directories: list[dict] | None = None

    reform_row: dict | None = None


class getFileInfoDomain(BaseModel):
    company_key: str
    file_id: int

    row: dict | None = None
    reform_row: dict | None = None


class fileViewDomain(BaseModel):
    company_key: str
    file_id: int
    page: int

    row: dict | None = None
    all_page: list[dict] | None = None
    reform_row: dict | None = None


class GetFilenamesDomain(BaseModel):
    company_key: str

    page: int
    per_page: int

    row: dict | None = None


class downloadFileDomain(BaseModel):
    company_key: str
    drive_id: int

    row: dict | None = None
    s3_bucket_name: str | None = None
    s3_object_name: str | None = None
    s3_presigned_url: str | None = None


class moveToDirectoryDomain(BaseModel):
    company_key: str
    drive_id: int | None = None
    drive_path_id: int | None = None
    to_dir_id: int


class renameDomain(BaseModel):
    company_key: str
    drive_id: int | None = None
    drive_path_id: int | None = None
    new_name: str
    is_file: bool
    is_dir: bool


class updateParserCreditAvailableDomain(BaseModel):
    company_key: str
    parser_credit_available: int


class updateFileContentDomain(BaseModel):
    company_key: str
    drive_id: int
    target_pages: list[int] | list[str]
    contents: list[str]
    service: str
    vector_db_index: str
    vector_db_namespace: str
    current_time: datetime

    vector_ids: list[str] | None = []
    vector_values: list | None = []
    vector_metadatas: list[dict] | None = []


class EnrollFileSearchStoreDomain(BaseModel):
    server_stage: str
    company_key: str
    company_name: str
    store_name: str | None = None


class deleteDomain(BaseModel):
    company_key: str
    file_id: int
    vector_db_index: str
    vector_db_namespace: str

    upload_file_id: int | None = None
    vector_ids: list[str] | str = []
    vector_metadatas: list[dict] | None = []


class deleteFileDomain(BaseModel):
    company_key: str
    file_id: int
    vector_db_index: str
    vector_db_namespace: str

    upload_file_id: int | None = None
    vector_ids: list = []
    vector_ids_target_to_delete_vector_db: list = []
