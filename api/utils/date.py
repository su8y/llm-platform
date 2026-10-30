from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo
import calendar
from email.utils import format_datetime


# datetime function for plan ================================
def get_init_plan_date(start_date:datetime, period:str=None, local_timezone:str=None) -> tuple[datetime, datetime]:
    period = period or "month"
    local_timezone = local_timezone or "Asia/Seoul"
    start_date_local = start_date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=ZoneInfo(local_timezone))
    
    if period == "month":
        if (start_date_local.month == 2 and start_date_local.day >= 28) or start_date_local.day >= 29:
            end_date_local = get_last_day_of_month(get_after_months(start_date_local, 1)).replace(tzinfo=ZoneInfo(local_timezone)).astimezone(tz=ZoneInfo("UTC"))
        else:
            end_date_local = (get_after_months(start_date_local, 1) - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
    elif period == "year":
        end_date_local = (get_after_years(start_date_local, 1)-timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        raise ValueError("Invalid period")
    
    start_date_utc = start_date_local.astimezone(tz=ZoneInfo("UTC"))
    end_date_utc = end_date_local.astimezone(tz=ZoneInfo("UTC"))
    return (start_date_utc, end_date_utc)


def get_next_plan_date(before_end_date:datetime, period:str=None, local_timezone:str=None) -> tuple[datetime, datetime]:
    local_timezone = local_timezone or "Asia/Seoul"
    next_start_date = before_end_date + timedelta(microseconds=1)
    if period == "month":
        if (next_start_date.month == 2 and next_start_date.day >= 28) or next_start_date.day >= 29:
            next_end_date = get_last_day_of_month(get_after_months(next_start_date, 1)).replace(tzinfo=ZoneInfo(local_timezone)).astimezone(tz=ZoneInfo("UTC"))
        else:
            next_end_date = get_after_months(next_start_date, 1) - timedelta(microseconds=1)
    elif period == "year":
        next_end_date = get_after_years(next_start_date, 1) - timedelta(microseconds=1)
    else:
        raise ValueError("Invalid period")
    return (next_start_date, next_end_date)


def get_utc_now() -> datetime:
	return datetime.now(ZoneInfo("UTC"))


def get_utc_after_days(days:float) -> datetime:
    return datetime.now(ZoneInfo("UTC")) + timedelta(days=days)


def get_after_months(target:datetime, months:int) -> datetime:
    return target + relativedelta(months=months)


def get_after_years(target:datetime, years:int) -> datetime:
    return target + relativedelta(years=years)


def get_local_now(timezone_str:str=None) -> datetime:
    timezone_str = "Asia/Seoul" if not timezone_str else timezone_str
    return datetime.now(ZoneInfo(timezone_str))


def adapt_timezone_datetime_to_datetime(datetime_obj:datetime, timezone_str:str) -> datetime:
    if datetime_obj is None:
        return None
    else:
        return datetime_obj.replace(tzinfo=ZoneInfo(timezone_str))


def adapt_timezone_str_to_datetime(datetime_str:str, timezone_str:str, datetime_format:str=None) -> datetime:
    if datetime_str is None:
        return None
    else:
        datetime_format = "%Y-%m-%d" if not datetime_format else datetime_format
        return datetime.strptime(datetime_str, datetime_format).replace(tzinfo=ZoneInfo(timezone_str))


def change_utc_datetime(datetime_obj:datetime) -> datetime:
    """
    :param datetime_obj: datetime
    :param timezone_str: str
    :return datetime(utc)
    """
    if datetime_obj is None:
        return None
    else:
        return datetime_obj.astimezone(ZoneInfo("UTC"))


def change_local_datetime(datetime_obj:datetime, timezone_str:str=None) -> datetime:
    """
    :param datetime_obj: datetime
    :param timezone_str: str
    :return datetime(utc)
    """
    if datetime_obj is None:
        return None
    else:
        timezone_str = "Asia/Seoul" if not timezone_str else timezone_str
        return datetime_obj.astimezone(tz=ZoneInfo(timezone_str))


def str_to_datetime(datetime_str:str) -> datetime:
    return datetime.strptime(datetime_str, "%Y-%m-%d")


def string_to_datetime(datetime_str:str, timezone_str:str=None, format:str=None) -> datetime:
    if datetime_str is None:
        return None
    else:
        timezone_str = "UTC" if not timezone_str else timezone_str
        return datetime.strptime(datetime_str, format or "%Y-%m-%d").astimezone(tz=ZoneInfo(timezone_str))


def datetime_to_string(datetime_obj:datetime, datetime_format:str=None, timezone_str:str=None) -> str:
    if datetime_obj is None:
        return None
    else:
        datetime_format = "%Y-%m-%d" if not datetime_format else datetime_format
        return datetime_obj.astimezone(tz=ZoneInfo(timezone_str)).strftime(datetime_format) if timezone_str else datetime_obj.strftime(datetime_format)


def get_first_hour_of_day(datetime_obj, timezone_str: str = None) -> datetime:
    if datetime_obj is None:
        return None
    else:
        timezone_str = "Asia/Seoul" if not timezone_str else timezone_str
        if isinstance(datetime_obj, str):
            local_date = datetime.strptime(datetime_obj, "%Y-%m-%d").astimezone(tz=ZoneInfo(timezone_str))
        elif isinstance(datetime_obj, datetime):
            local_date = datetime_obj.astimezone(tz=ZoneInfo(timezone_str))
        else:
            raise ValueError("Invalid datetime type")
        return local_date.replace(hour=0, minute=0, second=0, microsecond=0)


def get_last_hour_of_day(datetime_str:str, timezone_str:str=None) -> datetime:
    if datetime_str is None:
        return None
    else:
        timezone_str = "Asia/Seoul" if not timezone_str else timezone_str
        return datetime.combine(datetime.strptime(datetime_str, "%Y-%m-%d"), datetime.max.time()).astimezone(tz=ZoneInfo(timezone_str))


def get_last_day_of_month(datetime_obj:datetime) -> datetime:
    return datetime_obj.replace(day=calendar.monthrange(datetime_obj.year, datetime_obj.month)[1], hour=23, minute=59, second=59, microsecond=999999)


def cal_offset_hours(timezone:str, _format:str=None):
    _format = _format or "mysql"

    tz = ZoneInfo(timezone)
    now = datetime.now(tz)
    offset = now.strftime('%z')  # +0900

    if _format == "mysql":
        return f"{offset[:3]}:{offset[3:]}"  # +09:00
    return offset  # +0900


# Flask 스타일의 날짜 변환 함수
def flask_style_datetime(dt):
    if isinstance(dt, datetime):
        return format_datetime(dt)  # RFC 1123 형식 (Flask 스타일)
    return dt