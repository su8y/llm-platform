from fastapi import APIRouter, Depends, File

from client.slack import SlackClient
from models import get_db, close_db
from auth.dependencies import get_user_info, get_optional_user
from helper.drive import *
from payload.drive import *
from utils.response import *
from utils.constants import *



router = APIRouter(
    prefix="/drive",
    tags=["drive"],
)


@router.post("/upload_file")
@handle_errors()
async def upload_file(
    payload: uploadFileFormData = Depends(),
    files: list[UploadFile] = File(..., alias="files"),
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # check if user is expired
    if user_info["plan_info_id"] == EXPIRED_PLAN_INFO_ID:
        logging.info(f"[drive.drive.upload_file] Occured ExpiredPlanError. user_id: {user_info['user_id']}, plan_info_id: {user_info['plan_info_id']}")
        raise ExpiredPlanError

    # check server stage
    server_stage = os.getenv("SERVER_STAGE")
    stage = REAL if server_stage == REAL else STAGING if server_stage == STAGING else DEV
    queue_name = os.getenv("PARSER_RABBITMQ_QUEUE_NAME")

    # set infra client
    s3 = S3Client()
    message_broker = RabbitMQClient()
    message_client = SlackClient()
    drive_query = DriveQuery()
    upload_file_query = UploadFileQuery()

    # business logic
    domain_data:uploadFileDomain = helper_upload_file_make_domain_data(payload, user_info, files, stage, queue_name)
    if server_stage == REAL:
        await message_client.send_message(channel="casual", message=f"[llm-platform.fileParser.upload_file start] debug_id: {domain_data.debug_id}, company_name: {domain_data.company_name}, reg_time: {domain_data.reg_date}::UTC")
        await helper_upload_file_upload_for_debug(s3, domain_data)
    await helper_upload_file_check_page_is_over_parser_credit_available(domain_data)
    await helper_upload_file_make_data(domain_data)
    await helper_upload_file_record_drive_in_db(db, drive_query, domain_data)
    helper_upload_file_make_parser_args(domain_data)

    if domain_data.store_name:
        file_credit_query = FileCreditHistoryQuery()
        llm_proxy_client = LLMProxyClient()
        await helper_upload_file_to_s3(s3, domain_data) # import files data(buckets, keys) is in domain_data
        await helper_upload_file_request_import_file_to_llm_proxy(llm_proxy_client, domain_data) # document_name is in domain_data
        await helper_upload_file_update_insert_upload_file_row(db, upload_file_query, drive_query, domain_data)
        await helper_upload_file_decrease_parser_credit_available(db, file_credit_query, domain_data)

    else:
        send = ToParser(
            db=db,
            cloud_storage_client=s3,
            upload_file_query=upload_file_query,
            drive_query=drive_query,
            message_broker_client=message_broker,
            info=domain_data.parser_args,
            init_from="drive"
        )
        await send.activate()
    await helper_upload_file_update_is_show(db, drive_query, domain_data)
    # await close_db(db)
    # if server_stage == REAL:
    #     await helper_upload_file_delete_for_debug(s3, domain_data)

    # make response and return to client
    return Response200().to_orjson()


@router.post("/retry")
@handle_errors()
async def retry(
    payload: retryPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # server stage
    server_stage = os.getenv("SERVER_STAGE", "development")
    queue_name = os.getenv("PARSER_RABBITMQ_QUEUE_NAME")

    # domain data
    domain_data:retryDomain = helper_retry_make_domain_data(payload, user_info, server_stage, queue_name)

    # client
    s3_client = S3Client()
    vector_db_client = PineconeClient(index_name=domain_data.vector_db_index, namespace=domain_data.vector_db_namespace) if server_stage != DOCKER else MilvusClient(collection_name=f"_{domain_data.vector_db_namespace}")
    llm_proxy_client = LLMProxyClient()
    drive_query = DriveQuery()
    upload_file_query = UploadFileQuery()
    message_broker = RabbitMQClient()
    vector_query = VectorQuery()
    company_info_query = CompanyInfoQuery()

    # business logic
    await helper_retry_get_file_info(db, drive_query, domain_data)
    await helper_retry_update_status(db, drive_query, domain_data)
    await helper_retry_module_activate(
        db,
        domain_data, # data
        ToParser, FromParser, # module
        s3_client, vector_db_client, llm_proxy_client, message_broker, # infra
        upload_file_query, drive_query, vector_query, company_info_query # maindb query
    )

    # make response and return to client
    return Response200().to_orjson()


@router.post("/make_directory")
@handle_errors()
async def make_directory(
    payload: makeDirectoryPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # check plan is expired
    if user_info["plan_info_id"] == EXPIRED_PLAN_INFO_ID:
        logging.info(f"[drive.drive.upload_file] Occured ExpiredPlanError. user_id: {user_info['user_id']}, plan_info_id: {user_info['plan_info_id']}")
        raise ExpiredPlanError

    # client
    drive_path_query = DrivePathQuery()

    # business logic
    domain_data:makeDirectoryDomain = helper_make_directory_make_domain_data(payload, user_info)
    domain_data.parent_depth = await drive_path_query.get_parent_dir_depth(db, domain_data)
    await drive_path_query.insert_directory_row_in_drive_path(db=db, domain_data=domain_data)

    # make response and return to client
    return Response200().to_orjson()


# @router.post("/copy_file")
# @handle_errors()
# async def copy_file(
#     payload: copyFilePayload,
#     user_info: dict = Depends(get_user_info),
#     db: AsyncSession = Depends(get_db)
# ):
#     # set client
#     drive_query = DriveQuery()
#     drive_path_query = DrivePathQuery()
#
#     # business logic
#     # TODO: 복사했을 때, s3에 업로드한 파일은 같은걸 바라봐야함. 삭제할 때도 upload_file_id를 같이 쓰는 애가 있는지 파악하고 없을 때만 삭제하도록 해야함. 디렉토리 복사하면 위치 빼고 파일까지 동일하게 들어가야함.
#     drive_table.copy_file(user_info["company_key"], payload.file_id, payload.to_dir_id)
#     drive_path_table.copy_directory(user_info["company_key"], payload.dir_id, payload.to_dir_id)
#
#     # make response and return to client
#     return Response200().to_dict()


@router.post("/credit_charge")
@handle_errors()
async def credit_charge(
        query_params: chargeCreditPayload,
        user_info:dict = Depends(get_user_info),
        db: AsyncSession = Depends(get_db)
):

    charge_credit = query_params.charge_credit
    company_key = user_info["company_key"]

    await helper_charge_credit(db, company_key, charge_credit)

    return Response200(data=True).to_orjson()


@router.get("/get_status")
@handle_errors()
async def get_status(
    query_params: GetStatusQueryParams = Depends(),
    user_info:dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    #TODO: front request this router in loop. consider use REDIS"""

    # set client
    s3_client = S3Client()
    drive_query = DriveQuery()

    # domain_data
    domain_data = GetStatusDomain(
        company_key=user_info["company_key"],
        file_id=query_params.file_id,
        status=query_params.status,
        current_time=get_utc_now()
    )

    # business logic
    await helper_get_status(db, s3_client, drive_query, domain_data)

    # make response and return
    return Response200(data=domain_data.response).to_orjson()


@router.get("/get_page")
@handle_errors()
async def get_page(
    query_params: getPageQueryParams = Depends(),
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # client
    drive_path_query = DrivePathQuery()
    drive_query = DriveQuery()

    # business logic
    domain_data:getPageDomain = helper_get_page_make_domain_data(query_params, user_info)
    await helper_get_page_get_current_dir_datas(db, drive_path_query, domain_data)
    await helper_get_page_get_file_in_current_page(db, drive_query, domain_data)

    # make page data
    helper_get_drive_page_reform_data(domain_data)
    return Response200(data=domain_data.reform_row).to_orjson()


@router.post("/search")
@handle_errors()
async def search(
    payload: searchPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # client
    drive_query = DriveQuery()
    drive_path_query = DrivePathQuery()

    # business logic
    domain_data:searchDomain = helper_search_make_domain_data(payload, user_info)
    await helper_search_files_from_db(db, drive_query, domain_data)
    await helper_search_dir_from_db(db, drive_path_query, domain_data)

    # make response and return to client
    helper_search_reform_data(domain_data)
    return Response200(data=domain_data.reform_row).to_orjson()


@router.get("/get_file_info")
@handle_errors()
async def get_file_info(
    query_params: getFileInfoQueryParams = Depends(),
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # client
    s3_client = S3Client()
    drive_query = DriveQuery()

    # business logic
    domain_data = getFileInfoDomain(
        company_key=user_info["company_key"],
        file_id=query_params.file_id
    )
    domain_data.row = await drive_query.get_file_by_id(db, domain_data)

    # make response and return to client
    await helper_get_file_info_reform_data(s3_client, domain_data)
    return Response200(data=domain_data.reform_row).to_orjson()


@router.get("/file_view")
@handle_errors()
async def file_view(
    query_params: fileViewQueryParams = Depends(),
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # client
    s3_client = S3Client()
    drive_query = DriveQuery()
    vector_query = VectorQuery()

    # business logic
    domain_data = fileViewDomain(
        company_key=user_info["company_key"],
        file_id=query_params.file_id,
        page=query_params.page
    )
    await helper_file_view_get_data_from_db(db, drive_query, vector_query, domain_data)

    # make response and return to client
    await helper_get_file_content_and_all_page(s3_client, domain_data)
    return Response200(data=domain_data.reform_row).to_orjson()


@router.get("/get_filenames")
@handle_errors()
async def get_filenames(
    query_params: GetFilenamesQueryParams = Depends(),
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # client
    drive_query = DriveQuery()

    # business logic
    domain_data = GetFilenamesDomain(
        company_key=user_info["company_key"],
        page=query_params.page,
        per_page=query_params.per_page
    )
    await helper_get_filenames_from_db(db, drive_query, domain_data)

    # make response and return
    return Response200(data=domain_data.row).to_orjson()


@router.get("/download")
@handle_errors()
async def download_file(
    query_params: downloadFileQueryParams = Depends(),
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # client
    s3_client = S3Client()
    upload_file_query = UploadFileQuery()

    # business logic
    domain_data = downloadFileDomain(
        company_key=user_info["company_key"],
        drive_id=query_params.file_id
    )
    await helper_download_get_s3_path_from_db(db, upload_file_query, domain_data)
    await helper_download_get_s3_presigned_url(s3_client, domain_data)

    # URL로 리다이렉트
    return redirect(domain_data.s3_presigned_url)


@router.put("/move_to_directory")
@handle_errors()
async def move_file(
    payload: moveToDirectoryPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # client
    drive_query = DriveQuery()
    drive_path_query = DrivePathQuery()

    # business logic
    domain_data = moveToDirectoryDomain(
        company_key=user_info["company_key"],
        drive_id=payload.file_id,
        drive_path_id=payload.dir_id,
        to_dir_id=payload.to_dir_id
    )
    await helper_move_to_dir(db, drive_query, drive_path_query, domain_data)

    # make response and return to client
    return Response200().to_orjson()


@router.put("/rename")
@handle_errors()
async def rename(
    payload: renamePayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # client
    drive_query = DriveQuery()
    drive_path_query = DrivePathQuery()

    # business logic
    domain_data:renameDomain = helper_rename_make_domain_data(payload, user_info)
    await helper_rename_file_or_directory(db, drive_query, drive_path_query, domain_data)

    # make response and return to client
    return Response200().to_orjson()


@router.put("/update_parser_credit_available")
@handle_errors()
async def update_parser_credit_available(
    payload: updateParserCreditAvailablePayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # check user is admin
    if user_info["is_admin"] != True:
        raise ForbiddenError("You are not allowed to update parser credit available")

    # client
    company_info_query = CompanyInfoQuery()

    # business logic
    domain_data = updateParserCreditAvailableDomain(
        company_key=user_info["company_key"],
        parser_credit_available=payload.parser_credit_available
    )
    await company_info_query.increase_parser_credit_available(db, domain_data)

    # make response and return to client
    return Response200().to_orjson()


@router.put("/update_file_content")
@handle_errors()
async def update_file_content(
    payload: updateFileContentPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # server stage
    server_stage = os.getenv("SERVER_STAGE", "development")
    domain_data:updateFileContentDomain = helper_update_file_content_make_domain_data(payload, user_info, server_stage)

    # client
    s3_client = S3Client()
    vector_db_client = PineconeClient(index_name=domain_data.vector_db_index, namespace=domain_data.vector_db_namespace) if server_stage != DOCKER else MilvusClient(collection_name=f"_{domain_data.vector_db_namespace}")
    llm_proxy_client = LLMProxyClient()
    drive_query = DriveQuery()
    vector_query = VectorQuery()

    # business logic
    await helper_update_file_content(db, s3_client, vector_db_client, llm_proxy_client, drive_query, vector_query, domain_data)

    # make response and return to client
    return Response200().to_orjson()


@router.post("/delete")
@handle_errors()
async def delete(
    payload: deletePayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # server stage
    server_stage = os.getenv("SERVER_STAGE", "development")

    if not payload.file_id and not payload.dir_id:
        raise DataError("fileId or dirId is required")

    # client
    vector_db_client = PineconeClient(index_name=user_info["vector_db_index"], namespace=user_info["vector_db_namespace"]) if server_stage != DOCKER else MilvusClient(collection_name=f"_{user_info['vector_db_namespace']}")
    drive_query = DriveQuery()
    drive_path_query = DrivePathQuery()
    vector_query = VectorQuery()

    # directory: 하위 폴더·파일까지 삭제
    if payload.dir_id:
        deleted = await helper_delete_directory(db, drive_query, drive_path_query, vector_query, vector_db_client, user_info["company_key"], payload.dir_id, user_info["vector_db_index"], user_info["vector_db_namespace"])
        return Response200(data={"deletedFiles": deleted}).to_orjson()

    # domain_data
    domain_data = deleteDomain(
        company_key=user_info["company_key"],
        file_id=payload.file_id,
        vector_db_index=user_info["vector_db_index"],
        vector_db_namespace=user_info["vector_db_namespace"]
    )

    # business logic: check file, directory. is it single or multiple?, is there file in the directory?, is copied file?
    await helper_delete_update_is_delete_and_is_on(db, drive_query, domain_data)
    await helper_delete_update_is_on_of_vector_table(db, vector_query, domain_data)
    await helper_delete_get_vector_ids_and_metadatas(db, vector_query, domain_data)
    await close_db(db)
    await helper_delete_update_is_on_in_vector_db(vector_db_client, domain_data)

    return Response200().to_orjson()


@router.post("/delete_file")
@handle_errors()
async def delete_file(
    payload: deleteFilePayload,
    user_info: dict = Depends(get_user_info),
    # db: AsyncSession = Depends(get_db)
):
    # server stage
    server_stage = os.getenv("SERVER_STAGE", "development")

    # domain_data
    domain_data = deleteFileDomain(
        company_key=user_info["company_key"],
        file_id=payload.file_id,
        vector_db_index=user_info["vector_db_index"],
        vector_db_namespace=user_info["vector_db_namespace"]
    )

    # client
    # s3_client = S3Client()
    vector_db_client = PineconeClient(index_name=domain_data.vector_db_index, namespace=domain_data.vector_db_namespace) if server_stage != DOCKER else MilvusClient(collection_name=domain_data.vector_db_namespace)
    drive_query = DriveQuery()
    vector_query = VectorQuery()
    upload_file_query = UploadFileQuery()

    # business logic
    # TODO: Do Not USE depends. occured lost connection error when operate long time task
    async with get_db() as db:
        await helper_delete_file_get_upload_file_id(db, drive_query, domain_data)
        await helper_delete_file_get_vector_ids_and_metadatas(db, vector_query, domain_data)
    await helper_delete_vector_in_vector_db(vector_db_client, domain_data)
    async with get_db() as db:
        await helper_delete_row_in_vector_table(db, vector_query, domain_data)
        await helper_delete_row_in_upload_file_table(db, upload_file_query, domain_data)
        await helper_delete_row_in_drive_table(db, drive_query, domain_data)
    # await helper_delete_file_in_s3(s3_client, domain_data)

    # make response and return to client
    return Response200().to_orjson()


@router.post("/enroll_filesearch_store")
@handle_errors()
async def enroll_filesearch_store(
        payload: EnrollFileSearchStorePayload,
        user_info: dict = Depends(get_optional_user),
        db: AsyncSession = Depends(get_db),
):
    """
    1. LLM-Proxy로 Google.Gemini.FileSearch API Store 생성 요청
    2. Store 이름을 받아 main_db에 company_info table에 저장
    3. store_name이 있는 회사 계정만 FileSearch API 사용 가능
    """

    # server stage
    server_stage = os.getenv("SERVER_STAGE", "development")
    if server_stage == DOCKER: # 폐쇄망 설치(docker)는 외부 Google FileSearch API를 쓰지 않는다
        return Response400(message="FileSearch store is not available on docker(on-premise) stage").to_orjson()

    # client
    llm_proxy_client = LLMProxyClient()
    company_info_query = CompanyInfoQuery()

    # domain_data
    domain_data = await helper_enroll_filesearch_store_make_domain_data(db, company_info_query, payload, user_info, server_stage)

    # business logic
    await helper_enroll_filesearch_store_request_create_store(llm_proxy_client, domain_data)
    await helper_enroll_filesearch_store_update_store_name_in_db(db, company_info_query, domain_data)

    # make response and return
    return Response200().to_orjson()


@router.post("/callback_from_parser")
async def callback_from_parser(
    payload: callbackFromParserPayload,
    db: AsyncSession = Depends(get_db)
):
    try:
        logging.info(f"[api.drive.drive.callback_from_parser.payload] success to receive callback from parser")
        logging.info(f"[api.drive.drive.callback_from_parser.payload] payload: {payload}")

        # server stage
        server_stage = os.getenv("SERVER_STAGE", "development")

        # set infra client
        s3_client = S3Client()
        vector_db_client = PineconeClient(index_name=payload.vector_db_index, namespace=payload.vector_db_namespace) if server_stage != DOCKER else MilvusClient(collection_name=f"_{payload.vector_db_namespace}")
        llm_proxy_client = LLMProxyClient()
        vector_query = VectorQuery()
        drive_query = DriveQuery()
        company_info_query = CompanyInfoQuery()
        file_credit_query = FileCreditHistoryQuery()

        # business logic
        result = await FromParser(
            db=db,
            s3_client=s3_client,
            vector_db_client=vector_db_client,
            llm_proxy_client=llm_proxy_client,
            vector_query=vector_query,
            drive_query=drive_query,
            company_info_query=company_info_query,
            file_credit_query=file_credit_query,
            info=payload,
            server_stage=server_stage
        ).activate()

        # make response and return to client
        return Response200(data=result).to_dict()

    # for next tasks, return response_200
    except AWSError as e:
        logging.info(f"[api.drive.drive.callback_from_parser.payload] AWSError: {e}")
        return Response200(message=e.message).to_orjson()
    except DBError as e:
        logging.info(f"[api.drive.drive.callback_from_parser.payload] DBError: {e}")
        return Response200(message=e.message).to_orjson()
    except VectorDBError as e:
        logging.info(f"[api.drive.drive.callback_from_parser.payload] VectorDBError: {e}")
        return Response200(message=e.message).to_orjson()
    except Exception as e:
        logging.info(f"[api.drive.drive.callback_from_parser.payload] Exception: {e}")
        return Response200().to_orjson()
