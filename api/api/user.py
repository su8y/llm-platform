from fastapi import APIRouter
from jose import jwt, ExpiredSignatureError, JWTError

from auth.dependencies import *
from auth import SECRET_KEY, ALGORITHM
from client.milvus import MilvusClient
from models import get_db
from helper.user import *
from domain.user import *
from payload.user import *



router = APIRouter(
    prefix="/user",
    tags=["user"],
)



@router.post("/register")
@handle_errors()
async def register(
    payload: UserRegisterPayload,
    db: AsyncSession = Depends(get_db)
):
    # check server stage
    server_stage = os.getenv("SERVER_STAGE", "development")
    domain_data:registerDomain = helper_register_make_domain_data(payload, server_stage)

    # set client
    if domain_data.server_stage == DOCKER:
        vector_db_client = MilvusClient(collection_name=f"_{domain_data.vector_db_namespace}")
    else:
        vector_db_client = PineconeClient(index_name=domain_data.vector_db_index)
    llm_proxy_client = LLMProxyClient()
    user_info_query = UserInfoQuery()
    company_info_query = CompanyInfoQuery()
    invite_history_query = InviteHistoryQuery()
    drive_path_query = DrivePathQuery()

    # business logic
    await helper_register_check_exists_info(db, user_info_query, domain_data) # if already exists, raise error
    if not domain_data.is_slave: # Master User
        await helper_register_init_company_to_db(db, company_info_query, domain_data)
        await helper_register_init_user_to_db(db, user_info_query, domain_data)
        await helper_register_make_vector_space(vector_db_client, domain_data)
        if domain_data.server_stage != DOCKER: # 폐쇄망 설치(docker)는 Google FileSearch 스토어를 만들지 않는다
            await helper_register_make_file_search_store(db, llm_proxy_client, company_info_query, domain_data)
        await helper_register_make_drive_home_path(db, drive_path_query, domain_data)
        if domain_data.server_stage != DOCKER:
            await send_certification_email_by_dream_mailer(domain_data)
    else: # Slave User by Invite
        await helper_register_check_and_get_user_row_by_auth_key(db, invite_history_query, domain_data)
        await helper_register_init_user_to_db(db, user_info_query, domain_data)
        if domain_data.server_stage != DOCKER:
            await send_certification_email_by_dream_mailer(domain_data)

    # make response and return
    return Response200().to_dict()


@router.get("/get_register_info")
@handle_errors()
async def get_register_info(
    query_params: getRegisterInfoQueryParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # get data from query string
    if not query_params.invitation_key:
        raise DataError("There is not InvitationKey")

    # set client
    invite_history_query = InviteHistoryQuery()

    # business logic
    domain_data = getRegisterInfoDomain(invitation_key=query_params.invitation_key)
    row = await invite_history_query.get_slave_info(db, domain_data)

    # make response and return
    data = {
        "companyName": row["company_name"],
        "emailAddress": row["email_address_invite"],
        "lang": row["lang"]
    } if row else None
    return Response200(data=data).to_dict() if data else Response404().to_dict()


@router.get("/certificate")
@handle_errors()
async def certificate(
    query_params: certificateQueryParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # get data from query string
    decode_certification_key = helper_certificate_decode_args(query_params.certification) # -> dict

    # set client
    user_info_query = UserInfoQuery()
    invite_history_query = InviteHistoryQuery()

    # business logic
    domain_data = certificateDomain(
        user_id=decode_certification_key["id"],
        company_key=decode_certification_key["companyKey"],
        lang=decode_certification_key["lang"]
    )
    await helper_certificate_check_user_info(db, user_info_query, domain_data)
    await helper_certificate_certificate_state(db, user_info_query, invite_history_query, domain_data)

    # make url and redirect
    make_certification_front_url(domain_data)
    return redirect(url=domain_data.redirect_url)


@router.post("/login")
@handle_errors()
async def login(
    payload: UserLoginPayload,
    db: AsyncSession = Depends(get_db)
):
    # server stage
    server_stage = os.getenv("SERVER_STAGE", "development")

    # set client
    user_info_query = UserInfoQuery()
    company_info_query = CompanyInfoQuery()
    payment_query = PaymentQuery()
    credit_history_query = CreditHistoryQuery()

    # business logic
    domain_data = helper_login_make_domain_data(payload, server_stage)
    await helper_login_check(db, user_info_query, company_info_query, payment_query, credit_history_query, domain_data) # if fail, raise Error
    helper_login_make_response_data(domain_data)

    # make response and return
    data = {
        "accessToken": domain_data.access_token,
        "refreshToken": domain_data.refresh_token
    }
    return Response200(data=data).to_dict()


@router.post("/refresh_token")
@handle_errors()
async def refresh_token(
    payload: UserRefreshTokenPayload
):
    try:
        # validate refresh token
        if not payload.refresh_token:
            raise TokenError("Refresh token is required")

        # decode and verify refresh token
        token_payload = jwt.decode(payload.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        # check if token type is refresh
        if token_payload.get("type") != "refresh":
            raise TokenError("Invalid token type")

        # get identity from token
        token_identity = token_payload.get("sub")
        if not token_identity:
            raise TokenError("Invalid token")

        # parse and regenerate tokens
        identity = helper_refresh_parse_token(token_identity)
        data = helper_refresh_make_token_data(identity)

        # make response and return
        return Response200(data=data).to_dict()

    except ExpiredSignatureError as e:
        logging.info(f"[api.user.refresh_token] ExpiredSignatureError: {e}")
        raise TokenError("Refresh token has expired")
    except JWTError as e:
        logging.info(f"[api.user.refresh_token] JWTError: {e}")
        raise TokenError("Invalid refresh token")
    except TokenError as e:
        logging.info(f"[api.user.refresh_token] TokenError: {e.message}")
        raise e
    except Exception as e:
        logging.info(f"[api.user.refresh_token] Exception: {e}")
        raise TokenError("Failed to refresh token")


@router.get("/get_info")
@handle_errors()
async def get_info(
    user_info:dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # set client
    user_info_query = UserInfoQuery()

    # business logic
    domain_data = getInfoDomain(user_id=user_info['user_id'])
    domain_data.row = await user_info_query.get_user_info(db, domain_data)

    # make response and return
    helper_reform_user_info(domain_data)
    return Response200(data=domain_data.reform_row).to_dict()


@router.post("/find_password")
@handle_errors()
async def find_password(
    payload: UserFindPasswordPayload,
    db: AsyncSession = Depends(get_db)
):
    # server stage
    server_stage = os.getenv("SERVER_STAGE", "development")

    # domain_data
    domain_data = findPasswordDomain(
        user_id=payload.user_id,
        lang=payload.lang,
        server_stage=server_stage
    )

    # set client
    user_info_query = UserInfoQuery()
    password_reset_history_query = PasswordResetHistoryQuery()

    # business logic
    await helper_find_password_check_user_id(db, user_info_query, domain_data)
    helper_find_password_make_find_key(domain_data)
    helper_find_password_make_redirect_url(domain_data)
    await send_find_password_send_mail_by_dream_mailer(domain_data)
    await helper_find_password_insert_find_key_and_expire_date(db, password_reset_history_query, domain_data)

    # make response and return
    helper_find_password_mask_email_address(domain_data)
    return Response200(data={"emailAddress": domain_data.email_address}).to_dict()


@router.get("/check_validation_find_password")
@handle_errors()
async def check_validation_find_password(
    query_params: checkValidationFindPasswordQueryParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    domain_data: checkValidationFindPasswordDomain = helper_check_validation_find_password_make_domain_data(query_params)

    # set client
    password_reset_history_query = PasswordResetHistoryQuery()

    # business logic
    await helper_check_validation_find_password_check_find_key_and_expire_date(db, password_reset_history_query, domain_data)

    # make response and return
    helper_check_validation_find_password_make_redirect_url(domain_data)
    return redirect(url=domain_data.redirect_url)


@router.post("/change_password")
@handle_errors()
async def change_password(
    payload: UserChangePasswordPayload,
    db: AsyncSession = Depends(get_db)
):
    domain_data: changePasswordDomain = helper_reset_password_make_domain_data(payload)

    # set client
    user_info_query = UserInfoQuery()
    password_reset_history_query = PasswordResetHistoryQuery()

    # business logic
    helper_reset_password_check_validation_password(domain_data)
    await helper_reset_password_update_hashed_password(db, user_info_query, domain_data)
    await helper_reset_password_update_exp_date(db, password_reset_history_query, domain_data)

    # make response and return
    return Response200().to_dict()
