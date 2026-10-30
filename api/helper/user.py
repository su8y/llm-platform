import os
import re
import ast
import base64
from datetime import timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import parse_qsl
from werkzeug.security import generate_password_hash, check_password_hash

from client.pinecone import PineconeClient
from client.milvus import MilvusClient
from client.groxy import LLMProxyClient
from queries.user_info import UserInfoQuery
from queries.company_info import CompanyInfoQuery
from queries.invite_history import InviteHistoryQuery
from queries.payment import PaymentQuery
from queries.credit_history import CreditHistoryQuery
from queries.drive_path import DrivePathQuery
from queries.password_reset_history import PasswordResetHistoryQuery
from payload.user import *
from domain.user import *
from auth.jwt import create_token
from utils.constants import *
from utils.error import *
from utils.date import *
from utils.mail import send_mail_by_dream_mailer, send_find_password_mail_by_dream_mailer



def helper_register_make_domain_data(payload:UserRegisterPayload, server_stage:str):
    try:
        hashed_password = generate_password_hash(payload.user_password, method="pbkdf2:sha256")
        reg_date = get_utc_now()
        expired_date = get_first_hour_of_day(get_after_years(get_after_months(reg_date, 1), 1), "UTC")
        is_slave = True if payload.invitation_key else False
        user_auth = VIEWER if payload.invitation_key else MASTER
        company_key = str(uuid4()).replace("-", "") if not is_slave else None
        vector_db_namespace = str(uuid4()).replace("-", "")
        is_admin = True

        if server_stage != DOCKER:
            plan_info_id = None
            credit_available = 0
            parser_credit_available = 0
            vector_db_index = REAL_INDEX if server_stage == REAL else STAGING_INDEX
            certifi = False
        else:
            plan_info_id = 1
            credit_available = 0
            parser_credit_available = 0
            vector_db_index = REAL_INDEX
            certifi = True

        return registerDomain(
            user_id=payload.user_id,
            company_name=payload.company_name,
            hashed_password=hashed_password,
            email_address=payload.email_address,
            department=payload.department,
            reg_date=reg_date,
            expired_date=expired_date,
            lang=payload.lang,
            phone=payload.phone_number,
            invitation_key=payload.invitation_key,
            is_slave=is_slave,
            user_auth=user_auth,
            server_stage=server_stage,
            plan_info_id=plan_info_id,
            credit_available=credit_available,
            parser_credit_available=parser_credit_available,
            vector_db_index=vector_db_index,
            vector_db_namespace=vector_db_namespace,
            certifi=certifi,
            is_admin=is_admin,
            company_key=company_key
        )
    except DataError as e:
        logging.error(f"[helper.user.helper_register_make_domain_data] DataError: {e}")
        raise DataError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_register_make_domain_data] Exception: {e}")
        raise e


async def helper_register_check_exists_info(db:AsyncSession, user_info_query:UserInfoQuery, domain_data:registerDomain) -> None:
    try:
        user_info_result = await user_info_query.get_user_info_by_user_id(db=db, domain_data=domain_data)
        if user_info_result and domain_data.user_id == user_info_result.get("user_id"):
            raise AlreadyExistsIDError
        email_result = await user_info_query.get_user_email_by_email(db=db, domain_data=domain_data)
        if email_result and domain_data.email_address == email_result.get("email_address"):
            raise AlreadyExistsEmailError

    except AlreadyExistsIDError as e:
        logging.error(f"[helper.user.helper_register_check_exists_info] AlreadyExistsIDError: {e}")
        raise AlreadyExistsIDError(e)
    except AlreadyExistsEmailError as e:
        logging.error(f"[helper.user.helper_register_check_exists_info] AlreadyExistsEmailError: {e}")
        raise AlreadyExistsEmailError(e)
    except DBError as e:
        logging.error(f"[helper.user.helper_register_check_exists_info] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_register_check_exists_info] ExceptionError: {e}")
        raise e


async def helper_register_init_company_to_db(db:AsyncSession, company_info_query:CompanyInfoQuery, domain_data:registerDomain):
    try:
        # insert company info
        result = await company_info_query.get_info_by_company_name(db=db, domain_data=domain_data)
        if result and domain_data.company_name == result.get("company_name"):
            raise AlreadyExistsCompanyNameError()

        init_row = await company_info_query.register(
            db=db,
            domain_data=domain_data
        )
        domain_data.company_key = init_row["company_key"]

    except AlreadyExistsCompanyNameError as e:
        logging.error(f"[helper.user.helper_register_init_company] AlreadyExistsCompanyNameError: {e}")
        raise AlreadyExistsCompanyNameError(e)
    except DBError as e:
        logging.error(f"[helper.user.helper_register_init_company] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_register_init_company] Exception: {e}")
        raise e


async def helper_register_init_user_to_db(db:AsyncSession, user_info_query:UserInfoQuery, domain_data:registerDomain):
    try:
        # insert master user info
        await user_info_query.register(
            db=db,
            domain_data=domain_data
        )
    except DBError as e:
        logging.error(f"[helper.user.helper_register_init_user] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_register_init_user] Exception: {e}")
        raise e


async def helper_register_make_vector_space(
    vector_db_client: PineconeClient | MilvusClient, domain_data: registerDomain,
) -> None:
    if domain_data.server_stage == DOCKER:
        await vector_db_client.check_connection()
        return
    index_list = [index["name"] for index in await vector_db_client.get_index_list()]
    if domain_data.vector_db_index not in index_list:
        await vector_db_client.create_index()


async def helper_register_make_file_search_store(
        db:AsyncSession,
        llm_proxy_client: LLMProxyClient,
        company_info_query: CompanyInfoQuery,
        domain_data:registerDomain
):
    try:
        service = SERVICE_LLM_PLATFORM_REAL if domain_data.server_stage == REAL else SERVICE_LLM_PLATFORM_STAGING
        display_name = domain_data.company_name if domain_data.server_stage == REAL else domain_data.company_name + "_staging"

        response = await llm_proxy_client.create_store(service=service, display_name=display_name)
        if not isinstance(response, dict):
            raise LLMProxyError("Response Type Error from LLM-PROXY")
        domain_data.store_name = response.get("storeName")

        if domain_data.store_name:
            await company_info_query.update_store_name(db, domain_data)

    except LLMProxyError as e:
        logging.error(f"[helper.user.helper_register_make_file_search_store] LLMProxyError: {e}")
        raise LLMProxyError(e)
    except DBError as e:
        logging.error(f"[helper.user.helper_register_make_file_search_store] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_register_make_file_search_store] Exception: {e}")
        raise Exception(e)





    except LLMProxyError as e:
        logging.error(f"[helper.user.helper_register_make_file_search_store] LLMProxyError: {e}")



async def helper_register_make_drive_home_path(db:AsyncSession, drive_path_query:DrivePathQuery, domain_data:registerDomain):
    try:
        await drive_path_query.create_drive_path(
            db=db,
            domain_data=domain_data
        )
    except DBError as e:
        logging.error(f"[helper.user.helper_register_make_drive_home_path] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_register_make_drive_home_path] Exception: {e}")
        raise e


async def helper_register_check_and_get_user_row_by_auth_key(db:AsyncSession, invite_history_query:InviteHistoryQuery, domain_data:registerDomain):
    try:
        result = await invite_history_query.get_register_info_by_auth_key(db=db, domain_data=domain_data)
        domain_data.company_key = result["company_key"]
        domain_data.invite_history_id = result["invite_history_id"]
    except DBError as e:
        logging.error(f"[helper.user.helper_register_check_and_get_user_row_by_auth_key] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_register_check_and_get_user_row_by_auth_key] Exception: {e}")
        raise e


def helper_certificate_decode_args(certification:str):
    certifi_info_dict = _decode_certification_url(certification)
    return certifi_info_dict


def _decode_certification_url(args) -> dict:
    decode_base64_to_query = base64.urlsafe_b64decode(args).decode()
    decode_query_to_dict = dict(parse_qsl(decode_base64_to_query.lstrip("?")))
    return decode_query_to_dict


async def helper_certificate_check_user_info(db:AsyncSession, user_info_query:UserInfoQuery, domain_data:certificateDomain):
    try:
        domain_data.user_info_row = await user_info_query.get_user(db=db, domain_data=domain_data)
        if not domain_data.user_info_row or domain_data.company_key != domain_data.user_info_row['company_key']:
            raise ForbiddenError("No user row or companyKey is not matched")

        domain_data.invite_history_id = domain_data.user_info_row["invite_history_id"]

    except DBError as e:
        logging.error(f"[helper.user.helper_certificate_check_user_info] DBError: {e}")
        raise DBError(e)
    except ForbiddenError as e:
        logging.error(f"[helper.user.helper_certificate_check_user_info] ForbiddenError: {e}")
        raise ForbiddenError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_certificate_check_user_info] Exception: {e}")
        raise e


async def helper_certificate_certificate_state(db:AsyncSession, user_info_query:UserInfoQuery, invite_history_query:InviteHistoryQuery, domain_data:certificateDomain):
    try:
        await user_info_query.certificate(db=db, user_id=domain_data.user_id)
        await invite_history_query.update_data_by_id(
            db=db,
            domain_data=domain_data
        )
        domain_data.success = True
    except DBError as e:
        logging.error(f"[helper.user.helper_certificate_certificate_state] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_certificate_certificate_state] Exception: {e}")
        raise e


def helper_login_make_domain_data(payload:UserLoginPayload, server_stage:str):
    try:
        return loginDomain(
            user_id=payload.user_id,
            user_password=payload.user_password,
            server_stage=server_stage,
            reg_date=get_utc_now()
        )

    except Exception as e:
        logging.error(f"[helper.user.helper_login_make_domain_data] Exception: {e}")
        raise e


async def helper_login_check(
    db:AsyncSession,
    user_info_query:UserInfoQuery,
    company_info_query:CompanyInfoQuery,
    payment_query:PaymentQuery,
    credit_history_query:CreditHistoryQuery,
    domain_data:loginDomain
):
    try:
        user_info_row = await user_info_query.get_user(db=db, domain_data=domain_data)

        is_user = True if user_info_row else False
        if not is_user:
            raise NotFoundUserError

        hashed_password_from_db = user_info_row.get("user_password")
        is_password = check_password_hash(hashed_password_from_db, domain_data.user_password)
        if not is_password:
            raise NotFoundPasswordError

        is_certifi = user_info_row.get("certifi")
        if not is_certifi:
            raise NotCertifiError

        is_master_first_login = user_info_row.get("user_auth") == MASTER and user_info_row.get("plan_info_id") is None and domain_data.server_stage != DOCKER
        if is_master_first_login: # if master user and first login, create trial payment row
            domain_data.company_key = user_info_row.get("company_key")
            domain_data.plan_info_id = INIT_PLAN_ID
            domain_data.init_plan = _create_trial_payment_row(user_info_row)
            domain_data.expired_date = domain_data.init_plan[-1]["end_date"] + timedelta(microseconds=1)
            domain_data.first_payment_id = await payment_query.insert_plan_payment(db, domain_data)
            domain_data.credit_type = True
            domain_data.credit = 60

            await company_info_query.adapt_plan(db, domain_data)
            await credit_history_query.insert_credit_history(db=db, domain_data=domain_data)

    except NotFoundUserError as e:
        logging.error(f"[helper.user.helper_login_check] NotFoundUserError: {e}")
        raise NotFoundUserError(e)
    except NotFoundPasswordError as e:
        logging.error(f"[helper.user.helper_login_check] NotFoundPasswordError: {e}")
        raise NotFoundPasswordError(e)
    except NotCertifiError as e:
        logging.error(f"[helper.user.helper_login_check] NotCertifiError: {e}")
        raise NotCertifiError(e)
    except DataError as e:
        logging.error(f"[helper.user.helper_login_check] DataError: {e}")
        raise DataError(e)
    except DBError as e:
        logging.error(f"[helper.user.helper_login_check] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_login_check] Exception: {e}")
        raise e


def _create_trial_payment_row(data, period=None, local_timezone=None):
    try:
        current_date = get_utc_now()
        start_date, end_date = get_init_plan_date(start_date=current_date, period=period, local_timezone=local_timezone)
        next_start_date, next_end_date = get_next_plan_date(before_end_date=end_date, period="year", local_timezone=local_timezone)

        # 플랜 데이터 생성
        result = [
            {
                "company_key": data["company_key"],
                "plan_info_id": INIT_PLAN_ID,
                "payment_history_id": None,
                "start_date": start_date,
                "end_date": end_date,
                "payment_date": None,
                "payment_period": None,
                "reg_date": current_date,
                "use_credit": 0,
                "payment_status": "complete",
                "change_type": "system",
                "is_target_renewal": 0,
                "attempt_count": 0,
            },
            {
                "company_key": data["company_key"],
                "plan_info_id": EXPIRED_PLAN_INFO_ID,
                "payment_history_id": None,
                "start_date": next_start_date,
                "end_date": next_end_date,
                "payment_date": None,
                "payment_period": None,
                "reg_date": current_date,
                "use_credit": None,
                "payment_status": "waiting",
                "change_type": "system",
                "is_target_renewal": 0,
                "attempt_count": 0,
            }
        ]

        return tuple(result)
    except Exception as e:
        logging.error(f"[helper.user._create_trial_payment_row] Exception: {e}")
        raise e


def helper_login_make_response_data(domain_data:loginDomain):
    try:
        session_key = str(uuid4()).replace("-", "")
        identity = str({'session_key':session_key, 'user_id': domain_data.user_id})
        domain_data.access_token, domain_data.refresh_token = create_token(identity)

    except Exception as e:
        logging.error(f"[helper.user.helper_login_make_response_data] Exception: {e}")
        raise e


def helper_refresh_parse_token(token_identity:str):
    try:
        token_identity_dict = ast.literal_eval(token_identity)
        identity = str({
            'session_key':token_identity_dict['session_key'],
            'user_id': token_identity_dict['user_id']
        })
        return identity

    except Exception as e:
        logging.error(f"[helper.user.helper_refresh_parse_token] Exception: {e}")
        raise e


def helper_refresh_make_token_data(identity:str):
    access_token, refresh_token = create_token(identity)
    data = {"accessToken": access_token, "refreshToken": refresh_token}
    return data


def helper_reform_user_info(domain_data:getInfoDomain):
    domain_data.reform_row = domain_data.row
    domain_data.reform_row["userAuth"]["authEmailUse"] = True if domain_data.reform_row["emailAvailable"] else False
    domain_data.reform_row["userAuth"]["authEmailView"] = True if domain_data.reform_row["emailAvailable"] else False


async def helper_find_password_check_user_id(db:AsyncSession, user_info_query:UserInfoQuery, domain_data:findPasswordDomain):
    try:
        user_info_row = await user_info_query.get_user_info_for_find_password(db=db, domain_data=domain_data)
        if not user_info_row:
            raise NotFoundUserError
        else:
            domain_data.company_name = user_info_row["company_name"]
            domain_data.email_address = user_info_row["email_address"]
    except NotFoundUserError as e:
        logging.error(f"[helper.user.helper_find_password_check_user_id] NotFoundUserError: {e}")
        raise NotFoundUserError(e)
    except DBError as e:
        logging.error(f"[helper.user.helper_find_password_check_user_id] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_find_password_check_user_id] Exception: {e}")
        raise e


def helper_find_password_make_find_key(domain_data:findPasswordDomain):
    try:
        domain_data.find_key = str(uuid4()).replace("-", "")
    except Exception as e:
        logging.error(f"[helper.user.helper_find_password_make_find_key] Exception: {e}")
        raise e


def helper_find_password_make_redirect_url(domain_data:findPasswordDomain):
    try:
        base_url = REAL_API_URL if domain_data.server_stage == REAL else STAGING_API_URL if domain_data.server_stage == STAGING else DEV_API_URL
        path = 'user/check_validation_find_password'
        query = f"?user_id={domain_data.user_id}&find_key={domain_data.find_key}"
        encode_base64 = base64.urlsafe_b64encode(query.encode()).decode()
        domain_data.redirect_url = base_url + path + "?acceptance=" + encode_base64
    except Exception as e:
        logging.error(f"[helper.user.helper_find_password_make_redirect_url] Exception: {e}")
        raise e


async def send_find_password_send_mail_by_dream_mailer(domain_data:findPasswordDomain):
    try:
        message = {
            "lang": domain_data.lang,
            "expireDate": datetime_to_string(datetime_obj=domain_data.current_date + timedelta(days=1), datetime_format="%Y-%m-%d %H:%M", timezone_str="Asia/Tokyo" if domain_data.lang == "ja" else "Asia/Seoul"),
            "companyName": domain_data.company_name,
            "masterId": domain_data.user_id,
            "userId": domain_data.email_address,
            "query": domain_data.redirect_url
        }
        await send_find_password_mail_by_dream_mailer(
            template_name=FIND_PASSWORD_EMAIL_TEMPLATE_NAME,
            data=message,
            service_code=EMAIL_SERVICE_CODE
        )

    except Exception as e:
        logging.error(f"[helper.user.send_find_password_send_mail_by_dream_mailer] Exception: {e}")
        raise e


async def helper_find_password_insert_find_key_and_expire_date(db:AsyncSession, password_reset_history_query:PasswordResetHistoryQuery, domain_data:findPasswordDomain):
    try:
        await password_reset_history_query.update_is_newest_false(db=db, domain_data=domain_data)
        await password_reset_history_query.insert_row(db=db, domain_data=domain_data)
    except DBError as e:
        logging.error(f"[helper.user.helper_find_password_update_find_key_and_expire_date] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_find_password_update_find_key_and_expire_date] Exception: {e}")
        raise e


def helper_find_password_mask_email_address(domain_data:findPasswordDomain):
    try:
        if not domain_data.email_address or not isinstance(domain_data.email_address, str):
            raise ValueError("email_address is not valid")

        split_email_address = domain_data.email_address.split("@")
        email_address = split_email_address[0]
        email_address_first_letter = email_address[0]
        email_address_last_letter = email_address[-1]
        email_vendor = split_email_address[1].split(".")[0]
        email_vendor_first_letter = email_vendor[0]
        email_vendor_last_letter = email_vendor[-1]
        email_domain = split_email_address[1].split(".")[1:]
        if len(email_address) > 2:
            mask_email_address = email_address_first_letter + "*" * (len(email_address) - 2) + email_address_last_letter
        else:
            mask_email_address = email_address_first_letter + "*"
        if len(email_vendor) > 2:
            mask_email_vendor = email_vendor_first_letter + "*" * (len(email_vendor) - 2) + email_vendor_last_letter
        else:
            mask_email_vendor = email_vendor_first_letter + "*"
        domain_data.email_address = mask_email_address + "@" + mask_email_vendor + "." + ".".join(email_domain)

    except ValueError as e:
        logging.error(f"[helper.user.helper_find_password_mask_email_address] ValueError: {e}")
        raise DataError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_find_password_mask_email_address] Exception: {e}")
        raise e


def helper_check_validation_find_password_make_domain_data(query_params:checkValidationFindPasswordQueryParams):
    try:
        decode_base64 = base64.urlsafe_b64decode(query_params.acceptance).decode()
        query_params_dict = dict(parse_qsl(decode_base64.lstrip("?")))
        return checkValidationFindPasswordDomain(
            query_base64=query_params.acceptance,
            find_key=query_params_dict.get("find_key"),
            user_id=query_params_dict.get("user_id"),
            server_stage=os.getenv("SERVER_STAGE")
        )
    except Exception as e:
        logging.error(f"[helper.user.helper_check_validation_find_password_make_domain_data] DataError: {e}")
        raise DataError("Invalid acceptance parameter") from e


async def helper_check_validation_find_password_check_find_key_and_expire_date(db:AsyncSession, password_reset_history_query:PasswordResetHistoryQuery, domain_data:checkValidationFindPasswordDomain):
    try:
        user_info_row = await password_reset_history_query.get_find_key_by_user_id(db=db, domain_data=domain_data)
        if not user_info_row:
            error_message = "There is not Data in Database"
            logging.info(f"[helper.user.helper_check_validation_find_password_check_find_key_and_expire_date] {error_message}")
            raise NotValidatedFindPasswordError(error_message)
        if user_info_row.get("user_id") != domain_data.user_id:
            error_message = "user_id is not matched"
            logging.info(f"[helper.user.helper_check_validation_find_password_check_find_key_and_expire_date] {error_message}")
            raise NotValidatedFindPasswordError(error_message)
        if user_info_row.get("find_key") != domain_data.find_key:
            error_message = "find_key is not matched"
            logging.info(f"[helper.user.helper_check_validation_find_password_check_find_key_and_expire_date] {error_message}")
            raise NotValidatedFindPasswordError(error_message)
        if user_info_row.get("find_key_exp_date").replace(tzinfo=timezone.utc) < domain_data.current_date:
            error_message = "find_key is expired"
            logging.info(f"[helper.user.helper_check_validation_find_password_check_find_key_and_expire_date] {error_message}")
            raise NotValidatedFindPasswordError(error_message)
        domain_data.newest_row_id = user_info_row["id"]

    except NotValidatedFindPasswordError as e:
        logging.error(f"[helper.user.helper_check_validation_find_password_check_find_key_and_expire_date] NotValidatedFindPasswordError: {e}")
        raise NotValidatedFindPasswordError(e)
    except DataError as e:
        logging.error(f"[helper.user.helper_check_validation_find_password_check_find_key_and_expire_date] DataError: {e}")
        raise DataError(e)
    except DBError as e:
        logging.error(f"[helper.user.helper_check_validation_find_password_check_find_key_and_expire_date] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_check_validation_find_password_check_find_key_and_expire_date] Exception: {e}")
        raise e


def helper_check_validation_find_password_make_redirect_url(domain_data:checkValidationFindPasswordDomain):
    try:
        base_url = REAL_URL if domain_data.server_stage == REAL else STAGING_URL if domain_data.server_stage == STAGING else DEV_URL
        # path = "login"
        domain_data.redirect_url = base_url + "signin?changePassword=true&acceptance=" + domain_data.query_base64

    except Exception as e:
        logging.error(f"[helper.user.helper_check_validation_find_password_make_redirect_url] Exception: {e}")
        raise e


def helper_reset_password_make_domain_data(payload:UserChangePasswordPayload):
    try:
        decode_base64 = base64.urlsafe_b64decode(payload.acceptance).decode()
        query_params_dict = dict(parse_qsl(decode_base64.lstrip("?")))

        user_id = query_params_dict.get("user_id")
        find_key = query_params_dict.get("find_key")
        if not find_key or not user_id:
            error_message = "find_key or user_id is not valid"
            logging.info(f"[helper.user.helper_reset_password_make_domain_data] {error_message}")
            raise DataError(error_message)

        return changePasswordDomain(
            user_id=user_id,
            user_password=payload.user_password,
            hashed_password=generate_password_hash(payload.user_password, method="pbkdf2:sha256"),
            find_key=find_key
        )

    except DataError as e:
        logging.error(f"[helper.user.helper_reset_password_make_domain_data] DataError: {e}")
        raise DataError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_reset_password_make_domain_data] Exception: {e}")
        raise e


def helper_reset_password_check_validation_password(domain_data:changePasswordDomain):
    try:
        if len(domain_data.user_password) < 6 or len(domain_data.user_password) > 20:
            raise DataError("password length is not valid")

        if ' ' in domain_data.user_password:
            raise DataError("password is not valid")

        pattern = r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>/?`~]+$'

        if not re.match(pattern, domain_data.user_password):
            raise DataError("password is not valid")

    except DataError as e:
        logging.error(f"[helper.user.helper_reset_password_check_validation_password] DataError: {e}")
        raise DataError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_reset_password_check_validation_password] Exception: {e}")
        raise e


async def helper_reset_password_update_hashed_password(db:AsyncSession, user_info_query:UserInfoQuery, domain_data:changePasswordDomain):
    try:
        await user_info_query.update_password(db=db, domain_data=domain_data)
    except DBError as e:
        logging.error(f"[helper.user.helper_reset_password_update_hashed_password] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_reset_password_update_hashed_password] Exception: {e}")
        raise e


async def helper_reset_password_update_exp_date(db:AsyncSession, password_reset_history_query:PasswordResetHistoryQuery, domain_data:changePasswordDomain):
    try:
        await password_reset_history_query.update_expire_date_by_id(db=db, domain_data=domain_data)
    except DBError as e:
        logging.error(f"[helper.user.helper_check_validation_find_password_update_exp_date] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.user.helper_check_validation_find_password_update_exp_date] Exception: {e}")
        raise e


# =======================
# not business logic. etc
# =======================


async def send_certification_email_by_dream_mailer(domain_data:registerDomain):
    message = {
        "lang": domain_data.lang,
        "masterId": domain_data.user_id,
        "userId": domain_data.email_address,
        "companyName": domain_data.company_name,
        "query": make_certification_url(
            id=domain_data.user_id,
            company_key=domain_data.company_key,
            lang=domain_data.lang
        )
    }
    result = await send_mail_by_dream_mailer(
        template_name=CERTIFICATION_EMAIL_TEMPLATE_NAME,
        data=message,
        service_code=EMAIL_SERVICE_CODE
    )
    return result


def make_certification_url(id:str, company_key:str, lang:str) -> str:
    base_url = REAL_API_URL if os.getenv("SERVER_STAGE") == REAL else STAGING_API_URL if os.getenv("SERVER_STAGE") == STAGING else DEV_API_URL
    path = "user/certificate"
    query = f"?companyKey={company_key}&id={id}&lang={lang}"
    encode_base64 = base64.urlsafe_b64encode(query.encode()).decode()
    return base_url + path + "?certification=" + encode_base64


def make_certification_front_url(domain_data:certificateDomain) -> str:
    base_url = REAL_URL if os.getenv("SERVER_STAGE") == REAL else STAGING_URL if os.getenv("SERVER_STAGE") == STAGING else DEV_URL
    query = f"signin?certification={domain_data.success}&lang={domain_data.lang}"
    domain_data.redirect_url = base_url + query
