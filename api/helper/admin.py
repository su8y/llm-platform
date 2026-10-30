import os
import re
from uuid import uuid4
import base64
from urllib.parse import parse_qsl

from sqlalchemy.ext.asyncio import AsyncSession

from queries.invite_history import InviteHistoryQuery
from queries.user_auth import UserAuthQuery
from queries.user_info import UserInfoQuery
from queries.company_info import CompanyInfoQuery
from payload.admin import *
from domain.admin import *
from utils.constants import *
from utils.date import *
from utils.error import *
from utils.mail import *
from utils.response import *



def helper_get_member_making_domain_data(payload:getMembersPayload, user_info:dict):
    try:
        # set default value
        company_key = user_info["company_key"]
        page = int(payload.page)
        per_page = int(payload.per_page)
        local_timezone = payload.local_timezone
        current_time = get_utc_now()

        # parse filter params
        filter_params = {
            'status': payload.status,
            'userId': payload.user_id,
            'department': payload.department,
            'emailAddress': payload.email_address,
            'authName': payload.auth_name
        }

        # parse filter params
        for key, value in filter_params.items():
            if value in ['', 'all'] or (value is not None and len(value) == 0):
                filter_params[key] = None

        # TODO: make function to make query datetime by payload
        # parse date params
        start_date = payload.start_date
        end_date = payload.end_date
        start_date_datetime_local = string_to_datetime(start_date, local_timezone) if start_date else None
        end_date_datetime_local = get_last_hour_of_day(end_date, local_timezone) if end_date else None
        start_date_datetime_utc = change_utc_datetime(start_date_datetime_local) if start_date_datetime_local else None
        end_date_datetime_utc = change_utc_datetime(end_date_datetime_local) if end_date_datetime_local else None

        # make filters
        filters = {"company_key": company_key}
        
        if filter_params['userId']:
            filters['user_id'] = filter_params['userId']
        if filter_params['department']:
            filters['department'] = filter_params['department']
        if filter_params['authName']:
            filters['auth_name'] = filter_params['authName']
        if filter_params['emailAddress']:
            filters['email_address_invite'] = filter_params['emailAddress']
        
        # parse status filter
        status_mapping = {
            "complete": {"accept": True},
            "false": {"success": False},
            "expired": {"expired_now": current_time},
            "waiting": {"waiting_now": current_time}
        }
        
        if filter_params['status'] in status_mapping:
            filters.update(status_mapping[filter_params['status']])

        return getMembersDomain(
            company_key=company_key,
            page=page,
            per_page=per_page,
            start_date=start_date_datetime_utc,
            end_date=end_date_datetime_utc,
            filters=filters
        )
    except Exception as e:
        logging.error(f"[helper.admin.helper_get_member_making_domain_data] Exception: {e}")
        raise DataError(e)


async def helper_get_member_from_db(db:AsyncSession, invite_history_query:InviteHistoryQuery, domain_data:getMembersDomain):
    try:
        result = await invite_history_query.get_members_with_count(db, domain_data)
        domain_data.row = result.get("rows")
        domain_data.count = result.get("count")
    except DBError as dbe:
        logging.error(f"[helper.admin.helper_get_member_from_db] DBError: {dbe}")
        raise DBError(dbe)
    except Exception as e:
        logging.error(f"[helper.admin.helper_get_member_from_db] Exception: {e}")
        raise Exception(e)


def helper_get_members_reform(domain_data:getMembersDomain):
    try:
        if domain_data.count == 0 and domain_data.row == []:
            domain_data.reform_row = []
        else:
            domain_data.reform_row = [_check_status_and_make_data(row) for row in domain_data.row]
    except Exception as e:
        logging.error(f"[helper.admin.helper_get_members_reform] Exception: {e}")
        raise Exception(e)


def helper_change_auth_making_domain_data(payload:changeAuthPayload, user_info:dict):
    try:
        return changeAuthDomain(
            user_id=payload.user_id,
            auth_name=payload.auth_name,
            company_key=user_info["company_key"]
        )
    except Exception as e:
        logging.error(f"[helper.admin.helper_change_auth_making_domain_data] Exception: {e}")
        raise Exception(e)


async def helper_change_auth_get_auth_name(db:AsyncSession, user_auth_query:UserAuthQuery, domain_data:changeAuthDomain):
    try:
        domain_data.user_auth = await user_auth_query.get_user_auth_by_auth_name(db, domain_data)
        if not domain_data.user_auth:
            raise DataError("User auth not found")
    except DBError as dbe:
        logging.error(f"[helper.admin.helper_change_auth_get_auth_name] DBError: {dbe}")
        raise DBError(dbe)
    except DataError as de:
        logging.error(f"[helper.admin.helper_change_auth_get_auth_name] DataError: {de}")
        raise DataError(de)
    except Exception as e:
        logging.error(f"[helper.admin.helper_change_auth_get_auth_name] Exception: {e}")
        raise Exception(e)
    

async def helper_change_auth_from_db(db:AsyncSession, user_info_query:UserInfoQuery, domain_data:changeAuthDomain):
    try:
        await user_info_query.update_auth(db, domain_data)
    except DBError as dbe:
        logging.error(f"[helper.admin.helper_change_auth_from_db] DBError: {dbe}")
        raise DBError(dbe)
    except Exception as e:
        logging.error(f"[helper.admin.helper_change_auth_from_db] Exception: {e}")
        raise Exception(e)


def helper_invite_member_making_domain_data(payload:inviteMemberPayload, user_info:dict):
    try:
        return inviteMemberDomain(
            company_key=user_info["company_key"],
            user_id=user_info["user_id"],
            lang=payload.lang,
            email_addresses_list=payload.email_address.replace(" ", "").split(","),
            local_timezone=payload.local_timezone,
            invite_date=get_utc_now()
        )
    except Exception as e:
        logging.error(f"[helper.admin.helper_invite_member_making_domain_data] Exception: {e}")
        raise Exception(e)


async def helper_invite_member_checking_already_email_address(db:AsyncSession, invite_history_query:InviteHistoryQuery, domain_data:inviteMemberDomain):
    try:
        not_able_send_email_check_set = await invite_history_query.get_invite_email_set(db, domain_data)
        p = re.compile('^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        for email_address in domain_data.email_addresses_list:
            if not p.match(email_address):
                raise WrongEmailTypeError
            if email_address in not_able_send_email_check_set:
                raise AlreadyExistsEmailError
    
    except WrongEmailTypeError as we:
        logging.error(f"[helper_invite_member_checking_already_email_address] WrongEmailTypeError: {we}")
        raise WrongEmailTypeError(we)
    except AlreadyExistsEmailError as ae:
        logging.error(f"[helper_invite_member_checking_already_email_address] AlreadyExistsEmailError: {ae}")
        raise AlreadyExistsEmailError(ae)
    except DBError as dbe:
        logging.error(f"[helper_invite_member_checking_already_email_address] DBError: {dbe}")
        raise DBError(dbe)
    except Exception as e:
        logging.error(f"[helper_invite_member_checking_already_email_address] Exception: {e}")
        raise Exception(e)



async def helper_invite_member_making_query_data_and_mail_data(db:AsyncSession, company_info_query:CompanyInfoQuery, domain_data:inviteMemberDomain):
    try:
        company_name = await company_info_query.get_company_name_by_company_key(db, domain_data.company_key)
        invite_date = get_utc_now()
        expire_date = get_utc_after_days(days=2)
        
        domain_data.insert_data, domain_data.mail_data = zip(*[(
            # for database
            {
                "email_address_invite": email_address,
                "company_key": domain_data.company_key,
                "auth_key": (auth_key := str(uuid4()).replace("-", "")[:12]),
                "auth_key_exp_date": expire_date,
                "invite_date": invite_date,
                "invite_url": (invite_url := make_invitation_url(auth_key=auth_key)),
                "success": None,
                "accept": False,
            },
            # for send mail
            {
                "master_id": domain_data.user_id,
                "company_name": company_name,
                "expire_date": datetime_to_string(datetime_obj=expire_date, datetime_format="%Y-%m-%d %H:%M", timezone_str=domain_data.local_timezone),
                "email_address": email_address,
                "invite_url": invite_url,
                "local_timezone": domain_data.local_timezone,
                "lang": domain_data.lang
            }  
        ) for email_address in domain_data.email_addresses_list])
    
    except DBError as dbe:
        logging.error(f"[helper_invite_member_making_query_data_and_mail_data] DBError: {dbe}")
        raise DBError(dbe)
    except Exception as e:
        logging.error(f"[helper_invite_member_making_query_data_and_mail_data] Exception: {e}")
        raise Exception(e)


async def helper_invite_member_update_success_in_db(db:AsyncSession, invite_history_query:InviteHistoryQuery, domain_data:inviteMemberDomain | reInviteMemberDomain):
    try:
        error_auth_key_list = []
        if isinstance(domain_data.insert_data, (list, tuple)): # domain_data is inviteMemberDomain
            for data, response in zip(domain_data.insert_data, domain_data.mail_response):
                if response["success"]:
                    await invite_history_query.update_success(db, data["auth_key"], {"success": True})
                else:
                    error_auth_key_list.append(data["auth_key"])
                    await invite_history_query.update_error_message(db, data["auth_key"], {"error_message": response["error_message"]})
        else: # domain_data is reInviteMemberDomain
            if domain_data.mail_response["success"]:
                await invite_history_query.update_success(db, domain_data.insert_data["auth_key"], {"success": True})
            else:
                error_auth_key_list.append(domain_data.insert_data["auth_key"])
                await invite_history_query.update_error_message(db, domain_data.insert_data["auth_key"], {"error_message": domain_data.mail_response["error_message"]})

        if error_auth_key_list:
            raise Exception(error_auth_key_list)

    except DBError as dbe:
        logging.error(f"[helper_invite_member_update_success_in_db] DBError: {dbe}")
        raise DBError(dbe)
    except Exception as e:
        logging.error(f"[helper_invite_member_update_success_in_db] Exception: {e}")
        raise Exception(e)


def helper_reinvite_member_making_domain_data(payload:reInviteMemberPayload, user_info:dict):
    try:
        return reInviteMemberDomain(
            company_key=user_info["company_key"],
            user_id=user_info["user_id"],
            lang=payload.lang,
            email_address=payload.email_address,
            local_timezone=payload.local_timezone,
            invite_date=get_utc_now()
        )
    except Exception as e:
        logging.error(f"[helper_reinvite_member_making_domain_data] Exception: {e}")
        raise Exception(e)


async def helper_reinvite_member_checking_already_email_address(db:AsyncSession, invite_history_query:InviteHistoryQuery, domain_data:reInviteMemberDomain):
    try:
        p = re.compile('^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        if not p.match(domain_data.email_address):
            raise WrongEmailTypeError
        not_able_send_email_check_set = await invite_history_query.get_invite_email_set(db, domain_data)
        if domain_data.email_address in not_able_send_email_check_set:
            raise AlreadyExistsEmailError
    except WrongEmailTypeError as we:
        logging.error(f"[helper_reinvite_member_checking_already_email_address] WrongEmailTypeError: {we}")
        raise WrongEmailTypeError(we)
    except AlreadyExistsEmailError as ae:
        logging.error(f"[helper_reinvite_member_checking_already_email_address] AlreadyExistsEmailError: {ae}")
        raise AlreadyExistsEmailError(ae)
    except DBError as dbe:
        logging.error(f"[helper_reinvite_member_checking_already_email_address] DBError: {dbe}")
        raise DBError(dbe)
    except Exception as e:
        logging.error(f"[helper_reinvite_member_checking_already_email_address] Exception: {e}")
        raise Exception(e)


async def helper_reinvite_member_making_query_data_and_mail_data(db:AsyncSession, company_info_query:CompanyInfoQuery, domain_data:reInviteMemberDomain):
    try:
        company_name = await company_info_query.get_company_name_by_company_key(db, domain_data.company_key)
        invite_date = get_utc_now()
        expire_date = get_utc_after_days(days=2)
        
        domain_data.insert_data = {
            "email_address_invite": domain_data.email_address,
            "company_key": domain_data.company_key,
            "auth_key": (auth_key := str(uuid4()).replace("-", "")[:12]),
            "auth_key_exp_date": expire_date,
            "invite_date": invite_date,
            "invite_url": (invite_url := make_invitation_url(auth_key=auth_key)),
            "success": False,
            "accept": False
        }
        domain_data.mail_data = {
            "master_id": domain_data.user_id,
            "company_name": company_name,
            "expire_date": datetime_to_string(datetime_obj=expire_date, datetime_format="%Y-%m-%d %H:%M", timezone_str=domain_data.local_timezone),
            "email_address": domain_data.email_address,
            "invite_url": invite_url,
            "local_timezone": domain_data.local_timezone,
            "lang": domain_data.lang
        }
    
    except DBError as dbe:
        logging.error(f"[helper_reinvite_member_making_query_data_and_mail_data] DBError: {dbe}")
        raise DBError(dbe)
    except Exception as e:
        logging.error(f"[helper_reinvite_member_making_query_data_and_mail_data] Exception: {e}")
        raise Exception(e)
    

def helper_accept_invitation_decode_invitation_key(domain_data:acceptDomain):
    try:
        invitation_info_dict = decode_invitation_url(domain_data.acceptance)
        domain_data.auth_key = invitation_info_dict.get("authKey")
    except Exception as e:
        logging.error(f"[helper_accept_invitation_decode_invitation_key] Exception: {e}")
        raise Exception(e)


def helper_accept_invitation_making_invitation_front_url(domain_data:acceptDomain):
    try:
        expire_time_utc = adapt_timezone_datetime_to_datetime(datetime_obj=domain_data.row["auth_key_exp_date"], timezone_str="UTC")
        now = get_utc_now()
        if now > expire_time_utc: # expired
            domain_data.redirect_url = make_invitation_front_url_expired()
        else: # not expired
            domain_data.redirect_url = make_invitation_front_url(auth_key=domain_data.auth_key)
            
    except Exception as e:
        logging.error(f"[helper_accept_invitation_making_invitation_front_url] Exception: {e}")
        raise Exception(e)





# ==============================
# inner method 
# ==============================

def _check_status_and_make_data(row) -> dict:
    # current time
    current_time = get_utc_now()

    # set condition
    is_active = row.get("accept") == True
    is_waiting = row.get("auth_key_exp_date") > current_time
    is_expired = row.get("auth_key_exp_date") < current_time
    is_false = row.get("success") == False
    # set data
    if is_active:
        data = {
            "status": "complete",
            "authName": row.get("auth_name"),
            "department": row.get("department"),
            "date": row.get("invite_date"),
            "userId": row.get("user_id"),
            "emailAddress": row.get("email_address")
        }
    elif is_false:
        data = {
            "status": "false",
            "authName": None,
            "department": None,
            "date": row.get("invite_date"),
            "userId": None,
            "emailAddress": row.get("email_address_invite")
        }
    elif is_waiting:
        data = {
            "status": "waiting",
            "authName": None,
            "department": None,
            "date": row.get("invite_date"),
            "userId": None,
            "emailAddress": row.get("email_address_invite")
        }
    elif is_expired:
        data = {
            "status": "expired",
            "authName": None,
            "department": None,
            "date": row.get("invite_date"),
            "userId": None,
            "emailAddress": row.get("email_address_invite")
        }

    return data


async def send_invitation_mail_by_dream_mailer(domain_data:inviteMemberDomain | reInviteMemberDomain):
    try:
        if isinstance(domain_data.mail_data, (list, tuple)):
            result = []
            for arg in domain_data.mail_data:
                message = {
                    "lang": arg["lang"],
                    "expireDate": arg["expire_date"],
                    "companyName": arg["company_name"],
                    "masterId": arg["master_id"],
                    "userId": arg["email_address"],
                    "query": arg["invite_url"]
                }
                response = await send_mail_by_dream_mailer(
                    template_name=INVITATION_EMAIL_TEMPLATE_NAME,
                    data=message,
                    service_code=EMAIL_SERVICE_CODE
                )
                result.append(response)
        else:
            message = {
                "lang": domain_data.mail_data["lang"],
                "expireDate": domain_data.mail_data["expire_date"],
                "companyName": domain_data.mail_data["company_name"],
                "masterId": domain_data.mail_data["master_id"],
                "userId": domain_data.mail_data["email_address"],
                "query": domain_data.mail_data["invite_url"]
            }
            result = await send_mail_by_dream_mailer(
                template_name=INVITATION_EMAIL_TEMPLATE_NAME,
                data=message,
                service_code=EMAIL_SERVICE_CODE
            )
        
        domain_data.mail_response = result
    
    except Exception as e:
        logging.error(e)
        raise Exception(e)


def make_invitation_url(auth_key:str):
    base_url = REAL_API_URL if os.getenv("SERVER_STAGE") == REAL else STAGING_API_URL if os.getenv("SERVER_STAGE") == STAGING else DEV_API_URL
    path = 'admin/accept'
    query = f"?authKey={auth_key}"
    encode_base64 = base64.urlsafe_b64encode(query.encode()).decode()
    return base_url + path + "?acceptance=" + encode_base64


# def make_invitation_front_url(success:bool, company_name:str, email_address:str, invite_history_id:str, company_key:str):
def make_invitation_front_url(auth_key:str):
    base_url = REAL_URL if os.getenv("SERVER_STAGE") == REAL else STAGING_URL if os.getenv("SERVER_STAGE") == STAGING else DEV_URL
    query = f"signin?invitation=True&invitationKey={auth_key}"
    return base_url + query


def make_invitation_front_url_expired():
    base_url = REAL_URL if os.getenv("SERVER_STAGE") == REAL else STAGING_URL if os.getenv("SERVER_STAGE") == STAGING else DEV_URL
    query = "signin?invitation=Expired"
    return base_url + query


def decode_invitation_url(args):
    decode_base64_to_query = base64.urlsafe_b64decode(args).decode()
    decode_query_to_dict = dict(parse_qsl(decode_base64_to_query.lstrip("?")))
    return decode_query_to_dict