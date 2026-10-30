import asyncio
from io import BytesIO
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Tuple, Type
from pypdf import PdfReader
from markdown import markdown
from bs4 import BeautifulSoup

from client.aws import S3Client
from client.pinecone import PineconeClient
from client.milvus import MilvusClient
from client.rabbit import RabbitMQClient
from client.groxy import LLMProxyClient
from queries.drive import DriveQuery
from queries.file_credit_history import FileCreditHistoryQuery
from queries.drive_path import DrivePathQuery
from queries.upload_file import UploadFileQuery
from queries.vector import VectorQuery
from queries.company_info import CompanyInfoQuery
from payload.drive import *
from domain.drive import *
from module.Parser.send import ToParser
from module.Parser.callback import FromParser
from utils.date import *
from utils.error import *
from utils.vector import chunking_text



def helper_upload_file_make_domain_data(payload: uploadFileFormData, user_info: dict, files: List[UploadFile], stage: str, queue_name: str) -> uploadFileDomain:
    try:
        current_time = get_utc_now()
        server_stage = REAL if os.getenv("SERVER_STAGE") == REAL else STAGING if os.getenv("SERVER_STAGE") == STAGING else DEV
        domain_data = uploadFileDomain(
            server_stage=server_stage,
            company_key=user_info["company_key"],
            company_name=user_info["company_name"],
            parser_credit_available=user_info["parser_credit_available"],
            files=files,
            reg_date=current_time,
            update_date=current_time,
            upload_user_id=user_info["user_id"],
            drive_path_id=int(payload.current_dir_id),
            is_on=True,
            is_show=False,
            status=PENDING,
            vector_db_index=user_info["vector_db_index"],
            vector_db_namespace=user_info["vector_db_namespace"],
            queue_name=queue_name,
            debug_id=str(uuid4()).replace("-", ""),
            store_name=user_info["store_name"]
        )
        return domain_data
    except DataError as e:
        logging.error(f"[drive.helper.helper_upload_file_make_domain_data] DataError: {e}")
        raise DataError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_upload_file_make_domain_data] Exception: {e}")
        raise Exception(f"[drive.helper.helper_upload_file_make_domain_data] Exception: {e}")


async def helper_upload_file_upload_for_debug(s3:S3Client, domain_data:uploadFileDomain):
    try:
        tasks = list()
        for file in domain_data.files:
            contents = await file.read()
            await file.seek(0)

            file_name = file.filename
            file_obj = BytesIO(contents)

            bucket = "llm-platform-temp"
            key = f"drive/{domain_data.server_stage}/{domain_data.company_key}/{domain_data.debug_id}/{file_name}"
            tasks.append(s3.upload_to_s3(file_obj, bucket, key))
            domain_data.temp_s3_info.append({"bucket": bucket, "key": key})
        await asyncio.gather(*tasks)

    except AWSError as e:
        logging.error(f"[drive.helper.helper_upload_file_for_debug] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_upload_file_for_debug] Exception: {e}")
        raise e


async def helper_upload_file_check_page_is_over_parser_credit_available(domain_data: uploadFileDomain):
    try:
        if domain_data.parser_credit_available == 0:
            raise ParserCreditAvailableOverError()

        domain_data.page_count = 0
        for file in domain_data.files:
            filetype = file.filename.split(".")[-1]
            if filetype != "pdf":
                logging.info(f"[drive.helper.helper_upload_file_check_page_is_over_parser_credit_available] File type is not pdf: {filetype}")
                raise Exception("File type is not pdf")

            contents = await file.read()
            await file.seek(0)
            with BytesIO(contents) as file_obj:
                pdf_reader = PdfReader(file_obj)
                domain_data.page_count += len(pdf_reader.pages)

        if domain_data.page_count > domain_data.parser_credit_available:
            raise ParserCreditAvailableOverError()

    except ParserCreditAvailableOverError as e:
        logging.error(f"[drive.helper.helper_upload_file_check_page_is_over_parser_credit_available] ParserCreditAvailableOverError: {e}")
        raise ParserCreditAvailableOverError()
    except Exception as e:
        logging.error(f"[drive.helper.helper_upload_file_check_page_is_over_parser_credit_available] Exception: {e}")
        raise Exception(e)


async def helper_upload_file_make_data(domain_data: uploadFileDomain):
    try:
        for file in domain_data.files:
            contents = await file.read()
            await file.seek(0)

            domain_data.file_data.append({
                "company_key": domain_data.company_key,
                "filename": file.filename,
                "filetype": file.filename.split(".")[-1],
                "filesize": len(contents),
                "fileobject": contents,
                "thumnail_s3_path": domain_data.thumnail_s3_path,
                "reg_date": domain_data.reg_date,
                "update_date": domain_data.update_date,
                "upload_user_id": domain_data.upload_user_id,
                "drive_path_id": domain_data.drive_path_id,
                "is_on": domain_data.is_on,
                "is_show": domain_data.is_show,
                "status": domain_data.status,
                "unit_count": domain_data.page_count
            })
    except DataError as e:
        logging.error(f"[drive.helper.helper_upload_file_make_data] DataError: {e}")
        raise DataError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_upload_file_make_data] Exception: {e}")
        raise Exception(e)


async def helper_upload_file_record_drive_in_db(db: AsyncSession, drive_query: DriveQuery, domain_data: uploadFileDomain):
    try:
        if len(domain_data.file_data) == 1:
            domain_data.drive_ids = await drive_query.insert_drive_row(db, domain_data)
        elif len(domain_data.file_data) > 1:
            domain_data.drive_ids = await drive_query.bulk_insert_drive_row(db, domain_data)

    except DBError as e:
        logging.error(f"[drive.helper.helper_upload_file_record_drive_in_db] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_upload_file_record_drive_in_db] Exception: {e}")
        raise Exception(e)


async def helper_upload_file_update_is_show(db: AsyncSession, drive_query: DriveQuery, domain_data: uploadFileDomain):
    try:
        domain_data.is_show = True
        await drive_query.update_is_show(db, domain_data)
    except DBError as e:
        logging.error(f"[drive.helper.helper_upload_file_update_is_show] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_upload_file_update_is_show] Exception: {e}")
        raise Exception(e)


async def helper_upload_file_delete_for_debug(s3:S3Client, domain_data: uploadFileDomain):
    try:
        tasks = list()
        for temp_s3_info in domain_data.temp_s3_info:
            if not temp_s3_info: pass
            else: tasks.append(s3.delete_on_s3(bucket_name=temp_s3_info["bucket"], object_name=temp_s3_info["key"]))
        await asyncio.gather(*tasks)
    except AWSError as e:
        logging.error(e)
    except Exception as e:
        logging.error(e)


async def helper_upload_file_to_s3(s3_client: S3Client, domain_data: uploadFileDomain):
    try:
        # set bucket
        bucket_name = PARSER_S3_BUCKET_NAME

        # set key
        domain_data.filesearch_payload['keys'] = []
        for _id, file in zip(domain_data.drive_ids, domain_data.file_data):
            file_obj = BytesIO(file.get("fileobject"))
            object_name = f"{domain_data.server_stage}/{domain_data.company_key}/drive-{_id}/{file.get('filename')}"
            await s3_client.upload_to_s3(file_obj, bucket_name, object_name)
            domain_data.filesearch_payload['keys'].append(object_name)

        # set payload
        length_of_keys = len(domain_data.filesearch_payload['keys'])
        domain_data.filesearch_payload["buckets"] = [bucket_name for _ in range(length_of_keys)]

    except AWSError as e:
        logging.error(f"[helper.drive.helper_upload_file_to_s3] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[helper.drive.helper_upload_file_to_s3] Exception: {e}")
        raise Exception(e)


async def helper_upload_file_request_import_file_to_llm_proxy(llm_proxy_client: LLMProxyClient, domain_data: uploadFileDomain):
    try:
        service = SERVICE_LLM_PLATFORM_REAL if domain_data.server_stage == REAL else SERVICE_LLM_PLATFORM_STAGING
        domain_data.filesearch_response = await llm_proxy_client.import_files(
            service=service,
            store_name=domain_data.store_name,
            buckets=domain_data.filesearch_payload["buckets"],
            keys=domain_data.filesearch_payload["keys"],
        )

    except LLMProxyError as e:
        logging.error(f"[helper.drive.helper_upload_file_request_import_file_to_llm_proxy] LLMProxyError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[helper.drive.helper_upload_file_request_import_file_to_llm_proxy] Exception: {e}")
        raise Exception(e)


async def helper_upload_file_update_insert_upload_file_row(
        db: AsyncSession,
        upload_file_query: UploadFileQuery,
        drive_query: DriveQuery,
        domain_data: uploadFileDomain
):
    try:
        # value check
        length_of_request_files = len(domain_data.drive_ids)
        is_length_same:bool = length_of_request_files == len(domain_data.filesearch_payload["buckets"]) == len(domain_data.filesearch_payload["keys"]) == len(domain_data.filesearch_response["documentName"])
        if not is_length_same:
            message = f"is_length_same is False. please check length | drive_ids: {length_of_request_files}, buckets: {len(domain_data.filesearch_payload['buckets'])}, {len(domain_data.filesearch_payload['keys'])}, {len(domain_data.filesearch_payload['documentName'])}"
            raise ValueError(message)

        # insert row to upload_file table
        if length_of_request_files > 1:
            upload_file_ids = await upload_file_query.bulk_record_upload_file_history_for_filesearch(db, domain_data)
        elif length_of_request_files == 1:
            upload_file_id = await upload_file_query.record_upload_file_history_for_filesearch(db, domain_data)
            upload_file_ids = [upload_file_id]
        else:
            message = f"is_length_same is 0. please check length | drive_ids: {length_of_request_files}"
            raise ValueError(message)

        # update status
        await drive_query.update_drive_row_status_and_upload_file_id(
            db=db,
            ids=domain_data.drive_ids,
            upload_file_ids=upload_file_ids,
            status=4
        )

    except ValueError as e:
        logging.error(f"[drive.helper.helper_upload_file_update_insert_upload_file_row] ValueError: {e}")
        raise ValueError(e)
    except DBError as e:
        logging.error(f"[drive.helper.helper_upload_file_update_insert_upload_file_row] DBError: {e.message}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_upload_file_request_import_file_to_llm_proxy] Exception: {e}")
        raise Exception(e)


async def helper_upload_file_decrease_parser_credit_available(
        db: AsyncSession,
        file_credit_query: FileCreditHistoryQuery,
        domain_data: uploadFileDomain
):
    try:
        drive_id = domain_data.drive_ids[0] if isinstance(domain_data.drive_ids, list) else domain_data.drive_ids
        await file_credit_query.decrease_parser_credit_available(
            db=db,
            company_key=domain_data.company_key,
            use_parser_credit=domain_data.page_count,
            drive_id=drive_id
        )

    except DBError as e:
        logging.error(f"[drive.helper.helper_upload_file_decrease_parser_credit_available] DBError: {e.message}]")
        raise DBError(e.message)
    except Exception as e:
        logging.error(f"[drive.helper.helper_upload_file_decrease_parser_credit_available] Exception: {e}]")
        raise Exception(e)



def helper_upload_file_make_parser_args(domain_data: uploadFileDomain):
    try:
        domain_data.parser_args = {
            "company_key": domain_data.company_key,
            "drive_ids": domain_data.drive_ids,
            "file_data": domain_data.file_data,
            "stage": domain_data.server_stage,
            "vector_db_index": domain_data.vector_db_index,
            "vector_db_namespace": domain_data.vector_db_namespace,
            "queue_name": domain_data.queue_name
        }
    except DataError as e:
        logging.error(f"[drive.helper.helper_upload_file_make_parser_args] DataError: {e}")
        raise DataError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_upload_file_make_parser_args] Exception: {e}")
        raise Exception(e)


def helper_retry_make_domain_data(payload: retryPayload, user_info: dict, server_stage: str, queue_name: str) -> retryDomain:
    try:
        file_ids = payload.file_id
        if isinstance(file_ids, int):
            file_ids = [file_ids]

        domain_data = retryDomain(
            company_key=user_info["company_key"],
            file_ids=file_ids,
            server_stage=server_stage,
            vector_db_index=user_info["vector_db_index"],
            vector_db_namespace=user_info["vector_db_namespace"],
            queue_name=queue_name
        )
        return domain_data
    except DataError as e:
        logging.error(f"[drive.helper.helper_retry_make_domain_data] DataError: {e}")
        raise DataError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_retry_make_domain_data] Exception: {e}")
        raise Exception(e)


async def helper_retry_get_file_info(db: AsyncSession, drive_query: DriveQuery, domain_data: retryDomain):
    try:
        domain_data.drive_rows = await drive_query.get_file_by_ids(db, domain_data)
    except DBError as e:
        logging.error(f"[drive.helper.helper_retry_get_file_info] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_retry_get_file_info] Exception: {e}")
        raise Exception(e)


async def helper_retry_update_status(db: AsyncSession, drive_query: DriveQuery, domain_data: retryDomain):
    try:
        await drive_query.update_status_to_analysis(db, domain_data)
    except DBError as e:
        logging.error(f"[drive.helper.helper_retry_update_status] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_retry_update_status] Exception: {e}")
        raise Exception(e)


async def helper_retry_module_activate(
    db: AsyncSession,
    domain_data: retryDomain,
    ToParser: Type[ToParser],
    FromParser: Type[FromParser],
    s3_client: S3Client,
    vector_db_client: PineconeClient | MilvusClient,
    llm_proxy_client: LLMProxyClient,
    message_broker: RabbitMQClient,
    upload_file_query: UploadFileQuery,
    drive_query: DriveQuery,
    vector_query: VectorQuery,
    company_info_query: CompanyInfoQuery
):
    try:
        for row in domain_data.drive_rows: # Why using for loop: for safety. if request multiple file ids, it could be fail or success.
            status = row["status"]
            if status in [PARSER_FAILED, FAIL_TO_DB, FAIL_TO_SEND_MESSAGE, PARSER_PARTIAL_ERROR]:
                stage = REAL if domain_data.server_stage == REAL else STAGING
                info = {
                    "company_key": domain_data.company_key,
                    "drive_ids": [row["id"]],
                    "stage": stage,
                    "vector_db_index": domain_data.vector_db_index,
                    "vector_db_namespace": domain_data.vector_db_namespace,
                    "queue_name": domain_data.queue_name
                }
                send = ToParser(db, s3_client, upload_file_query, drive_query, message_broker, info, init_from="drive")
                await send.reactivate(status)

            elif status in [PARSER_FAILED_NOT_SAME_COUNT, PARSER_FAILED_UPDATE_TO_VECTOR_DB]:
                domain_data.id = row["upload_file_id"]
                domain_data.file_s3_path = row["s3_path"].rsplit("/", 1)[0] + "/pages"
                domain_data.status = "success"
                callback = FromParser(db, s3_client, vector_db_client, llm_proxy_client, vector_query, drive_query, company_info_query, domain_data, domain_data.server_stage)
                await callback.reactivate(status)
    except Exception as e:
        logging.error(f"[drive.helper.helper_retry_module_activate] Exception: {e}")
        raise Exception(e)


def helper_make_directory_make_domain_data(payload: makeDirectoryPayload, user_info: dict) -> makeDirectoryDomain:
    try:
        current_time = get_utc_now()
        return makeDirectoryDomain(
            company_key=user_info["company_key"],
            dir_name=payload.dir_name,
            parent_id=payload.current_dir_id,
            reg_date=current_time,
            update_date=current_time,
        )
    except DataError as e:
        logging.error(f"[drive.helper.helper_make_directory_make_domain_data] DataError: {e}")
        raise DataError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_make_directory_make_domain_data] Exception: {e}")
        raise Exception(e)


async def helper_charge_credit(db:AsyncSession, companey_key:str, charge_credit:int):
    try:
        await FileCreditHistoryQuery.insert_credit_history(db, companey_key, charge_credit)
    except DBError as e:
        logging.error(f"[drive.helper.helper_charge_credit] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_charge_credit] Exception: {e}")
        raise Exception(e)



async def helper_get_status(db:AsyncSession, s3_client:S3Client, drive_query:DriveQuery, domain_data:GetStatusDomain):
    try:
        domain_data.drive_row = await drive_query.get_file_by_id(db, domain_data)
        status = domain_data.drive_row.get("status")
        is_s3_path = domain_data.drive_row.get("s3_path") and isinstance(domain_data.drive_row["s3_path"], str)
        if is_s3_path:
            bucket_and_key = (domain_data.drive_row["s3_path"].rsplit("/", 1)[0] + "/pages").split(":")
            bucket_name = bucket_and_key[0]
            object_name = bucket_and_key[1]
            complete_cnt = await s3_client.get_file_list_cnt_in_bucket(bucket_name=bucket_name, object_name=object_name)

            if status == PENDING:
                if not complete_cnt:
                    domain_data.response = {
                        "fileId": domain_data.drive_row.get("id"),
                        "status": PENDING,
                        "completePage": None,
                        "totalPage": None
                    }
                else:
                    domain_data.update_status = ANALYZING
                    await drive_query.update_drive_row_status(db, domain_data.file_id, domain_data.update_status)
                    domain_data.response = {
                        "fileId": domain_data.drive_row.get("id"),
                        "status": domain_data.update_status,
                        "completePage": complete_cnt,
                        "totalPage": domain_data.drive_row.get("unit_count")
                    }

            elif status == ANALYZING:
                domain_data.response = {
                    "fileId": domain_data.drive_row.get("id"),
                    "status": status,
                    "completePage": complete_cnt,
                    "totalPage": domain_data.drive_row.get("unit_count")
                }

            elif status == FINISHED:
                domain_data.response = {
                    "fileId": domain_data.drive_row.get("id"),
                    "status": FINISHED,
                    "completePage": None,
                    "totalPage": None
                }

            else: # for checking status
                domain_data.response = {
                    "fileId": domain_data.drive_row.get("id"),
                    "status": status,
                    "completePage": complete_cnt,
                    "totalPage": domain_data.drive_row.get("unit_count")
                }

        elif domain_data.current_time > adapt_timezone_datetime_to_datetime(domain_data.drive_row.get("reg_date"), "UTC") + timedelta(hours=6):
            domain_data.update_status = PARSER_FAILED
            await drive_query.update_drive_row_status(db, domain_data.file_id, domain_data.update_status)
            domain_data.response = {
                "fileId": domain_data.drive_row.get("id"),
                "status": domain_data.update_status,
                "completePage": None,
                "totalPage": None
            }

        else:
            domain_data.response = {
                "fileId": domain_data.drive_row.get("id"),
                "status": status if status in [PENDING, SUCCESS_TO_S3, ANALYZING, FAILED] else PARSER_FAILED if status in ERROR_STATUS_LIST else 4,
                "completePage": None,
                "totalPage": None
            }


    except AppError:
        raise
    except DBError as e:
        logging.error(f"[helper.drive.helper_get_status] DBError: {e}")
        raise DBError(e)
    except AWSError as e:
        logging.error(f"[helper.drive.helper_get_status] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[helper.drive.helper_get_status] Exception: {e}")
        raise Exception(e)


def helper_get_page_make_domain_data(query_params: getPageQueryParams, user_info: dict) -> getPageDomain:
    try:
        is_home = True if query_params.dir_id is None else False
        return getPageDomain(
            company_key=user_info["company_key"],
            user_id=user_info["user_id"],
            parser_credit_available=user_info["parser_credit_available"],
            dir_id=query_params.dir_id,
            is_home=is_home,
            # filter
            page=query_params.page,
            per_page=query_params.per_page,
            name=query_params.name,
            start_date=string_to_datetime(query_params.start_date, "UTC"),
            end_date=get_last_hour_of_day(query_params.end_date, "UTC"),
        )
    except DataError as e:
        logging.error(f"[drive.helper.helper_get_page_make_domain_data] DataError: {e}")
        raise DataError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_get_page_make_domain_data] Exception: {e}")
        raise Exception(e)


async def helper_get_page_get_current_dir_datas(db: AsyncSession, drive_path_query: DrivePathQuery, domain_data: getPageDomain):
    try:
        domain_data.current_dir_id = await drive_path_query.get_home_directory(db, domain_data) if domain_data.is_home else int(domain_data.dir_id)
        domain_data.dir_in_current_page = await drive_path_query.get_directories_by_parent_id(db, domain_data)
    except DBError as e:
        logging.error(f"[drive.helper.helper_get_page_get_current_dir_datas] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_get_page_get_current_dir_datas] Exception: {e}")
        raise Exception(e)


async def helper_get_page_get_file_in_current_page(db: AsyncSession, drive_query: DriveQuery, domain_data: getPageDomain):
    try:
        domain_data.file_in_current_page = await drive_query.get_files_in_directory_with_pagination(db, domain_data)
    except DBError as e:
        logging.error(f"[drive.helper.helper_get_page_get_file_in_current_page] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_get_page_get_file_in_current_page] Exception: {e}")
        raise Exception(e)


def helper_get_drive_page_reform_data(domain_data: getPageDomain):
    try:
        domain_data.reform_row = {
            "directories": domain_data.dir_in_current_page,
            "files": domain_data.file_in_current_page,
            "currentDirId": domain_data.current_dir_id,
            "parserCreditAvailable": domain_data.parser_credit_available
        }
    except DataError as e:
        logging.error(f"[drive.helper.helper_get_drive_page_reform_data] DataError: {e}")
        raise DataError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_get_drive_page_reform_data] Exception: {e}")
        raise Exception(e)


def helper_search_make_domain_data(payload: searchPayload, user_info: dict) -> searchDomain:
    try:
        return searchDomain(
            company_key=user_info["company_key"],
            is_on=payload.is_on,
            is_show=payload.is_show,
            filetype=payload.filetype,
            name=payload.name,
            start_date=string_to_datetime(payload.start_date, "UTC"),
            end_date=get_last_hour_of_day(payload.end_date, "UTC"),
            page=payload.page,
            per_page=payload.per_page
        )
    except DataError as e:
        logging.error(f"[drive.helper.helper_search_make_domain_data] DataError: {e}")
        raise DataError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_search_make_domain_data] Exception: {e}")
        raise Exception(e)


# def helper_search_make_query_data_for_file(payload: searchPayload, user_info: dict) -> Dict:
#   try:
#       filters = {"company_key": user_info["company_key"], "status": 0}
#       optional_filters = ["is_on", "is_show", "filetype", "name"]
#       for filter_key in optional_filters:
#           filter_value = getattr(payload, filter_key, None)
#           if filter_value is not None:
#               filters[filter_key] = filter_value

#       start_date =
#       end_date = )
#       page = payload.page
#       per_page = payload.per_page

#       return {
#           "start_date": start_date,
#           "end_date": end_date,
#           "filters": filters,
#           "page": page,
#           "per_page": per_page
#       }
#   except Exception as e:
#       logging.error(f"[drive.helper.helper_search_make_query_data] Failed to make query data: {e}")
#       raise Exception(f"[drive.helper.helper_search_make_query_data] Failed to make query data: {e}")


# def helper_search_make_query_data_for_dir(payload: dict, user_info: dict) -> Dict:
#   try:
#       filters = {"company_key": user_info["company_key"]}
#       start_date = string_to_datetime(payload.get("startDate"), "UTC")
#       end_date = get_last_hour_of_day(payload.get("endDate"), "UTC")
#       dir_name = payload.get("name")

#       return {
#           "name": dir_name,
#           "start_date": start_date,
#           "end_date": end_date,
#           "filters": filters
#       }
#   except Exception as e:
#       logging.error(f"[drive.helper.helper_search_make_query_data] Failed to make query data: {e}")
#       raise Exception(f"[drive.helper.helper_search_make_query_data] Failed to make query data: {e}")


async def helper_search_files_from_db(db: AsyncSession, drive_query: DriveQuery, domain_data: searchDomain) -> List[Dict]:
    try:
        domain_data.files = await drive_query.search(db, domain_data)
    except DBError as e:
        logging.error(f"[drive.helper.helper_search_files_from_db] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_search_files_from_db] Exception: {e}")
        raise Exception(e)


async def helper_search_dir_from_db(db: AsyncSession, drive_path_query: DrivePathQuery, domain_data: searchDomain) -> List[Dict]:
    try:
        domain_data.directories = await drive_path_query.search(db, domain_data)
    except DBError as e:
        logging.error(f"[drive.helper.helper_search_dir_from_db] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_search_dir_from_db] Exception: {e}")
        raise Exception(e)


def helper_search_reform_data(domain_data: searchDomain) -> Dict:
    try:
        domain_data.reform_row = {
            "files": domain_data.files,
            "directories": domain_data.directories
        }
    except DataError as e:
        logging.error(f"[drive.helper.helper_search_reform_data] DataError: {e}")
        raise DataError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_search_reform_data] Exception: {e}")
        raise Exception(e)


async def helper_get_file_info_reform_data(s3_client: S3Client, domain_data: getFileInfoDomain) -> Dict:
    try:
        thumbnail = await _download_thumbnail(s3_client, domain_data.row["thumnail_s3_path"]) if domain_data.row.get("thumnail_s3_path") else None

        if domain_data.row["status"] in [1,2,3]:
            status = 3
        elif domain_data.row["status"] == FAILED:
            status = 0
        elif domain_data.row["status"] in [FAIL_TO_DB, FAIL_TO_SEND_MESSAGE, PARSER_FAILED, PARSER_FAILED_NOT_SAME_COUNT, PARSER_FAILED_UPDATE_TO_VECTOR_DB]:
            status = 5
        else:
            status = 4

        result = {
            "fileId": domain_data.row["id"],
            "fileName": domain_data.row["filename"],
            "fileType": domain_data.row["filetype"],
            "fileSize": domain_data.row["filesize"],
            "regDate": domain_data.row["reg_date"],
            "updateDate": domain_data.row["update_date"],
            "uploadUserId": domain_data.row["upload_user_id"],
            "status": status,
            "thumbnail": thumbnail,
        }

        # if domain_data.row.get("status") == 4 and domain_data.row.get("s3_path"):
        #   page_files, page_file_list = await _download_page_files(s3_client, domain_data.row["s3_path"])
        #   result["pageFile"] = page_files
        #   result["pageFileList"] = page_file_list

        domain_data.reform_row = result

    except AWSError as e:
        logging.error(f"[drive.helper.helper_get_file_info_reform_data] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_get_file_info_reform_data] Exception: {e}")
        raise Exception(e)


async def _download_thumbnail(s3_client: S3Client, thumbnail_s3_path: str) -> bytes:
    try:
        bucket = thumbnail_s3_path.split("/")[0]
        key = thumbnail_s3_path.split("/")[1]
        response = await s3_client.download_file(bucket=bucket, key=key)
        return response
    except AWSError as e:
        logging.error(f"[drive.helper.download_thumbnail] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[drive.helper.download_thumbnail] Exception: {e}")
        raise Exception(e)


async def _download_page_files(s3_client: S3Client, s3_path_of_file: str) -> Tuple[List[str], List[Dict]]:
    try:
        def get_page_number(key: str) -> int:
            return int(key.split('/')[-1].split('.')[0])

        bucket_name = s3_path_of_file.split(":")[0]
        file_path = s3_path_of_file.split(":")[1]
        object_name = "/".join(file_path.split("/")[:-1])+"/pages/"

        #TODO: s3_client
        data, data_list = await s3_client.get_file_from_parser(bucket_name, object_name)

        sorted_file_list = sorted(data_list, key=lambda x: get_page_number(x['key']))
        sorted_page_file = [
            page for _, page in sorted(zip(data_list, data),
            key=lambda pair: get_page_number(pair[0]['key']))
        ]

        return ([item.decode("utf-8") for item in sorted_page_file], sorted_file_list)

    except AWSError as e:
        logging.error(f"[drive.helper.download_page_files] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[drive.helper.download_page_files] Exception: {e}")
        raise Exception(e)


async def helper_file_view_get_data_from_db(db: AsyncSession, drive_query: DriveQuery, vector_query: VectorQuery, domain_data: fileViewDomain):
    try:
        domain_data.row = await drive_query.get_file_by_id(db, domain_data)
        domain_data.all_page = await vector_query.get_all_page(db, domain_data) if domain_data.page else None
    except AppError:
        raise
    except DBError as e:
        logging.error(f"[drive.helper.helper_file_view_get_data_from_db] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_file_view_get_data_from_db] Exception: {e}")
        raise Exception(e)


async def helper_get_filenames_from_db(db:AsyncSession, drive_query:DriveQuery, domain_data:GetFilenamesDomain):
    try:
        domain_data.row = await drive_query.get_filename_and_id(db, domain_data)
    except DBError as e:
        logging.error(f"[drive.helper.helper_get_filenames_from_db] DBError: {e.message}")
    except Exception as e:
        logging.error(f"[drive.helper.helper_get_filenames_from_db] Exception: {e}")


async def helper_get_file_content_and_all_page(
    s3_client: S3Client,
    domain_data: fileViewDomain
) -> Dict:
    try:
        result = {
            "currentPage": domain_data.page,
            "error": True
        }

        if domain_data.all_page:
            result["allPage"] = sorted(list(set(domain_data.all_page)))

        if domain_data.row.get("s3_path"):
            s3_path = domain_data.row["s3_path"].rsplit("/", 1)[0] + "/pages/" + str(domain_data.page) + ".text"
            bucket, key = s3_path.split(":")
            file, is_error = await s3_client.get_file_from_s3(bucket_name=bucket, object_name=key)
            result["content"] = file.decode("utf-8") if file else ""
            result["error"] = is_error

        result["unitCount"] = domain_data.row["unit_count"] if domain_data.row.get("unit_count") else max(domain_data.all_page)

        domain_data.reform_row = result

    except AWSError as e:
        logging.error(f"[drive.helper.helper_get_file_content_and_all_page] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_get_file_content_and_all_page] Exception: {e}")
        raise Exception(e)


async def helper_download_get_s3_path_from_db(db: AsyncSession, upload_file_query: UploadFileQuery, domain_data: downloadFileDomain):
    try:
        domain_data.row = await upload_file_query.get_s3_path_by_drive_id(db, domain_data)
    except DBError as e:
        logging.error(f"[drive.helper.helper_download_get_s3_path_from_db] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_download_get_s3_path_from_db] Exception: {e}")
        raise Exception(e)


async def helper_download_get_s3_presigned_url(s3_client: S3Client, domain_data: downloadFileDomain):
    try:
        domain_data.s3_bucket_name = domain_data.row["s3_path"].split(":")[0]
        domain_data.s3_object_name = domain_data.row["s3_path"].split(":")[1]
        domain_data.s3_presigned_url = await s3_client.generate_presigned_url(
            bucket_name=domain_data.s3_bucket_name,
            object_name=domain_data.s3_object_name,
            expires_in=3600,  # 1시간
            response_headers={
                'response-content-disposition': f'attachment; filename="{domain_data.row["filename"]}"',
                'response-content-type': f'application/{domain_data.row["filetype"]}'
            }
        )
    except AWSError as e:
        logging.error(f"[drive.helper.helper_download_get_s3_presigned_url] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_download_get_s3_presigned_url] Exception: {e}")
        raise Exception(e)


async def helper_move_to_dir(db: AsyncSession, drive_query: DriveQuery, drive_path_query: DrivePathQuery, domain_data: moveToDirectoryDomain):
    try:
        if not domain_data.drive_id and not domain_data.drive_path_id:
            raise DataError("Invalid request")
        if domain_data.drive_id:
            await drive_query.move_file(db, domain_data)
        if domain_data.drive_path_id:
            if domain_data.to_dir_id == domain_data.drive_path_id:
                raise DataError("Cannot move a folder into itself")
            if await drive_path_query.is_home_directory(db, domain_data.company_key, domain_data.drive_path_id):
                raise DataError("Cannot move the root folder")
            descendants = await drive_path_query.get_descendant_dir_ids(db, domain_data.company_key, domain_data.drive_path_id)
            if domain_data.to_dir_id in descendants:
                raise DataError("Cannot move a folder into its own subfolder")
            await drive_path_query.move_directory(db, domain_data)

    except AppError:
        raise
    except Exception as e:
        logging.error(f"[drive.helper.helper_move_to_dir] Exception: {e}")
        raise Exception(e)


async def helper_delete_directory(db: AsyncSession, drive_query: DriveQuery, drive_path_query: DrivePathQuery, vector_query: VectorQuery, vector_db_client, company_key: str, dir_id: int, vector_db_index: str, vector_db_namespace: str) -> int:
    """폴더와 하위 폴더를 삭제한다. 안의 파일은 파일 삭제와 같은 절차(소프트 삭제 + 벡터 비활성)를 거친다. 반환: 삭제한 파일 수"""
    if await drive_path_query.is_home_directory(db, company_key, dir_id):
        raise DataError("Cannot delete the root folder")
    dir_ids = [dir_id] + await drive_path_query.get_descendant_dir_ids(db, company_key, dir_id)
    file_ids = await drive_query.get_active_file_ids_in_directories(db, company_key, dir_ids)
    for file_id in file_ids:
        file_domain = deleteDomain(company_key=company_key, file_id=file_id, vector_db_index=vector_db_index, vector_db_namespace=vector_db_namespace)
        await helper_delete_update_is_delete_and_is_on(db, drive_query, file_domain)
        await helper_delete_update_is_on_of_vector_table(db, vector_query, file_domain)
        await helper_delete_get_vector_ids_and_metadatas(db, vector_query, file_domain)
        await helper_delete_update_is_on_in_vector_db(vector_db_client, file_domain)
    await drive_query.detach_files_from_directories(db, company_key, dir_ids)
    for child_id in reversed(dir_ids):        # 깊은 폴더부터 (self FK)
        await drive_path_query.remove_directory_by_id(db, child_id, company_key)
    return len(file_ids)


def helper_rename_make_domain_data(payload: renamePayload, user_info: dict) -> renameDomain:
    try:
        is_dir = True if payload.dir_id else False
        is_file = True if payload.file_id else False

        return renameDomain(
            company_key=user_info["company_key"],
            drive_id=payload.file_id,
            drive_path_id=payload.dir_id,
            new_name=payload.new_name,
            is_dir=is_dir,
            is_file=is_file
        )

    except DataError as e:
        logging.error(f"[drive.helper.helper_rename_make_domain_data] DataError: {e}")
        raise DataError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_rename_make_domain_data] Exception: {e}")
        raise Exception(e)


async def helper_rename_file_or_directory(db: AsyncSession, drive_query: DriveQuery, drive_path_query: DrivePathQuery, domain_data: renameDomain):
    try:
        if domain_data.is_file and domain_data.is_dir:
            raise DataError("Invalid request")
        elif domain_data.is_file:
            await drive_query.rename_file(db, domain_data)
        elif domain_data.is_dir:
            await drive_path_query.rename_directory(db, domain_data)
        else:
            raise DataError("Invalid request")
    except DBError as e:
        logging.error(f"[drive.helper.helper_rename_file_or_directory] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_rename_file_or_directory] Exception: {e}")
        raise Exception(e)


def helper_update_file_content_make_domain_data(payload: updateFileContentPayload, user_info: dict, server_stage: str) -> updateFileContentDomain:
    try:
        service = "llm-platform" if server_stage != DOCKER else "llm-platform-install"
        return updateFileContentDomain(
            company_key=user_info["company_key"],
            drive_id=payload.file_id,
            target_pages=payload.current_page,
            contents=payload.content,
            service=service,
            vector_db_index=user_info["vector_db_index"],
            vector_db_namespace=user_info["vector_db_namespace"],
            current_time=get_utc_now()
        )
    except DataError as e:
        logging.error(f"[drive.helper.helper_update_file_content_make_domain_data] DataError: {e}")
        raise DataError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_update_file_content_make_domain_data] Exception: {e}")
        raise Exception(e)


async def helper_update_file_content(
    db: AsyncSession,
    s3_client: S3Client,
    vector_db_client: PineconeClient | MilvusClient,
    llm_proxy_client: LLMProxyClient,
    drive_query: DriveQuery,
    vector_query: VectorQuery,
    domain_data: updateFileContentDomain,
) -> None:
    if len(domain_data.target_pages) != len(domain_data.contents):
        raise DataError("Page and content counts must match")

    for page, content in zip(domain_data.target_pages, domain_data.contents):
        chunks = chunking_text(_get_clean_text(markdown(content), False), EMBEDDING_MODEL, 500, 150)
        rows = await drive_query.get_vector_by_drive_id_and_page(db, domain_data.drive_id, page)
        if not rows:
            raise DataError("File page is unavailable")
        bucket, key = rows[0]["s3_path"].split(":", 1)
        key = key.rsplit("/", 1)[0] + f"/pages/{page}.text"
        await s3_client.put_object_to_s3(bucket_name=bucket, object_name=key, file_data=content)

        domain_data.vector_values = []
        for start in range(0, len(chunks), 10):
            domain_data.vector_values.extend(await asyncio.gather(*(
                llm_proxy_client.embeddings(text=chunk, service=domain_data.service)
                for chunk in chunks[start:start + 10]
            )))
        domain_data.vector_metadatas = [{
            "company_key": domain_data.company_key,
            "upload_file_id": rows[0]["upload_file_id"],
            "page": page, "data_type": "parser", "is_show": True,
            "is_on": True, "chunk": index,
        } for index in range(1, len(chunks) + 1)]

        if len(rows) == len(chunks):
            ids = [row["vector_id"] for row in rows]
        else:
            old_ids = [row["vector_id"] for row in rows]
            await vector_db_client.remove(id=[f"parser-{key}" for key in old_ids])
            await vector_query.delete_vector_by_ids(db, old_ids)
            ids = await vector_query.bulk_insert_vector(db, domain_data)
        domain_data.vector_ids = [f"parser-{key}" for key in ids]
        for key, metadata, chunk in zip(ids, domain_data.vector_metadatas, chunks):
            metadata.update(id=key, content=chunk)
        await vector_db_client.insert_many(
            ids=domain_data.vector_ids, values=domain_data.vector_values,
            metadatas=domain_data.vector_metadatas,
        )
        await drive_query.update_drive_row_update_time(db, domain_data)


async def helper_enroll_filesearch_store_make_domain_data(
        db: AsyncSession,
        company_info_query: CompanyInfoQuery,
        payload: EnrollFileSearchStorePayload,
        user_info: dict | None,
        server_stage: str
):
    try:
        # check already has store
        store_name, company_name = await company_info_query.get_store(db, payload.company_key)
        if store_name:
            raise DataError("Can enroll filesearch store which company has not")

        # check has company_key
        is_company_key_in_payload = payload.company_key or False
        is_company_key_in_user_info = isinstance(user_info, dict) and user_info.get("company_key") or False
        is_company_name_in_user_info = isinstance(user_info, dict) and user_info.get("company_name") or False
        if any([is_company_key_in_payload, is_company_key_in_user_info]):
            return EnrollFileSearchStoreDomain(
                server_stage=server_stage,
                company_key=payload.company_key or user_info["company_key"],
                company_name=user_info["company_name"] if is_company_name_in_user_info else company_name,
            )
        else:
            raise DataError("User should input company_key or company_key in user_info")

    except DataError as e:
        logging.error(f"[drive.helper.helper_update_file_content] DataError: {e.message}")
        raise DataError
    except Exception as e:
        logging.error(f"[drive.helper.helper_update_file_content] Exception: {e}")
        raise Exception(e)


async def helper_enroll_filesearch_store_request_create_store(
        llm_proxy_client: LLMProxyClient,
        domain_data: EnrollFileSearchStoreDomain
):
    try:
        service = SERVICE_LLM_PLATFORM_REAL if domain_data.server_stage == REAL else SERVICE_LLM_PLATFORM_STAGING
        display_name = domain_data.company_name if domain_data.server_stage == REAL else domain_data.company_name + "_staging"

        response = await llm_proxy_client.create_store(service=service, display_name=display_name)
        if not isinstance(response, dict):
            raise LLMProxyError("Response Type Error from LLM-PROXY")
        domain_data.store_name = response.get("storeName")

    except LLMProxyError as e:
        logging.error(f"[drive.helper.helper_update_file_content] LLMProxyError: Failed to create store: {e.message}]")
        raise LLMProxyError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_update_file_content] Exception: {e}")
        raise Exception(e)


async def helper_enroll_filesearch_store_update_store_name_in_db(
        db: AsyncSession,
        company_info_query: CompanyInfoQuery,
        domain_data: EnrollFileSearchStoreDomain,
):
    try:
        if domain_data.store_name:
            await company_info_query.update_store_name(db, domain_data)
        else:
            raise DataError("Domain name should not be empty")

    except DataError as e:
        logging.error(f"[drive.helper.helper_update_file_content] DataError: Failed to update file content: {e.message}]")
        raise DataError
    except Exception as e:
        logging.error(f"[drive.helper.helper_update_file_content] Exception: {e}")
        raise Exception(e)



async def helper_delete_update_is_delete_and_is_on(db: AsyncSession, drive_query: DriveQuery, domain_data: deleteDomain):
    try:
        await drive_query.update_is_delete_and_is_on(db, domain_data)
    except DBError as e:
        logging.error(f"[drive.helper.helper_delete_file_update_is_delete_and_is_on] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_delete_file_update_is_delete_and_is_on] Exception: {e}")
        raise Exception(e)


async def helper_delete_update_is_on_of_vector_table(db: AsyncSession, vector_query: VectorQuery, domain_data: deleteDomain):
    try:
        await vector_query.update_is_on_of_vector_table(db, domain_data)
    except DBError as e:
        logging.error(f"[drive.helper.helper_delete_file_update_is_on_of_vector_table] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_delete_file_update_is_on_of_vector_table] Exception: {e}")
        raise Exception(e)


async def helper_delete_get_vector_ids_and_metadatas(db: AsyncSession, vector_query: VectorQuery, domain_data: deleteDomain):
    try:
        vector_results = await vector_query.get_vector_ids_and_metadatas(db, domain_data)
        domain_data.vector_ids = [f"parser-{vector_result['id']}" for vector_result in vector_results]
        domain_data.vector_metadatas = [{
            "company_key": vector_result["company_key"],
            "upload_file_id": vector_result["upload_file_id"],
            "page": vector_result["page"],
            "data_type": vector_result["data_type"],
            "is_on": bool(vector_result["is_on"]),
            "is_show": bool(vector_result["is_show"]),
            "chunk": vector_result["chunk"]
        } for vector_result in vector_results]
    except DBError as e:
        logging.error(f"[drive.helper.helper_delete_file_get_vector_ids_and_metadatas] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_delete_file_get_vector_ids_and_metadatas] Exception: {e}")
        raise Exception(e)


async def helper_delete_update_is_on_in_vector_db(vector_db_client: PineconeClient | MilvusClient, domain_data: deleteDomain):
    try:
        await vector_db_client.update(ids=domain_data.vector_ids, metadatas=domain_data.vector_metadatas)
    except VectorDBError as e:
        logging.error(f"[drive.helper.helper_delete_file_update_is_on_in_vector_db] VectorDBError: {e}")
        raise VectorDBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_delete_file_update_is_on_in_vector_db] Exception: {e}")
        raise Exception(e)


async def helper_delete_file_get_upload_file_id(db: AsyncSession, drive_query: DriveQuery, domain_data: deleteFileDomain):
    try:
        result = await drive_query.get_upload_file_id(db, domain_data)
        domain_data.upload_file_id = result["upload_file_id"]
    except DBError as e:
        logging.error(f"[drive.helper.helper_delete_file_get_upload_file_id] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_delete_file_get_upload_file_id] Exception: {e}")
        raise Exception(e)


async def helper_delete_file_get_vector_ids_and_metadatas(db: AsyncSession, vector_query: VectorQuery, domain_data: deleteFileDomain):
    try:
        domain_data.vector_ids = await vector_query.get_vector_ids_by_upload_file_id(db, domain_data)
        domain_data.vector_ids_target_to_delete_vector_db = [f"parser-{vector_id}" for vector_id in domain_data.vector_ids]
    except DBError as e:
        logging.error(f"[drive.helper.helper_delete_file_get_vector_ids_and_metadatas] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_delete_file_get_vector_ids_and_metadatas] Exception: {e}")
        raise Exception(e)


async def helper_delete_vector_in_vector_db(vector_db_client: PineconeClient | MilvusClient, domain_data: deleteFileDomain):
    try:
        await vector_db_client.remove(id=domain_data.vector_ids_target_to_delete_vector_db)
    except VectorDBError as e:
        logging.error(f"[drive.helper.helper_delete_vector_in_vector_db] VectorDBError: {e}")
        raise VectorDBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_delete_vector_in_vector_db] Exception: {e}")
        raise Exception(e)


async def helper_delete_row_in_vector_table(db: AsyncSession, vector_query: VectorQuery, domain_data: deleteFileDomain):
    try:
        # await vector_query.delete_vector_by_ids(db, domain_data.vector_ids)
        await vector_query.delete_vector_by_upload_file_id(db, domain_data.company_key, domain_data.upload_file_id)
    except DBError as e:
        logging.error(f"[drive.helper.helper_delete_row_in_vector_table] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_delete_row_in_vector_table] Exception: {e}")
        raise Exception(e)


async def helper_delete_row_in_upload_file_table(db: AsyncSession, upload_file_query: UploadFileQuery, domain_data: deleteFileDomain):
    try:
        await upload_file_query.delete_upload_file_history(db, domain_data.upload_file_id)
    except DBError as e:
        logging.error(f"[drive.helper.helper_delete_row_in_upload_file_table] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_delete_row_in_upload_file_table] Exception: {e}")
        raise Exception(e)


async def helper_delete_row_in_drive_table(db: AsyncSession, drive_query: DriveQuery, domain_data: deleteFileDomain):
    try:
        await drive_query.delete_file(db, domain_data)
    except DBError as e:
        logging.error(f"[drive.helper.helper_delete_row_in_drive_table] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_delete_row_in_drive_table] Exception: {e}")
        raise Exception(e)


async def helper_delete_file_in_s3(s3_client: S3Client, domain_data: deleteFileDomain):
    try:
        await s3_client.delete_object(domain_data.s3_bucket_name, domain_data.s3_object_name)
    except AWSError as e:
        logging.error(f"[drive.helper.helper_delete_file_in_s3] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[drive.helper.helper_delete_file_in_s3] Exception: {e}")
        raise Exception(e)

def _get_clean_text(text, keep_html_tags=True, allowed_html_tags=None):
    try:
        # 1. HTML 태그 처리
        soup = BeautifulSoup(text, "html.parser")

        if keep_html_tags:
            if allowed_html_tags is None:
                # 기본적으로 유지할 태그 리스트
                allowed_html_tags = ['p', 'b', 'strong', 'em', 'h1', 'h2', 'h3', 'ul', 'li', 'ol']
            for tag in soup.find_all():
                if tag.name not in allowed_html_tags:
                    tag.unwrap()
                else:
                    # 태그 속성 제거
                    tag.attrs = {}
            text = str(soup)
        else:
            # 모든 태그 제거하고 텍스트만 추출
            text = soup.get_text(separator=' ')

        # 2. 불필요한 공백 제거
        text = ' '.join(text.split())

        return text

    except Exception as e:
        logging.error(f"[drive.helper._get_clean_text] Exception: {e}")
        raise Exception(e)
