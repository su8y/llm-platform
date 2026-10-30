import calendar
from heapq import nlargest

from sqlalchemy.ext.asyncio import AsyncSession
from dateutil.relativedelta import relativedelta

from queries.user_info import UserInfoQuery
from queries.chat_history import ChatHistoryQuery
from queries.ask_top import AskTopQuery
from payload.monitoring import *
from domain.monitoring import *
from utils.date import *
from utils.error import *



def helper_get_chat_history_make_domain_data(payload:getChatHistoryPayload, user_info:dict):
    try:
        # set date    
        start_date = string_to_datetime(payload.start_date, "UTC") if payload.start_date else None
        start_date_local = adapt_timezone_str_to_datetime(payload.start_date, payload.timezone) if payload.start_date else None
        end_date = get_last_hour_of_day(payload.end_date, "UTC") if payload.end_date else None

        # result
        return getChatHistoryDomain(
            company_key=user_info["company_key"],
            page=payload.page,
            per_page=payload.per_page,
            start_date=start_date,
            end_date=end_date,
            asker_id=payload.asker_id,
            manager_id=payload.manager_id,
            issue_status=payload.issue_status,
            timezone=payload.timezone,
            start_date_local=start_date_local,
            is_mcp=payload.is_mcp
        )
    except Exception as e:
        logging.error(e)
        raise DataError(e)


async def helper_get_session_list_and_count(db:AsyncSession, chat_history_query:ChatHistoryQuery, domain_data:getChatHistoryDomain):
    try:
        domain_data.session_list, domain_data.session_count = await chat_history_query.get_session_list(
            db=db,
            domain_data=domain_data
        )
    except DBError as e:
        logging.error(f"[helper.monitoring.helper_get_session_list_and_count] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.monitoring.helper_get_session_list_and_count] Exception: {e}")
        raise e


async def helper_get_chat_history_from_db_and_reform(db:AsyncSession, chat_history_query:ChatHistoryQuery, domain_data:getChatHistoryDomain):
    try:
        # get chat history by session_key
        domain_data.chat_history_rows = await chat_history_query.get_chat_history_by_session_list(
            db=db,
            domain_data=domain_data
        )
        
        # reform data for frontend
        _reform_chat_history_data(domain_data)
    
    except DBError as e:
        logging.error(f"[helper.monitoring.helper_get_chat_history_from_db_and_reform] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.monitoring.helper_get_chat_history_from_db_and_reform] Exception: {e}")
        raise e


def _reform_chat_history_data(domain_data:getChatHistoryDomain):
    """session_key 기준으로 묶어서 표기"""
    # datas:list, count:int, start_date_datetime_local:datetime=None, local_timezone:str=None
    middle = dict()
    result = list()
    session_key_checker = set()
    for data in domain_data.chat_history_rows:
        row = dict()
        if data["session_key"] in session_key_checker:
            if data["reg_date"] < middle[data['session_key']]['regDate']:
                middle[data['session_key']]['regDate'] = data["reg_date"]
                middle[data['session_key']]['chatTitle'] = data.get("chat_title") or data["message"] if data["role"] == "human" else ""          
            if data["rating"]:
                middle[data['session_key']]['rating'].append(data["rating"])
        else:
            session_key_checker.add(data["session_key"])
            row["sessionKey"] = data["session_key"]
            row["issueStatus"] = data["issue_status"]
            row["regDate"] = data["reg_date"]
            row["askerId"] = data["asker_id"] if data.get("asker_id", None) else "llm-platform"
            row["askerName"] = data["asker_name"]
            row["managerId"] = data["manager_id"]
            row["rating"] = [data["rating"]] if data["rating"] else []
            row["chatTitle"] = data.get("chat_title") or data["message"] if data["role"] == "human" else ""
            row["isMCP"] = bool(data.get("is_mcp", False))
            
            middle[data['session_key']] = row
    
    for value in middle.values():
        value["rating"] = round(sum(value["rating"]) / len(value["rating"]), 1) if value["rating"] else None
        if not domain_data.start_date_local or change_local_datetime(value["regDate"], domain_data.timezone) >= domain_data.start_date_local:
            result.append(value)
    
    result.sort(key=lambda x: x["regDate"], reverse=True)
    domain_data.rows = result
    domain_data.issue_count = len([r for r in result if r['issueStatus'] == 'needSolve'])


def helper_get_chat_history_head_make_domain_data(payload:getChatHistoryDetailHeadPayload, user_info:dict):
    company_key = user_info["company_key"]
    session_key = payload.session_key
    return getChatHistoryDetailHeadDomain(
        company_key=company_key,
        session_key=session_key
    )


async def helper_get_chat_history_head(db:AsyncSession, chat_history_query:ChatHistoryQuery, user_info_query:UserInfoQuery, domain_data:getChatHistoryDetailHeadDomain):
    try:
        domain_data.rows = await chat_history_query.get_chat_history_head(db, domain_data)
        domain_data.reformed_rows = reform_chat_history_detail_head(domain_data) if domain_data.rows else None
        domain_data.id_list = await user_info_query.get_user_ids(db=db, domain_data=domain_data) if domain_data.reformed_rows else None
    except DBError as e:
        logging.error(f"[helper.monitoring.helper_get_chat_history_head] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.monitoring.helper_get_chat_history_head] Exception: {e}")
        raise e


def helper_get_chat_history_tail_make_domain_data(payload:getChatHistoryDetailTailPayload, user_info:dict):
    try:
        page_mode = payload.page_mode
        page = int(payload.page) if page_mode else None
        per_page = int(payload.per_page) if page_mode else None

        return getChatHistoryDetailTailDomain(
            page_mode=page_mode,
            page=page,
            per_page=per_page,
            company_key=user_info["company_key"],
            session_key=payload.session_key
        )

    except Exception as e:
        logging.error(e)
        raise DataError(e)


async def helper_get_chat_history_tail(db:AsyncSession, chat_history_query:ChatHistoryQuery, domain_data:getChatHistoryDetailTailDomain):
    try:
        domain_data.rows = await chat_history_query.get_chat_history_tail(
            db=db,
            domain_data=domain_data
        )
        domain_data.reformed_rows = reform_chat_history_data_tail(datas=domain_data.rows)
        domain_data.count = await chat_history_query.get_chat_history_tail_count(db=db, domain_data=domain_data)
    
    except DBError as e:
        logging.error(f"[helper.monitoring.helper_get_chat_history_tail] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.monitoring.helper_get_chat_history_tail] Exception: {e}")
        raise e


def helper_get_chat_rating_make_domain_data(payload:getChatRatingPayload, user_info:dict):
    try:
        company_key = user_info["company_key"]
        period = payload.period
        local_timezone = payload.timezone
        start_date = payload.start_date
        start_date_datetime_utc = string_to_datetime(start_date, "UTC")
        start_date_datetime_local = adapt_timezone_str_to_datetime(start_date, local_timezone)
        end_date = payload.end_date
        end_date_datetime_utc = get_last_hour_of_day(end_date, "UTC")
        end_date_datetime_local = adapt_timezone_str_to_datetime(end_date, local_timezone)
        return getChatRatingDomain(
            # for query
            company_key=company_key,
            start_date=start_date_datetime_utc,
            end_date=end_date_datetime_utc,
            # for reform
            period=period,
            start_date_local=start_date_datetime_local,
            end_date_local=end_date_datetime_local,
            timezone=local_timezone
        )
    except Exception as e:
        logging.error(f"[helper.monitoring.helper_get_chat_rating_make_query_data] Exception: {e}")
        raise DataError(e)


async def helper_get_chat_rating(db:AsyncSession, chat_history_query:ChatHistoryQuery, domain_data:getChatRatingDomain):
    try:
        domain_data.rows = await chat_history_query.get_chat_rating(
            db=db,
            domain_data=domain_data
        )
        domain_data.reformed_rows = reform_chat_rating_data(domain_data)
    except DBError as e:
        logging.error(f"[helper.monitoring.helper_get_chat_rating] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.monitoring.helper_get_chat_rating] Exception: {e}")
        raise e


def helper_get_chat_count_make_domain_data(payload:getChatCountPayload, user_info:dict):
    company_key = user_info["company_key"]
    period = payload.period
    local_timezone = payload.timezone
    start_date = payload.start_date
    end_date = payload.end_date
    start_date_datetime_utc = string_to_datetime(start_date, "UTC")
    start_date_datetime_local = adapt_timezone_str_to_datetime(start_date, local_timezone)
    end_date_datetime_utc = get_last_hour_of_day(end_date, "UTC")
    end_date_datetime_local = adapt_timezone_str_to_datetime(end_date, local_timezone)
    return getChatCountDomain(
        # for query
        company_key=company_key,
        start_date=start_date_datetime_utc,
        end_date=end_date_datetime_utc,
        # for reform
        period=period,
        timezone=local_timezone,
        start_date_local=start_date_datetime_local,
        end_date_local=end_date_datetime_local
    )


async def helper_get_chat_count(db:AsyncSession, chat_history_query:ChatHistoryQuery, domain_data:getChatCountDomain):
    try:
        domain_data.rows = await chat_history_query.get_chat_count(
            db=db,
            domain_data=domain_data
        )
        reform_chat_count_data(domain_data)
    except DBError as e:
        logging.error(f"[helper.monitoring.helper_get_chat_count] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.monitoring.helper_get_chat_count] Exception: {e}")
        raise e


def helper_update_chat_history_make_domain_data(payload:updateChatHistoryPayload, user_info:dict):
    update_data = [payload.rating, payload.assessor_id, payload.issue_status, payload.manager_id]
    if not any(update_data):
        raise DataError("There is not update data.")
    
    return {
        "company_key": user_info["company_key"],
        "session_key": payload.session_key,
        "manager_id": payload.manager_id,
        "issue_status": payload.issue_status,
        "rating": payload.rating,
        "assessor_id": payload.assessor_id
    }


async def helper_update_chat_history(db:AsyncSession, chat_history_query:ChatHistoryQuery, domain_data:updateChatHistoryDomain):
    try:
        result = await chat_history_query.update_chat_history(
            db=db,
            domain_data=domain_data
        )
        return result
    except DBError as e:
        logging.error(f"[helper.monitoring.helper_update_chat_history] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.monitoring.helper_update_chat_history] Exception: {e}")
        raise e


def helper_get_top_make_query_data(payload:getTopPayload, user_info:dict):
    company_key = user_info["company_key"]
    start_date = payload.start_date
    end_date = payload.end_date
    start_date_datetime_utc = string_to_datetime(start_date, "UTC")
    end_date_datetime_utc = string_to_datetime(end_date, "UTC")
    return {
        "company_key": company_key,
        "start_date": start_date_datetime_utc,
        "end_date": end_date_datetime_utc
    }


async def helper_get_top(db:AsyncSession, ask_top_query:AskTopQuery, query_data:dict):
    try:
        result = await ask_top_query.get_top(
            db=db,
            company_key=query_data["company_key"],
            start_date=query_data["start_date"],
            end_date=query_data["end_date"]
        )
        data = reform_ask_top_data(result)
        return data
    except DBError as e:
        logging.error(f"[helper.monitoring.helper_get_top] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.monitoring.helper_get_top] Exception: {e}")
        raise e


def helper_run_ask_keyword_make_args_data(payload):
    period = payload.get("period", "day")
    target_date = payload.get("target_date", None)
    company_key = payload.get("company_key", None)
    model = payload.get("model", "gpt-4o-mini")

    #TODO: temporary code. will delete after building AskKeyword Task
    if not target_date and period == "day":
        date_format = "%Y-%m-%d"
        start_date = datetime.strptime("2025-01-01", date_format).astimezone(tz=ZoneInfo("UTC"))
        end_date = datetime.strptime("2025-01-13", date_format).astimezone(tz=ZoneInfo("UTC"))
        target_date = [day.strftime(date_format) for day in (start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1))]
    elif not target_date and period == "week":
        # date_format = "%Y-%m-%d"
        # start_date = datetime.strptime("2024-10-20", date_format).astimezone(tz=timezone("utc"))
        # end_date = datetime.strptime("2024-11-07", date_format).astimezone(tz=timezone("utc"))
        target_date = ["2024-10-07", "2024-10-14", "2024-10-21", "2024-10-28", "2024-11-04", "2024-11-11", "2024-11-18", "2024-11-25", "2024-12-02", "2024-12-09", "2024-12-16", "2024-12-23", "2024-12-30", "2025-01-06"]
        # target_date = [day.strftime("%Y-%m") for day in (start_date + relativedelta(months=i) for i in range((end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1))]
    elif not target_date and period == "month":
        # date_format = "%Y-%m-%d"
        # start_date = datetime.strptime("2024-10-20", date_format).astimezone(tz=timezone("utc"))
        # end_date = datetime.strptime("2024-11-07", date_format).astimezone(tz=timezone("utc"))
        # target_date = [day.strftime("%Y-%m") for day in (start_date + relativedelta(months=i) for i in range((end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1))]
        target_date = ["2024-10-01"] # ["2024-10-01", "2024-11-01", "2024-12-01"]
    
    return {
        "period": period,
        "company_key": company_key,
        "target_date": target_date,
        "model": model
    }











def reform_chat_history_detail_head(domain_data:getChatHistoryDetailHeadDomain):
    result = {}
    for enum, data in enumerate(domain_data.rows):
        
        if enum == 0: # base format
            result["sessionKey"] = data["session_key"]
            result["managerId"] = data["manager_id"]
            result["issueStatus"] = data["issue_status"]
            result["regDate"] = data["reg_date"]
            result["askerId"] = data["asker_id"] if data.get("asker_id", None) else "llm-platform"
            result["askerName"] = data["asker_name"]
            result["rating"] = [data["rating"]] if data["rating"] else []
            result["assessorId"] = data["assessor_id"]
            result["ratingGraph"] = {"X": ["1", "2", "3", "4", "5"], "data": [0, 0, 0, 0, 0]}
            if data["rating"]:
                result["ratingGraph"]["data"][data["rating"]-1] += 1
        
        else:
            result["regDate"] = data["reg_date"] if data["reg_date"] < result["regDate"] else result["regDate"]
            if data["rating"]:
                result["rating"].append(data["rating"])
                result["ratingGraph"]["data"][data["rating"]-1] += 1
    
    result["rating"] = round(sum(result["rating"])/len(result["rating"]), 1) if len(result["rating"]) else None
    return result


def reform_chat_history_data_tail(datas:list) -> dict:
    datas.sort(key=lambda x:x["reg_date"])
    return {
            "rows": [
                {
                    "id": data["id"],
                    "message": data["message"],
                    "role": data["role"],
                    "regDate": data["reg_date"],
                    "rating": data["rating"],
                    "memo": data["memo"],
                } for data in datas
            ]
    }


def reform_chat_rating_data(domain_data:getChatRatingDomain):
    try:
        result = {
            "target": {"total": 0, "targetCount": 0, "targetRatio": 0},
            "askGraph": {"X": ["1", "2", "3", "4", "5"], "data": [0, 0, 0, 0, 0]},
            "ratingGraph": {"X": [], "data": []},
            "average": 0
        }

        date_format = "%Y-%m" if domain_data.period == "month" else "%Y-%m-%d"
        if domain_data.period == "day":
            rating_avg = {day.strftime(date_format): [] for day in (domain_data.start_date_local + timedelta(days=i) for i in range((domain_data.end_date_local - domain_data.start_date_local).days + 1))}
        elif domain_data.period == "month":
            rating_avg = {day.strftime("%Y-%m"): [] for day in (domain_data.start_date_local + relativedelta(months=i) for i in range((domain_data.end_date_local.year - domain_data.start_date_local.year) * 12 + domain_data.end_date_local.month - domain_data.start_date_local.month + 1))}
        elif domain_data.period == "week":
            rating_avg = {get_weeks_dateformat(day): [] for day in (domain_data.start_date_local + timedelta(days=i*7) for i in range((domain_data.end_date_local - domain_data.start_date_local).days // 7 + 1))}

        if not domain_data.rows:
            result["ratingGraph"] = {"X": list(rating_avg.keys()), "data": [0 for _ in range(len(rating_avg))]}
            return result
        else:
            # set default format
            len_datas = len(domain_data.rows)
            sorted_datas = sorted(domain_data.rows, key=lambda x: x["reg_date"].astimezone(tz=ZoneInfo(domain_data.timezone)), reverse=False)
            ratings = {i: [] for i in range(1, 6)}
            for r in sorted_datas:
                rating = r["rating"]
                if rating in ratings:
                    ratings[rating].append(r["rating"])

            # set value for loop
            for r in sorted_datas:
                rating = r["rating"]
                if rating:
                    rating_avg[r["reg_date"].astimezone(tz=ZoneInfo(domain_data.timezone)).strftime(date_format)].append(rating)
            rating_all = ratings[1] + ratings[2] + ratings[3] + ratings[4] + ratings[5]
            length_rating_all = len(rating_all)
            rating_sum = sum(rating_all)

            result["target"] = {
                "total": len_datas,
                "targetCount": length_rating_all,
                "targetRatio": round(length_rating_all/len_datas, 2)
            }
            result["askGraph"] = {
                "X": ["1", "2", "3", "4", "5"],
                "data": [len(ratings[1]), len(ratings[2]), len(ratings[3]), len(ratings[4]), len(ratings[5])]
            }
            result["average"] = round(rating_sum/length_rating_all, 1) if length_rating_all else 0
            for key, value in rating_avg.items():
                result["ratingGraph"]["X"].append(key)
                result["ratingGraph"]["data"].append(round(sum(value)/len(value), 1) if len(value) else 0)
            return result
    
    except Exception as e:
        logging.error(f"[helper.monitoring.reform_chat_rating_data] Exception: {e}")
        raise e


def reform_chat_count_data(domain_data:getChatCountDomain):
    try:
        result = {
            "session": {"X": [], "data": []},
            "chat": {"X": [], "data": []}
        }
        date_format = "%Y-%m" if domain_data.period == "month" else "%Y-%m-%d"
        
        if not domain_data.rows:
            result["chat"] = {"X": [day.strftime(date_format) for day in (domain_data.start_date_local + timedelta(days=i) for i in range((domain_data.end_date_local - domain_data.start_date_local).days + 1))], "data": [0 for _ in range((domain_data.end_date_local - domain_data.start_date_local).days + 1)]}
            result["session"] = {"X": [day.strftime(date_format) for day in (domain_data.start_date_local + timedelta(days=i) for i in range((domain_data.end_date_local - domain_data.start_date_local).days + 1))], "data": [0 for _ in range((domain_data.end_date_local - domain_data.start_date_local).days + 1)]}    
        else:
            if domain_data.period == "day":
                middle = {"chat": {day.strftime(date_format): 0 for day in (domain_data.start_date_local + timedelta(days=i) for i in range((domain_data.end_date_local - domain_data.start_date_local).days + 1))}, "session": {day.strftime(date_format): set() for day in (domain_data.start_date_local + timedelta(days=i) for i in range((domain_data.end_date_local - domain_data.start_date_local).days + 1))}}
            elif domain_data.period == "month":
                middle = {"chat": {day.strftime("%Y-%m"): 0 for day in (domain_data.start_date_local + relativedelta(months=i) for i in range((domain_data.end_date_local.year - domain_data.start_date_local.year) * 12 + domain_data.end_date_local.month - domain_data.start_date_local.month + 1))}, "session": {day.strftime("%Y-%m"): set() for day in (domain_data.start_date_local + relativedelta(months=i) for i in range((domain_data.end_date_local.year - domain_data.start_date_local.year) * 12 + domain_data.end_date_local.month - domain_data.start_date_local.month + 1))}}
            elif domain_data.period == "week":
                middle = {"chat": {get_weeks_dateformat(day): 0 for day in (domain_data.start_date_local + timedelta(days=i*7) for i in range((domain_data.end_date_local - domain_data.start_date_local).days // 7 + 1))}, "session": {get_weeks_dateformat(day): set() for day in (domain_data.start_date_local + timedelta(days=i*7) for i in range((domain_data.end_date_local - domain_data.start_date_local).days // 7 + 1))}}
            
            for data in domain_data.rows:
                if domain_data.period != "week":
                    date = datetime_to_string(datetime_obj=data["reg_date"], timezone_str=domain_data.timezone)
                else:
                    date = get_weeks_dateformat(change_local_datetime(datetime_obj=data["reg_date"]), timezone_str=domain_data.timezone)
                middle["chat"][date] += 1
                middle["session"][date].add(data["session_key"])

            chat_dates = tuple(middle["chat"].keys())
            session_dates = tuple(middle["session"].keys())
            result["chat"] = {"X": chat_dates, "data": [middle["chat"][date] for date in chat_dates]}
            result["session"] = {"X": session_dates, "data": [len(middle["session"][date]) for date in session_dates]}
            
        domain_data.reformed_rows = result
    
    except Exception as e:
        logging.error(f"[helper.monitoring.reform_chat_count_data] Exception: {e}")
        raise e


def get_weeks_dateformat(datetime:datetime):
    year = int(datetime.year)
    month = int(datetime.month)
    day = int(datetime.day)
    cal = calendar.Calendar(firstweekday=0)
    month_weeks = cal.monthdayscalendar(year, month)
    for enum, week in enumerate(month_weeks, start=1):
        if day in week:
            return f"{year}-{month}-{enum}"
        

def reform_ask_top_data(datas: list) -> list:
    if not datas:
        return [None, None, None]
    
    reform_data = []
    for data in datas:
        reform_data.extend([
            {"question": data[f"rank{i}"], "count": data[f"rank{i}_count"]}
            for i in range(1, 4)
        ])    
    # nlargest를 사용하여 상위 3개 항목 추출
    top_3 = nlargest(3, reform_data, key=lambda x: x["count"])

    return [item["question"] for item in top_3]