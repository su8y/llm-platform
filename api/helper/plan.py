import logging

from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from domain.plan import GetCurrentPlanDomain
from queries.payment import PaymentQuery
from queries.company_info import CompanyInfoQuery
from payload.plan import *
from utils.error import *
from utils.date import *
from utils.constants import *




def helper_insert_payment_makging_data(payload:insertPaymentPayload, user_info:dict):
    return {
        "user_id": user_info["user_id"],
        "company_key": payload.company_key,
        "plan_info_id": payload.plan_id,
        "plan_period": payload.plan_period,
        "reg_date": get_utc_now(),
        "type": payload.type, # card, bank
        "card_number": payload.card_number if payload.type == "card" else None,
        "success": True,
        "approval": True,
        "actual_payment_amount": payload.actual_payment_amount,
    }


def helper_insert_payment_reform(row):
    return {
        "paymentHistoryId": row["id"],
        "companyKey": row["company_key"],
        "planId": row["plan_info_id"],
        "planPeriod": row["plan_period"],
        "regDate": row["reg_date"],
        "regDateString": datetime_to_string(datetime_obj=row["reg_date"]),
        "cardNumber": row["card_number"],
        "type": row["type"],
        "success": row["success"],
        "approval": row["approval"],
        "userId": row["user_id"],
    }


def helper_insert_plan_making_payment_data(payload:insertPlanPayload):
    try:
        target_company_key = payload.company_key
        plan_info_id = payload.plan_id
        plan_period = payload.plan_period
        payment_history_id = payload.payment_history_id
        payment_date = payload.payment_date
        is_target_renewal = payload.is_target_renewal
        local_timezone = payload.local_timezone
        start_date = payload.start_date

        if not plan_info_id or not plan_period or not target_company_key:
            raise DataError("planId, planPeriod, companyKey is required. please check payload")
        reg_date = get_utc_now()
        start_date = str_to_datetime(start_date) if start_date else reg_date
        return {
            "payment_history_id": payment_history_id,
            "target_company_key": target_company_key,
            "plan_info_id": plan_info_id,
            "plan_period": plan_period,
            "payment_date": payment_date,
            "start_date": start_date,
            "reg_date": reg_date,
            "expired_date": get_first_hour_of_day(get_after_years(get_after_months(start_date, months=plan_period+1), years=1)),
            "is_target_renewal": is_target_renewal,
            "local_timezone": local_timezone
        }
    except Exception as e:
        logging.error(e)
        raise DataError(f"[api.plan.helper.helper_insert_plan_making_payment_data] check payload: {e}")


async def check_is_current_plan(db:AsyncSession, payment_query:PaymentQuery, query_data:dict):
    try:
        is_current_plan = await payment_query.is_current_plan(db, query_data["target_company_key"], query_data["reg_date"])
        if is_current_plan:
            logging.info(f"[plan.helper.check_is_current_plan] current plan is exist. can not insert new plan")
            raise DataError("current plan is exist. can not insert new plan")
        await payment_query.update_trial_plan(db, query_data["target_company_key"], query_data["reg_date"])
        await payment_query.delete_expired_plan(db, query_data["target_company_key"])
    except DBError as e:
        logging.error(f"[api.plan.helper.check_is_current_plan] check company_info_table: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[api.plan.helper.check_is_current_plan] check company_info_table: {e}")
        raise Exception(e)


def helper_insert_plan_making_insert_row_data(data):
    try:
        period = "month" # if data["plan_period"] == 1 else "year"
        local_timezone = data["local_timezone"]
        start_date, end_date = get_init_plan_date(data["start_date"], period, local_timezone)
        # next_start_date, next_end_date = get_next_plan_date(end_date, period)

        # 결제 완료 플랜 데이터 생성
        result = []
        for i in range(data["plan_period"]):
            if i != 0:
                start_date, end_date = get_next_plan_date(end_date, period, local_timezone)
            result.append({
                "company_key": data["target_company_key"],
                "plan_info_id": data["plan_info_id"],
                "start_date": start_date,
                "end_date": end_date,
                "reg_date": data["reg_date"],
                "use_credit": 0,
                "payment_status": "complete",
                "change_type": "system",
                "payment_date": data["payment_date"],
                "payment_history_id": data["payment_history_id"]
            })
        
        # 결제 대기 플랜 데이터 생성
        start_date, end_date = get_next_plan_date(end_date, period, local_timezone)
        result.append({
            "company_key": data["target_company_key"],
            "plan_info_id": data["plan_info_id"] if data["is_target_renewal"] is True else 8,
            "start_date": start_date,
            "end_date": end_date,
            "reg_date": data["reg_date"],
            "use_credit": 0,
            "payment_status": "waiting",
            "change_type": "system",
        })
        return tuple(result)
    except Exception as e:
        logging.error(f"[api.plan.helper.helper_insert_plan_making_insert_row_data] check data: {e}")
        raise DataError(f"[api.plan.helper.helper_insert_plan_making_insert_row_data] check data: {e}")


def helper_get_current_credit_make_domain_data(query_params:getCurrentCreditParams, user_info:dict):
    try:
        return GetCurrentPlanDomain(
            company_key=user_info["company_key"],
            params_current_credit=query_params.current_credit if query_params.current_credit not in (None, "") else None
        )
    except Exception as e:
        logging.error(f"[helper.plan.helper_get_current_credit_make_domain_data] DataError: {e}")
        raise DataError("Invalid currentCredit parameter") from e



async def helper_get_plan_info_making_except_data(db:AsyncSession, company_info_query: CompanyInfoQuery, user_info:dict):
    plan_info_id = user_info["plan_info_id"]
    is_trial = True if plan_info_id == 3 else False
    is_expired = True if plan_info_id == 8 else False
    
    if is_trial is True:
        company_info_row = await company_info_query.get_company_info(db, user_info["company_key"])
        result = {
            "useAbleCredit": user_info["credit_available"],
            "totalCredit": 60,
            "startDate": (start_date := company_info_row["reg_date"]),
            "endDate": get_first_hour_of_day(get_after_months(start_date, months=1)),
            "nextDate": None,
            "planName": "Trial",
        }
    elif is_expired is True:
        result = {
            "useAbleCredit": 0,
            "totalCredit": 0,
            "startDate": None,
            "endDate": None,
            "nextDate": None,
            "planName": "Expired",
        }
    else:
        result = None
    return result

def helper_get_plan_history_query_data(payload:getPlanHistoryPayload, user_info:dict):
    return {
        "company_key": user_info["company_key"],
        "page": payload.page,
        "per_page": payload.per_page,
        "plan_name": payload.plan_name,
        "payment_history_type": payload.type,
    }


def helper_change_plan_query_data(payload:changePlanPayload, user_info:dict):
    return {
        "company_key": user_info["company_key"],
        "plan_info_id": payload.plan_id,
        "current_plan_info_id": user_info["plan_info_id"],
        "current_time": get_utc_now()
    }


def helper_checking_is_upgrade(query_data):
    current_plan_info_id = query_data["current_plan_info_id"]
    plan_info_id = query_data["plan_info_id"]
    if current_plan_info_id not in [BASIC_PLAN_ID, PREMIUM_PLAN_ID, PRO_PLAN_ID] or plan_info_id not in [BASIC_PLAN_ID, PREMIUM_PLAN_ID, PRO_PLAN_ID]:
        logging.info(f"[api.plan.helper.helper_checking_is_upgrade] current plan or plan_info_id is not valid. only basic, premium, pro plan is valid")
        logging.info(f"[api.plan.helper.helper_checking_is_upgrade] current_plan_info_id: {current_plan_info_id}, plan_info_id: {plan_info_id}")
        raise DataError("current plan or plan_info_id is not valid")
    
    if current_plan_info_id == BASIC_PLAN_ID:
        is_upgrade = True if plan_info_id in [PREMIUM_PLAN_ID, PRO_PLAN_ID] else False
    elif current_plan_info_id == PREMIUM_PLAN_ID:
        is_upgrade = True if plan_info_id == PRO_PLAN_ID else False
    elif current_plan_info_id == PRO_PLAN_ID:
        is_upgrade = False
    
    return is_upgrade


async def helper_upgrade_plan_check_and_clear(db:AsyncSession, payment_query:PaymentQuery, query_data:dict):
    try:
        current_date = query_data["current_time"]
        target_update_ids = await payment_query.get_plan_until_end(db, query_data["company_key"], current_date)
        if target_update_ids:
            await payment_query.update_before_end_date(db, target_update_ids, current_date)
            # await payment_query.update_plan_payment(db, target_update_ids, current_date)
    except DBError as e:
        logging.error(f"[api.plan.helper.helper_upgrade_plan_check_and_clear] check company_info_table: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[api.plan.helper.helper_upgrade_plan_check_and_clear] check company_info_table: {e}")
        raise DataError(f"[api.plan.helper.helper_upgrade_plan_check_and_clear] check company_info_table")


async def helper_upgrade_next_month_plan_update(db:AsyncSession, payment_query:PaymentQuery, target_upgrade_row, query_data:dict):
    try:
        if target_upgrade_row is None:
            target_upgrade_row = {
                "company_key": query_data["company_key"],
                "plan_info_id": query_data["plan_info_id"],
                "start_date": query_data["current_time"] + timedelta(days=1),
                "end_date": get_after_months(get_last_hour_of_day(query_data["current_time"]), months=1) - timedelta(days=1),
                "payment_date": datetime_to_string((get_after_months(get_last_hour_of_day(query_data["current_time"]), months=1) - timedelta(days=1)) + timedelta(seconds=1)),
                "payment_status": "waiting",
                "change_type": "system",
            }
            await payment_query.insert_plan_payment(db, target_upgrade_row)
        else:
            # await payment_query.update_plan_payment(db, target_upgrade_row)
            pass
    except DBError as e:
        logging.error(e)
        raise e
    except Exception as e:
        logging.error(e)
        raise e
    
    



def reform_plan_info(result):
    try:
        if not result or (len(result) == 1 and result[0]["plan_name"] == "Expired"):
            return {
                "useAbleCredit": None,
                "totalCredit": None,
                "startDate": None,
                "endDate": None,
                "nextDate": None,
                "planName": None,
            }
        else:
            current_plan_row = result[0]
            next_plan_row = result[1] if len(result) > 1 else None
            return {
                "useAbleCredit": current_plan_row["credit_available"],
                "totalCredit": current_plan_row["init_credit"],
                "startDate": current_plan_row["start_date"],
                "endDate": current_plan_row["end_date"],
                "nextDate": next_plan_row["start_date"] if next_plan_row and next_plan_row["plan_name"] != "Expired" else None,
                "planName": current_plan_row["plan_name"],
            }
    except Exception as e:
        logging.error(e)
        raise DataError(e)


def reform_all_plan(results):
    return [
        {
            "planId": result["id"],
            "planName": result["plan_name"],
            "planPrice": result["plan_price"],
            "initCredit": result["init_credit"],
            "model": result["model"],
            "isShow": result["is_show"],
        } for result in results
    ]