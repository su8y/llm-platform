from typing import Any
from dataclasses import dataclass
from datetime import datetime
from email.utils import format_datetime

from fastapi.responses import RedirectResponse, ORJSONResponse

from utils.constants import *



class DateFormatOption:
    ISO = "iso"  # 기본 ISO 형식 (2023-01-01T12:00:00)
    FLASK = "flask"  # Flask 스타일 (Sat, 01 Jan 2023 12:00:00 GMT)
    DATE_ONLY = "date_only"  # 날짜만 (2023-01-01)

@dataclass
class ResponseModel:
    code: int = None
    data: Any = None
    message: str = None
    date_format: str = "flask"

    def to_dict(self):
        return {
            "code": self.code,
            "data": self._format_dates(self.data),
            "message": self.message
        }

    def to_orjson(self):
        # 표준 HTTP 범위의 code 만 상태코드로 싣고, 사내 코드(998/999/9000대)는 200 으로 내보낸다
        status_code = self.code if isinstance(self.code, int) and 100 <= self.code <= 599 else 200
        return ORJSONResponse(
            status_code=status_code,
            content=self.to_dict(),
        )

    # same as flask_style_datetime
    def _format_dates(self, obj):
        if isinstance(obj, datetime):
            if self.date_format == DateFormatOption.FLASK:
                return format_datetime(obj)
            elif self.date_format == DateFormatOption.DATE_ONLY:
                return obj.strftime("%Y-%m-%d")
            else:  # ISO
                return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._format_dates(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._format_dates(item) for item in obj]
        return obj


@dataclass
class Response200(ResponseModel):
    code: int = 200
    def __post_init__(self):
        self.code = 200

@dataclass
class Response500(ResponseModel):
    code: int = 500
    def __post_init__(self):
        self.code = 500

@dataclass
class Response400(ResponseModel):
    code: int = 400
    def __post_init__(self):
        self.code = 400

@dataclass
class Response401(ResponseModel):
    code: int = 401
    def __post_init__(self):
        self.code = 401

@dataclass
class Response402(ResponseModel):
    code: int = 402
    def __post_init__(self):
        self.code = 402

@dataclass
class Response403(ResponseModel):
    code: int = 403
    def __post_init__(self):
        self.code = 403

@dataclass
class Response404(ResponseModel):
    code: int = 404
    def __post_init__(self):
        self.code = 404

@dataclass
class Response405(ResponseModel):
    code: int =405
    def __post_init__(self):
        self.code = 405

@dataclass
class Response998(ResponseModel):
    code: int = 998
    def __post_init__(self):
        self.code = NOT_ABLE_DELETE_CATEGORY_CODE

@dataclass
class Response999(ResponseModel):
    code: int = 999
    def __post_init__(self):
        self.code = OVER_TOKEN_SIZE_CODE

@dataclass
class Response9000(ResponseModel):
    code: int = 9000
    def __post_init__(self):
        self.code = 9000

@dataclass
class Response9001(ResponseModel):
    code: int = 9001
    def __post_init__(self):
        self.code = 9001

@dataclass
class Response9002(ResponseModel):
    code: int = 9002
    def __post_init__(self):
        self.code = 9002

@dataclass
class Response9003(ResponseModel):
    code: int = 9003
    def __post_init__(self):
        self.code = 9003

@dataclass
class Response9004(ResponseModel):
    code: int = 9004
    def __post_init__(self):
        self.code = 9004

@dataclass
class Response9005(ResponseModel):
    code: int = 9005
    def __post_init__(self):
        self.code = 9005


def redirect(url: str, status_code: int = None):
    return RedirectResponse(url=url, status_code=status_code or 307)
