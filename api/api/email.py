from urllib.parse import quote, unquote

from fastapi import APIRouter, Depends, File
from fastapi.responses import StreamingResponse

from models import get_db, close_db
from auth.dependencies import get_user_info
from helper.email import *
from helper.prompt import *
from helper.mail_setting import *
from payload.mail_setting import *
from queries.mail_receive_setting import MailReceiveSettingQuery
from queries.mail_smtp_setting import MailSmtpSettingQuery
from client.smtp import SMTPClient
from module.MailReceiver.runner import MailReceiverRunner
from payload.email import *
from domain.email import *
from domain.prompt import *
from queries.cx_email_references import CXEmailReferencesQuery
from queries.cx_email_temp import CXEmailTempQuery
from utils.error import *
from utils.date import get_utc_now

from module.Mail.activate import RunLLMEmail



router = APIRouter(
    prefix="/email",
    tags=["email"],
)



@router.post("/inbox_list")
@handle_errors()
async def inbox_list(
    payload: InboxListPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # domain_data
    domain_data:InboxListDomain = helper_inbox_list_make_domain_data(payload, user_info)

    # set client
    cx_email_query = CXEmailQuery()

    # business logic
    await helper_inbox_list_get_rows_and_count(db, cx_email_query, domain_data)

    # make response and return!
    helper_inbox_list_reform_row(domain_data)
    return Response200(data={"rows": domain_data.reform_rows, "count": domain_data.count}).to_dict()


@router.post("/insert_prompt")
@handle_errors()
async def insert_prompt(
        payload:insertPromptPayload,
        user_info:dict = Depends(get_user_info),
        db:AsyncSession = Depends(get_db)
):
    # client
    prompt_history_query = MailPromptHistoryQuery()

    # business logic
    domain_data:insertPromptDomain = helper_insert_prompt_make_domain_data(payload, user_info)
    data = await helper_insert_prompt(db, prompt_history_query, domain_data)

    # make response and return
    return Response200(data=data).to_dict()


@router.get("/get_prompt_version")
@handle_errors()
async def get_prompt_version(
        user_info:dict = Depends(get_user_info),
        db:AsyncSession = Depends(get_db)
):
    # client
    prompt_history_query = MailPromptHistoryQuery()

    # business logic
    domain_data = getVersionDomain(company_key=user_info['company_key'])
    data = await prompt_history_query.get_prompt_version(db, domain_data)

    # make response and return
    return Response200(data=data).to_dict()


@router.post("/get_prompt")
@handle_errors()
async def get_prompt(
        payload:getPromptPayload,
        user_info:dict = Depends(get_user_info),
        db:AsyncSession = Depends(get_db)
):
    # client
    prompt_history_query = MailPromptHistoryQuery()

    # business logic
    domain_data = getPromptDomain(company_key=user_info['company_key'], prompt_id=payload.prompt_id)
    data = await prompt_history_query.get_prompt(db, domain_data)

    # make response and return
    return Response200(data=data).to_dict()


@router.post("/get_inbox")
@handle_errors()
async def get_inbox(
    payload: getInboxPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # domain_data
    domain_data = GetInboxDomain(
        id=payload.id,
        company_key=user_info["company_key"]
    )

    # set client
    cx_email_query = CXEmailQuery()

    # business logic
    await helper_get_inbox_get_row(db, cx_email_query, domain_data)

    # make response and return!
    helper_get_inbox_reform_row(domain_data)
    if domain_data.reform_row.get("thread"):
        s3_client = S3Client()
        await helper_get_inbox_download_s3_file(s3_client, domain_data)
    return Response200(data={"row": domain_data.reform_row}).to_dict()


@router.post("/update_company")
@handle_errors()
async def update_company(
    payload: UpdateCompanyPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # domain_data
    domain_data = UpdateCompanyDomain(
        id=payload.id,
        company_key=user_info["company_key"],
        company=payload.company
    )

    # infra side
    cx_email_query = CXEmailQuery()

    # business side
    await helper_update_company(db, cx_email_query, domain_data)

    # return response
    return Response200().to_dict()


@router.post("/get_inbox_history")
@handle_errors()
async def get_inbox_history(
    payload: GetInboxHistoryPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # domain_data
    domain_data = GetInboxHistoryDomain(
        id=payload.id,
        company_key=user_info["company_key"]
    )

    # set client
    cx_email_history_query = CXEmailHistoryQuery()

    # business logic
    await helper_get_inbox_history(db, cx_email_history_query, domain_data)

    # response
    return Response200(data=domain_data.response).to_dict()


@router.get("/get_manager_list")
@handle_errors()
async def get_manager_list(
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # domain_data
    domain_data = GetManagerListDomain(
        company_key=user_info["company_key"]
    )

    # set client
    user_info_query = UserInfoQuery()

    # business logic
    await helper_get_manager_list(db, user_info_query, domain_data)

    # response
    return Response200(data=domain_data.response).to_dict()


@router.post("/set_manager")
@handle_errors()
async def set_manager(
    payload: SetManagerPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # domain_data
    domain_data = SetManagerDomain(
        id=payload.id,
        company_key=user_info["company_key"],
        user_id=user_info["user_id"],
        manager_id=payload.manager_id,
        action_code=EMAIL_HISTORY_SET_MANAGER,
        current_time=get_utc_now(),
    )

    # set client
    cx_email_query = CXEmailQuery()
    cx_email_history_query = CXEmailHistoryQuery()

    # business logic
    await helper_set_manager(db, cx_email_query, domain_data)
    await helper_record_history(db, cx_email_history_query, domain_data)

    # response
    return Response200().to_dict()


@router.get("/get_status")
@handle_errors()
async def get_status(
    query_params: GetStatusQueryParams = Depends(),
    user_info: dict = Depends(get_user_info)
):
    if not query_params.id and not query_params.current_status:
        raise DBError("You should give info email id or current status")

    if query_params.current_status:
        response = {
            EMAIL_PENDING: True,
            EMAIL_ANSWERING: True,
            EMAIL_SENT: True,
            EMAIL_CLOSED: True,
            EMAIL_SPAM: True
        }
    else:
        response = {
            EMAIL_PENDING: True,
            EMAIL_ANSWERING: True,
            EMAIL_SENT: True,
            EMAIL_CLOSED: True,
            EMAIL_SPAM: True
        }
    return Response200(data=response).to_dict()


@router.post("/change_status")
@handle_errors()
async def change_status(
    payload: ChangeStatusPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # domain_data
    domain_data = ChangeStatusDomain(
        id = payload.id,
        user_id = user_info["user_id"],
        company_key = user_info["company_key"],
        status = payload.status,
        current_time = get_utc_now()
    )

    # infra side
    cx_email_query = CXEmailQuery()
    cx_email_history_query = CXEmailHistoryQuery()

    # biz side
    helper_change_status_make_action_code(domain_data)
    await helper_check_and_enroll_manager(db, cx_email_query, domain_data)
    await helper_change_status_change_status(db, cx_email_query, domain_data)
    await helper_record_history(db, cx_email_history_query, domain_data)

    # response
    return Response200().to_dict()


@router.post("/update_receive_comment")
@handle_errors()
async def update_receive_comment(
    payload: UpdateReceiveCommentPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # domain_data
    domain_data = UpdateReceiveCommentDomain(
        id = payload.id,
        user_id = user_info["user_id"],
        company_key = user_info["company_key"],
        comment = payload.comment,
        current_time=get_utc_now(),
        action_code=EMAIL_HISTORY_EDIT_TO_UPDATE_RECEIVED_COMMENT
    )

    # infra client
    cx_email_query = CXEmailQuery()
    cx_email_history_query = CXEmailHistoryQuery()

    # business logic
    await helper_update_receive_comment(db, cx_email_query, domain_data)
    await helper_record_history(db, cx_email_history_query, domain_data)

    # response
    return Response200().to_dict()


@router.get("/indox_file_download/{s3Key:path}")
@handle_errors()
async def indox_file_download(s3Key: str):
    s3_client = S3Client()
    s3_key = unquote(s3Key)
    filename = s3_key.split('/')[-1]

    streaming_generator, content_type, content_length = await helper_inbox_file_streaming(s3_client, s3_key)

    return StreamingResponse(
        streaming_generator,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename.encode('utf-8'))}",
            "Content-Length": str(content_length)
        }
    )


@router.post("/init_answer")
@handle_errors()
async def init_answer(
    payload: InitAnswerPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db),
):
    # domain_data
    domain_data = InitAnswerDomain(
        id = payload.id,
        user_id = user_info["user_id"],
        company_key = user_info["company_key"],
        current_time = get_utc_now()
    )

    # set client
    cx_email_temp_query = CXEmailTempQuery()

    # business logic
    await helper_init_answer_check_has_row(db, cx_email_temp_query, domain_data)
    if not domain_data.has_row:
        company_info_query = CompanyInfoQuery()
        cx_email_query = CXEmailQuery()
        await helper_get_to_address(db, company_info_query, domain_data)
        await helper_init_answer_get_all_info(db, cx_email_query, domain_data)
        await helper_init_answer_insert_answer_temp_row(db, cx_email_temp_query, domain_data)
        await helper_init_answer_update_has_temp_to_true(db, cx_email_query, domain_data)

    # response
    return Response200().to_dict()


@router.post("/get_send_info")
@handle_errors()
async def get_send_info(
        payload: GetSendInfoPayload,
        user_info: dict = Depends(get_user_info),
        db: AsyncSession = Depends(get_db),
):
    # domain_data
    domain_data = GetSendInfoDomain(
        cx_email_id = payload.id,
        company_key = user_info["company_key"]
    )

    # infra client
    cx_email_temp_query = CXEmailTempQuery()

    # business side
    await helper_get_send_info(db, cx_email_temp_query, domain_data)

    # response
    return Response200(data=domain_data.response).to_dict()


@router.post("/create_answer")
@handle_errors()
async def create_answer(
    payload: CreateAnswerPayload,
    user_info: dict = Depends(get_user_info)
):
    # server stage
    server_stage = os.getenv("SERVER_STAGE")

    # domain_data
    domain_data:CreateEmailContentDomain = helper_create_answer_make_domain_data(payload, user_info, server_stage)

    # set client
    domain_data.s3_client = S3Client()
    domain_data.llm_proxy_client = LLMProxyClient()
    domain_data.vector_db_client = PineconeClient(
        index_name=domain_data.vector_db_index,
        namespace=domain_data.vector_db_namespace
    ) if server_stage != DOCKER else MilvusClient(collection_name=domain_data.vector_db_namespace)
    domain_data.main_db_client = MySQLClient()

    logging.info(f"==================== START Analysis service: {domain_data.service}")
    logging.info(f"==================== START Analysis vendor: {domain_data.vendor}")
    logging.info(f"==================== START Analysis model: {domain_data.model}")
    logging.info(f"==================== START Analysis vector_db_index: {domain_data.vector_db_index}")
    logging.info(f"==================== START Analysis vector_db_namespace: {domain_data.vector_db_namespace}")

    # business logic
    # await helper_create_answer_check_status(domain_data)
    answer = str()
    async for chunk in RunLLMEmail(args=domain_data).activate():
        answer += chunk

    # make response and return!
    return Response200(data={"answer": answer, "status": EMAIL_ANSWERING}).to_dict()


@router.post("/save_send_info")
@handle_errors()
async def save_send_info(
    payload: SaveSendInfoPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db),
):
    # domain_data
    domain_data: SaveSendInfoDomain = helper_save_send_info_make_domain_data(payload, user_info)

    # infra side
    s3_client = S3Client()
    company_info_query = CompanyInfoQuery()
    cx_email_temp_query = CXEmailTempQuery()
    cx_email_history_query = CXEmailHistoryQuery()

    # business side
    await helper_get_to_address(db, company_info_query, domain_data)
    await helper_save_send_info_check_diff_attach_and_delete(db, cx_email_temp_query, s3_client, domain_data)
    await helper_save_send_info_update_row(db, cx_email_temp_query, domain_data)
    await helper_record_history(db, cx_email_history_query, domain_data)

    # make and return response
    return Response200().to_dict()


@router.post("/save_send_info_upload_attach")
@handle_errors()
async def save_send_info_upload_attach(
    attachments: Optional[list[UploadFile]] = File(default=None, alias="files"),
    user_info: dict = Depends(get_user_info),
):
    # domain_data
    domain_data = SaveAttachDomain(
        attachments = attachments,
        company_key = user_info["company_key"]
    )

    # infra side
    s3_client = S3Client()

    # business logic
    await helper_save_send_info_upload_attach(s3_client, domain_data)

    # make and return response
    return Response200(data=domain_data.response).to_dict()


@router.post("/check_has_thread")
@handle_errors()
async def check_has_thread(
    payload: CheckHasThreadPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):

    # domain_data
    domain_data = CheckHasThreadDomain(
        id = payload.id
    )

    # infra side
    cx_email_query = CXEmailQuery()

    # business logic
    await helper_check_has_thread_get_first_message_id_and_references(db, cx_email_query, domain_data)
    helper_check_has_thread(domain_data)
    await helper_check_hash_thread_get_sent_row(db, cx_email_query, domain_data)
    helper_check_has_sent_thread(domain_data)

    # response
    return Response200().to_dict()


@router.post("/send_email")
@handle_errors()
async def send_email(
    payload: SendEmailPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db),
):
    # server stage
    server_stage = os.getenv("SERVER_STAGE")

    # domain_data
    domain_data:SendEmailDomain = helper_send_email_make_domain_data(payload, user_info, server_stage)

    # set client
    s3_client = S3Client()
    ses_client = SESClient()
    llm_proxy_client = LLMProxyClient()
    cx_email_query = CXEmailQuery()
    cx_email_history_query = CXEmailHistoryQuery()
    cx_email_references_query = CXEmailReferencesQuery()
    email_send_history_query = EmailSendHistoryQuery()
    smtp_setting_query = MailSmtpSettingQuery()
    smtp_client = SMTPClient()
    vector_query = VectorQuery()
    if server_stage != DOCKER:
        vector_db_client = PineconeClient(index_name=domain_data.vector_db_index, namespace=domain_data.vector_db_namespace)
    else:
        vector_db_client = MilvusClient(collection_name=f"_{domain_data.vector_db_namespace}")

    # business logic
    logging.info(f"[api.email.send_email] cx_email_id:{domain_data.id} is start to send email.")
    await helper_send_email_get_data_from_cx_email(db, cx_email_query, domain_data)
    await helper_send_email_get_cid_and_image(db, s3_client, cx_email_query, domain_data)
    await helper_send_email_download_attachments(s3_client, domain_data)
    await helper_send_email_insert_answer_row(db, email_send_history_query, domain_data)
    await helper_send_email_load_smtp_setting(db, smtp_setting_query, domain_data)
    if domain_data.smtp_config:
        await helper_send_email_send_mail_by_smtp_setting(smtp_client, domain_data)   # 회사 SMTP 설정 (설치형)
    else:
        try:
            await helper_send_email_send_mail_by_ses(ses_client, domain_data)
        except:
            logging.error(f"Fail to send email by AWS SES. cx_email_id is {domain_data.id}")
            raise AWSError

    await helper_record_history(db, cx_email_history_query, domain_data)
    await helper_send_email_update_cx_email_status(db, cx_email_query, domain_data)
    await helper_send_email_upload_html_to_s3(s3_client, domain_data)
    await helper_send_email_update_email_send_history_row(db, email_send_history_query, domain_data)
    await helper_send_email_insert_refereces_row(db, cx_email_references_query, domain_data)

    await helper_send_email_check_is_vector_content_over_token(domain_data)
    if not domain_data.is_over_token: # email html이 50,000이 넘으면 vector에 저장 X
        await helper_send_email_chunking_thread(llm_proxy_client, domain_data)
        await helper_send_email_insert_answer_vector_row(db, vector_query, domain_data)
        await helper_send_email_insert_question_and_answer_to_vector_db(vector_db_client, domain_data)
    await close_db(db)

    return Response200().to_dict()


@router.post("/delete_sent_email")
@handle_errors()
async def delete_sent_email(
    payload: DeleteSentEmailPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db),
):
    # make domain_data
    domain_data = DeleteSentEmailDomain(
        email_send_history_id=payload.id,
        company_key=user_info["company_key"],
        vector_db_index=user_info["vector_db_index"],
        vector_db_namespace=user_info["vector_db_namespace"],
        server_stage = os.getenv("SERVER_STAGE"),
        is_soft_deletion=True
    )

    # set client
    if domain_data.server_stage != DOCKER:
        vector_db_client = PineconeClient(index_name=domain_data.vector_db_index, namespace=domain_data.vector_db_namespace)
    else:
        vector_db_client = MilvusClient(collection_name=f"_{domain_data.vector_db_namespace}")
    email_send_history_query = EmailSendHistoryQuery()
    vector_query = VectorQuery()

    # business logic
    if domain_data.is_soft_deletion:
        await helper_delete_sent_email_getting_chunk_metadatas(db, vector_query, domain_data)
        await helper_delete_sent_email_updating_data_in_vector_db(vector_db_client, domain_data)
        await helper_delete_sent_email_updating_row_in_main_db(db, vector_query, email_send_history_query, domain_data)
    else:
        await helper_delete_sent_email_getting_chunk(db, vector_query, domain_data)
        await helper_delete_sent_email_deleting_data_in_vector_db(vector_db_client, domain_data)
        await helper_delete_sent_email_deleting_row_in_main_db(db, vector_query, email_send_history_query, domain_data)

    # make response and return
    return Response200().to_dict()


@router.post("/get_ses_bounce")
async def get_ses_bounce(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # parse request.body
    body = await request.body()

    # make domain_data
    domain_data:GetSESBounceDomain = helper_get_ses_bounce_make_domain_data(body)

    # business logic
    if domain_data.is_bounce:
        email_send_history_query = EmailSendHistoryQuery()
        await helper_get_ses_bounce_update_bounce(db, email_send_history_query, domain_data)

    # return response
    return {"status":"ok"}


# @router.post("/send_email_smtp")
# @handle_errors()
# async def send_email_smtp(
#     payload: SendEmailFormData = Depends(),
#     attachments: Optional[list[UploadFile]] = File(default=None, alias="files"),
#     user_info: dict = Depends(get_user_info),
#     db: AsyncSession = Depends(get_db)
# ):
#     # server stage
#     server_stage = os.getenv("SERVER_STAGE")
#
#     # domain_data
#     domain_data:SendEmailDomain = helper_send_email_make_domain_data(payload, user_info, server_stage, attachments)
#
#     # set client
#     s3_client = S3Client()
#     smtp_client = SMTPClient()
#     llm_proxy_client = LLMProxyClient()
#     cx_email_query = CXEmailQuery()
#     cx_email_history_query = CXEmailHistoryQuery()
#     email_rag_query = EmailSendHistoryQuery()
#     vector_query = VectorQuery()
#     if server_stage != DOCKER:
#         vector_db_client = PineconeClient(
#             index_name=domain_data.vector_db_index,
#             namespace=domain_data.vector_db_namespace
#         )
#     else:
#         vector_db_client = MilvusClient(collection_name=f"_{domain_data.vector_db_namespace}")
#
#     # business logic
#     await helper_send_email_send_mail_by_smtp(smtp_client, domain_data)
#     await helper_record_history(db, cx_email_history_query, domain_data)
#     await helper_send_email_update_status(db, cx_email_query, domain_data)
#     await helper_send_email_upload_html_to_s3(s3_client, domain_data)
#     await helper_send_email_insert_answer_row(db, email_rag_query, domain_data)
#     await helper_send_email_chunking_thread(llm_proxy_client, domain_data)
#     await helper_send_email_insert_answer_vector_row(db, vector_query, domain_data)
#     await close_db(db)
#     await helper_send_email_insert_question_and_answer_to_vector_db(vector_db_client, domain_data)
#
#     return Response200().to_dict()


@router.post("/upload_base64_image")
@handle_errors()
async def upload_base64_image(
    payload:UploadBase64Payload,
    user_info:dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # domain_data
    domain_data = UploadBase64Domain(
        company_key=user_info["company_key"],
        image=payload.image,
        current_date=get_utc_now()
    )

    # set client
    s3_client = S3Client()
    email_cid_images_query = EmailCIDImagesQuery()

    # business logic
    await helper_upload_base64_image_to_s3(s3_client, domain_data)
    await helper_upload_base64_insert_row_in_email_cid_images(db, email_cid_images_query, domain_data)

    # make response and return
    return ORJSONResponse(content=domain_data.response)


@router.post("/get_dashboard_chart")
@handle_errors()
async def get_dashboard_chart(
    payload: GetDashboardChartPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # domain_data
    domain_data:GetDashboardChartDomain = helper_get_dashboard_chart_make_domain_data(
        payload, user_info
    )

    # set client
    cx_email_query = CXEmailQuery()

    # business logic
    await helper_get_dashboard_chart_get_data_from_db(db, cx_email_query, domain_data) # rows

    # make response and return
    helper_get_dashboard_chart_make_response(domain_data)
    return Response200(data=domain_data.response).to_dict()


@router.post("/get_dashboard_line")
@handle_errors()
async def get_dashboard_line(
    payload: GetDashboardLinePayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # domain_data
    domain_data:GetDashboardLineDomain = helper_get_dashboard_line_make_domain_data(
        payload, user_info
    )

    # set client
    cx_email_query = CXEmailQuery()
    email_send_histroy_query = EmailSendHistoryQuery()

    # business logic
    await helper_get_dashboard_line_get_data_from_db(db, cx_email_query, email_send_histroy_query, domain_data) # rows

    # make response and return
    helper_get_dashboard_line_make_response(domain_data)
    return Response200(data=domain_data.response).to_dict()


@router.post("/get_dashboard_manager_count")
@handle_errors()
async def get_dashboard_manager_count(
        payload: GetDashboardManagerCntPayload,
        user_info: dict = Depends(get_user_info),
        db: AsyncSession = Depends(get_db)
):
    # domain_data
    domain_data:GetDashboardManagerCntDomain = helper_get_dashboard_manager_count_make_domain_data(
        payload, user_info
    )

    # set client
    cx_email_query = CXEmailQuery()

    # business logic
    await helper_get_dashboard_manager_count_get_data_from_db(db, cx_email_query, domain_data) # rows

    # make response and return
    helper_get_dashboard_manager_count_make_response(domain_data)
    return Response200(data=domain_data.response).to_dict()


# ---------- 메일 수신 설정 (IMAP / SES) : master 전용 ----------

@router.get("/setting/list")
@handle_errors()
async def get_mail_settings(
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    helper_mail_setting_check_master(user_info)

    # set client
    setting_query = MailReceiveSettingQuery()

    # business logic
    rows = await setting_query.list_by_company(db, user_info["company_key"])

    # make response and return
    return Response200(data=[helper_mail_setting_make_public(row) for row in rows]).to_dict()


@router.post("/setting/test")
@handle_errors()
async def test_mail_setting(
    payload: testMailSettingPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    helper_mail_setting_check_master(user_info)

    # set client
    setting_query = MailReceiveSettingQuery()

    # business logic
    domain_data = helper_mail_setting_make_domain_data(payload, user_info)
    await helper_mail_setting_merge_secrets(db, setting_query, domain_data)
    await helper_mail_setting_test_connection(domain_data)

    # make response and return
    return Response200(data=domain_data.test_result).to_dict()


@router.post("/setting/upsert")
@handle_errors()
async def upsert_mail_setting(
    payload: upsertMailSettingPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    helper_mail_setting_check_master(user_info)

    # set client
    setting_query = MailReceiveSettingQuery()

    # business logic
    domain_data = helper_mail_setting_make_domain_data(payload, user_info)
    await helper_mail_setting_merge_secrets(db, setting_query, domain_data)
    await helper_mail_setting_upsert(db, setting_query, domain_data)

    # make response and return
    return Response200(data=helper_mail_setting_make_public(domain_data.existing_row)).to_dict()


@router.post("/setting/delete")
@handle_errors()
async def delete_mail_setting(
    payload: deleteMailSettingPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    helper_mail_setting_check_master(user_info)

    # set client
    setting_query = MailReceiveSettingQuery()

    # business logic
    await helper_mail_setting_delete(db, setting_query, user_info, payload)

    # make response and return
    return Response200().to_dict()


@router.post("/setting/run_now")
@handle_errors()
async def run_mail_receive_now(
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    helper_mail_setting_check_master(user_info)

    # business logic
    received = await MailReceiverRunner.run_once(company_key=user_info["company_key"])

    # make response and return
    return Response200(data={"received": received}).to_dict()


# ---------- SMTP 발신 설정 : master 전용 ----------

@router.get("/setting/smtp/get")
@handle_errors()
async def get_smtp_setting(
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    helper_mail_setting_check_master(user_info)

    # set client
    smtp_setting_query = MailSmtpSettingQuery()

    # business logic
    row = await smtp_setting_query.get_by_company(db, user_info["company_key"])

    # make response and return
    return Response200(data=helper_smtp_setting_make_public(row)).to_dict()


@router.post("/setting/smtp/test")
@handle_errors()
async def test_smtp_setting(
    payload: testSmtpSettingPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    helper_mail_setting_check_master(user_info)

    # set client
    smtp_setting_query = MailSmtpSettingQuery()

    # business logic
    domain_data = helper_smtp_setting_make_domain_data(payload, user_info)
    await helper_smtp_setting_merge_secrets(db, smtp_setting_query, domain_data)
    await helper_smtp_setting_test_connection(db, smtp_setting_query, domain_data)

    # make response and return
    return Response200(data=domain_data.test_result).to_dict()


@router.post("/setting/smtp/upsert")
@handle_errors()
async def upsert_smtp_setting(
    payload: upsertSmtpSettingPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    helper_mail_setting_check_master(user_info)

    # set client
    smtp_setting_query = MailSmtpSettingQuery()

    # business logic
    domain_data = helper_smtp_setting_make_domain_data(payload, user_info)
    await helper_smtp_setting_merge_secrets(db, smtp_setting_query, domain_data)
    await helper_smtp_setting_upsert(db, smtp_setting_query, domain_data)

    # make response and return
    return Response200(data=helper_smtp_setting_make_public(domain_data.existing_row)).to_dict()


@router.post("/setting/smtp/delete")
@handle_errors()
async def delete_smtp_setting(
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    helper_mail_setting_check_master(user_info)

    # set client
    smtp_setting_query = MailSmtpSettingQuery()

    # business logic
    await smtp_setting_query.delete(db, user_info["company_key"])

    # make response and return
    return Response200().to_dict()
