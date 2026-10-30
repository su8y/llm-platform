import os
import logging
from functools import wraps

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, ORJSONResponse

from .constants import *
from .response import *


SUCCESS_CODE = 200
FAIL_CODE = 500
INVALID_DATA_CODE = 400


def handle_errors():
    def decorator(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            try:
                return await f(*args, **kwargs)

            # Token Error
            except OverTokenError as e:
                logging.error(f"[OverTokenError] ::: {e.message}")
                return ORJSONResponse(
                    status_code=500,
                    content=Response500(message="[OverTokenError] ::: Over Token Size").to_dict()
                )

            # client Error
            except AWSError as e:
                logging.error(f"[AWSError] ::: {e.message}")
                return ORJSONResponse(
                    status_code=500,
                    content=Response500(message="[AWSError] ::: AWS Error").to_dict()
                )

            except VectorDBError as e:
                logging.error(f"[VectorDBError] ::: {e.message}")
                return ORJSONResponse(
                    status_code=500,
                    content=Response500(message="[VectorDBError] ::: Vector DB Error").to_dict()
                )

            except MailSourceError as e:
                logging.error(f"[MailSourceError] ::: {e.message}")
                return ORJSONResponse(
                    status_code=400,
                    content=Response400(message=f"[MailSourceError] ::: {e.message}").to_dict()
                )
            except DBError as e:
                logging.error(f"[DBError] ::: {e.message}")
                return ORJSONResponse(
                    status_code=500,
                    content=Response500(message="[DBError] ::: DB Error").to_dict()
                )

            except MemoryDBError as e:
                logging.error(f"[MemoryDBError] ::: {e.message}")
                return ORJSONResponse(
                    status_code=500,
                    content=Response500(message="[MemoryDBError] ::: Memory DB Error").to_dict()
                )

            # route side Error
            except ForbiddenError as e:
                logging.error(f"[ForbiddenError] ::: {e.message}")
                return ORJSONResponse(
                    status_code=403,
                    content=Response403(message="[ForbiddenError] ::: Forbidden Error").to_dict()
                )

            except DataError as e:
                logging.error(f"[DataError] ::: {e.message}")
                return ORJSONResponse(
                    status_code=400,
                    content=Response400(message="[DataError] ::: Data Error").to_dict()
                )

            except AlreadyExistsIDError as e:
                logging.info(f"[AlreadyExistsIDError] ::: {e.message}")
                return Response9000(message="[AlreadyExistsIDError] ::: Already Exists ID").to_dict()

            except AlreadyExistsEmailError as e:
                logging.info(f"[AlreadyExistsEmailError] ::: {e.message}")
                return Response9001(message="[AlreadyExistsEmailError] ::: Already Exists Email").to_dict()

            except AlreadyExistsCompanyNameError as e:
                logging.info(f"[AlreadyExistsCompanyNameError] ::: {e.message}")
                return Response9002(message="[AlreadyExistsCompanyNameError] ::: Already Exists Company Name").to_dict()

            except NotValidatedFindPasswordError as e:
                path = "signin?changePassword=false"
                # path = "login/?changePassword=false"
                url = REAL_URL if os.getenv("SERVER_STAGE") == REAL else STAGING_URL if os.getenv("SERVER_STAGE") == STAGING else DEV_URL
                redirect_url = url + path
                logging.error(f"[NotValidatedFindPasswordError] ::: {e}")
                logging.error(f"[NotValidatedFindPasswordError] ::: redirect_url: {redirect_url}")
                return redirect(redirect_url)

            except NotFoundUserError as e:
                logging.error(f"[NotFoundUserError] ::: {e.message}")
                return Response402(message="[NotFoundUserError] ::: Not Found User").to_dict()

            except NotFoundPasswordError as e:
                logging.error(f"[NotFoundPasswordError] ::: {e.message}")
                return Response403(message="[NotFoundPasswordError] ::: Not Found Password").to_dict()

            except NotCertifiError as e:
                logging.error(f"[NotCertifiError] ::: {e.message}")
                return Response405(message="[NotCertifiError] ::: Not Certifi").to_dict()

            except NoCreditError as e:
                logging.error(f"[NoCreditError] ::: {e.message}")
                return Response200(message="[NoCreditError] ::: No Credit").to_dict()

            except LLMModuleError as e:
                logging.error(f"[LLMModuleError] ::: {e.message}")
                return Response200(message="[LLMModuleError] ::: LLM Module Error").to_dict()

            except WrongEmailTypeError as e:
                logging.info(f"[WrongEmailTypeError] ::: {e.message}")
                return Response9003(message="[WrongEmailTypeError] ::: Wrong Email Type").to_dict()

            except ExpiredPlanChatError as e:
                logging.error(f"[ExpiredPlanChatError] ::: {e.message}")
                return Response200(message="[ExpiredPlanChatError] ::: Expired Plan Chat").to_dict()

            except ExpiredPlanError as e:
                logging.error(f"[ExpiredPlanError] ::: {e.message}")
                return Response200(message="[ExpiredPlanError] ::: Expired Plan").to_dict()

            except LLMStreamingError as e:
                logging.error(f"[LLMStreamingError] ::: {e.message}")
                return Response200(message="[LLMStreamingError] ::: LLM Streaming Error").to_dict()

            except TokenError as e:
                logging.error(f"[TokenError] ::: {e.message}")
                return Response401(message="[TokenError] ::: Token Error").to_orjson()

            except HasThreadError:
                logging.info(f"[HasThreadError] ::: User requests an answer to an email that already has a thread.")
                return Response9005(message="[HasThreadError] ::: Has Thread Error").to_dict()

            except Exception as e:
                logging.error(f"[Exception] ::: {e}")
                return JSONResponse(
                    status_code=500,
                    content=Response500(message="[Exception] ::: Exception").to_dict()
                )
        return decorated_function
    return decorator


class AppError(Exception):

    def __init__(self, message=None, code=None, status=None):
        super().__init__()
        self.message = message or "Message"
        self.code = code or 500
        self.status = status or "ERROR"

    def to_dict(self):
        return {
            "message": self.message,
            "status": self.status,
            "code": self.code
        }

class LLMProxyError(AppError):

    def __init__(self, message="LLM proxy error occurred"):
        super().__init__(message=message, code=FAIL_CODE)


class AWSError(AppError):

    def __init__(self, message="AWS error occurred"):
        super().__init__(message=message, code=FAIL_CODE)


class MessageQueueError(AppError):

    def __init__(self, message="Message queue error occurred"):
        super().__init__(message=message, code=FAIL_CODE)


class VectorDBError(AppError):

    def __init__(self, message="Vector database error occurred"):
        super().__init__(message=message, code=FAIL_CODE)


class DBError(AppError):

    def __init__(self, message="Database error occurred"):
        super().__init__(message=message, code=FAIL_CODE)


class MemoryDBError(AppError):

    def __init__(self, message="Memory database error occurred"):
        super().__init__(message=message, code=FAIL_CODE)


class DataError(AppError):

    def __init__(self, message="Invalid data provided"):
        super().__init__(message=message, code=INVALID_DATA_CODE)


class OverTokenError(AppError):

    def __init__(self, message="is over token size"):
        super().__init__(message=message, code=SUCCESS_CODE)


class InvalidTokenError(AppError):

    def __init__(self, message="Invalid Token"):
        super().__init__(message=message, code=SUCCESS_CODE)


class NoQuestionError(AppError):

    def __init__(self, message="No Question"):
        super().__init__(message=message, code=SUCCESS_CODE)


class NoChatbotKeyError(AppError):

    def __init__(self, message="No Chatbot Key"):
        super().__init__(message=message, code=SUCCESS_CODE)


class NoChatbotRefererError(AppError):

    def __init__(self, message="No Chatbot Referer"):
        super().__init__(message=message, code=SUCCESS_CODE)


class ParserCreditAvailableOverError(AppError):

    def __init__(self, message="Parser Credit Available Over"):
        super().__init__(message=message, code=SUCCESS_CODE)


class ExpiredPlanChatError(AppError):

    def __init__(self, message="Expired Plan"):
        super().__init__(message=message, code=SUCCESS_CODE)


class ExpiredPlanError(AppError):

    def __init__(self, message="Expired Plan"):
        super().__init__(message=message, code=SUCCESS_CODE)


class ForbiddenError(AppError):

    def __init__(self, message="Forbidden"):
        super().__init__(message=message, code=SUCCESS_CODE)


class LLMStreamingError(AppError):

    def __init__(self, message="LLM proxy streaming error occurred"):
        super().__init__(message=message, code=SUCCESS_CODE)


class AlreadyExistsIDError(AppError):

    def __init__(self, message="Already Exists ID"):
        super().__init__(message=message, code=ALREADY_ID_CODE)


class AlreadyExistsEmailError(AppError):

    def __init__(self, message="Already Exists Email"):
        super().__init__(message=message, code=ALREADY_EMAIL_CODE)


class AlreadyExistsCompanyNameError(AppError):

    def __init__(self, message="Already Exists Company Name"):
        super().__init__(message=message, code=ALREADY_COMPANY_NAME_CODE)


class NotValidatedFindPasswordError(AppError):

    def __init__(self, message="Not Validated Find Password"):
        super().__init__(message=message, code=SUCCESS_CODE)


class NotFoundUserError(AppError):

    def __init__(self, message="Not Found User"):
        super().__init__(message=message, code=NOT_FOUND_USER_CODE)


class NotFoundPasswordError(AppError):

    def __init__(self, message="Not Found Password"):
        super().__init__(message=message, code=NOT_FOUND_PASSWORD_CODE)


class NotCertifiError(AppError):

    def __init__(self, message="Not Certifi"):
        super().__init__(message=message, code=NOT_CERTIFIED_USER_CODE)


class NoCreditError(AppError):

    def __init__(self, message=PARSER_CREDIT_AVAILABLE_OVER_MESSAGE):
        super().__init__(message=message, code=SUCCESS_CODE)

class NotMCPAuthError(AppError):

    def __init__(self, message=PARSER_CREDIT_AVAILABLE_OVER_MESSAGE):
        super().__init__(message=message, code=SUCCESS_CODE)


class LLMModuleError(AppError):

    def __init__(self, message="LLM Module Error"):
        super().__init__(message=message, code=SUCCESS_CODE)


class WrongEmailTypeError(AppError):

    def __init__(self, message="Wrong Email Type"):
        super().__init__(message=message, code=WRONG_EMAIL_TYPE_CODE)


class TokenError(AppError):

    def __init__(self, message="Token Error"):
        super().__init__(message=message, code=401)


class MailSourceError(AppError):
    """IMAP / SES 등 메일 수신 소스 접속·조회 실패. 대부분 설정(호스트·계정·권한) 문제라 400 으로 응답한다"""
    def __init__(self, message="Mail source error occurred"):
        super().__init__(message=message, code=INVALID_DATA_CODE)


class HasThreadError(AppError):

    def __inti__(self, message="Already has Thread"):
        super().__init__(message=message, code=9005)


# global token error handler
def token_exception_handler(app: FastAPI):
    @app.exception_handler(TokenError)
    async def token_error_handler(request: Request, exc: TokenError):
        return JSONResponse(
            status_code=401,
            content={
                "res": {
                    "code": 401,
                    "message": str(exc),
                    "data": None
                }
            }
        )
