import ast
import time
from uuid import uuid4
from datetime import datetime
from dateutil.relativedelta import relativedelta
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt import create_token
from client.redis import RedisClient
from client.groxy import LLMProxyClient
from queries.company_info import CompanyInfoQuery
from queries.chat_history import ChatHistoryQuery
from payload.playground import *
from domain.playground import *
from module.LLM.agent import agent_make_title
from utils.error import *
from utils.date import *




def helper_chat_checking_payload_and_user_info(domain_data:chatDomain):
    # user_info data
    company_key = domain_data.company_key
    session_key = domain_data.session_key
    credit_available = domain_data.credit_available
    vector_db_index = domain_data.vector_db_index
    vector_db_namespace = domain_data.vector_db_namespace
    question = domain_data.question

    # make error
    if domain_data.plan_info_id == EXPIRED_PLAN_INFO_ID:
        raise ExpiredPlanChatError
    if credit_available == 0:
        raise NoCreditError
    if not question:
        raise NoQuestionError
    if not company_key or not session_key or not vector_db_index or not vector_db_namespace or not credit_available or not domain_data.plan_info_id:
        raise InvalidTokenError
    if not isinstance(credit_available, int) or not isinstance(vector_db_index, str) or not isinstance(vector_db_namespace, str) or not isinstance(session_key, str) or not isinstance(company_key, str) or not isinstance(question, str):
        logging.info(f"[helper.playground.helper_chat_checking_payload_and_user_info] Invalid data: credit_available: {type(credit_available)}, vector_db_index: {type(vector_db_index)}, vector_db_namespace: {type(vector_db_namespace)}, session_key: {type(session_key)}, company_key: {type(company_key)}, question: {type(question)}")
        raise DataError


def helper_chat_make_domain_data(
    payload:chatPayload,
    user_info:dict,
    server_stage:str
) -> chatDomain:
    try:
        # set args
        session_key = user_info["session_key"] if not payload.is_mcp else f"mcp_{user_info['session_key']}"
        payload.info['session_key'] = session_key
        payload.info['company_key'] = user_info["company_key"]
        payload.info['init_date'] = get_utc_now()

        # set service
        if server_stage == DOCKER:
            service = SERVICE_LLM_PLATFORM_INSTALL
        elif server_stage == REAL:
            service = SERVICE_LLM_PLATFORM_REAL
        else:
            service = SERVICE_LLM_PLATFORM_STAGING

        result = chatDomain(
            service=service,
            vendor=payload.vendor or BASE_VENDOR if not payload.is_mcp else BASE_MCP_VENDOR,
            model=payload.model or BASE_MODEL if not payload.is_mcp else BASE_MCP_MODEL,
            question=payload.question,
            lang=payload.lang or KOREAN,
            answer_id=str(uuid4()).replace("-", ""),
            session_key=session_key,
            company_key=user_info["company_key"],
            vector_db_index=user_info["vector_db_index"],
            vector_db_namespace=user_info["vector_db_namespace"],
            credit_available=user_info["credit_available"],
            plan_info_id=user_info["plan_info_id"],
            info=payload.info,
            start_time=time.time(),
            is_mcp=True if payload.is_mcp else False,
            store_name=user_info["store_name"],
            file_id=payload.file_id
        )

        # for fileSearch
        if result.store_name:
            result.vendor = GOOGLE
            result.model = GOOGLE_MODEL_LIST[0]

        return result

    except DataError as e:
        logging.error(f"[helper.playground.helper_chat_make_domain_data] DataError: {e}")
        raise DataError(e)
    except Exception as e:
        logging.error(f"[helper.playground.helper_chat_make_domain_data] Exception: {e}")
        raise Exception(e)


async def helper_chat_change_args_data_for_proxy(db:AsyncSession, company_info_query:CompanyInfoQuery, domain_data:chatDomain):
    try:
        domain_data.model = domain_data.model or await company_info_query.get_model(db=db, company_key=domain_data.company_key)
        domain_data.vector_db_embedding_model = EMBEDDING_MODEL if domain_data.model in OPENAI_MODEL_LIST else BEDROCK_EMBEDDING_MODEL
    except DBError:
        logging.info("[helper.playground.helper_chat_change_args_data_for_proxy] DBError: can't get model from company_info_table")
        raise LLMModuleError
    except Exception as e:
        logging.info(f"[helper.playground.helper_chat_change_args_data_for_proxy] DBError: can't get model from company_info_table: {e}")
        raise LLMModuleError


async def helper_get_retrieval_data_getting_source_data_ids(db:AsyncSession, chat_history_query:ChatHistoryQuery, payload:retrievalPayload, user_info:dict, server_stage: str):
    """
    - refer_id_str = "[1, 2, 3, 4]" string list -> ["1", "2", "3", "4"] list
    - parser_id_str = "[1, 2, 3, 4]" string list -> ["1", "2", "3", "4"] list
    - question_id_str = "snsjj-2jsd" string uuid4 -> same
    """
    try:
        refer_id_str, parser_id_str, email_id_str, sitemap_id_str, question_id_str, mcp_tools_str = await chat_history_query.get_refer_id(db=db, id=payload.id)
        refer_ids = [str(id) if isinstance(id, int) else id for id in ast.literal_eval(refer_id_str)] if refer_id_str else []
        parser_ids = [str(id) if isinstance(id, int) else id for id in ast.literal_eval(parser_id_str)] if parser_id_str else []
        email_ids = [str(id) if isinstance(id, int) else id for id in ast.literal_eval(email_id_str)] if email_id_str else []
        sitemap_ids = [str(id) if isinstance(id, int) else id for id in ast.literal_eval(sitemap_id_str)] if sitemap_id_str else []
        mcp_tools = ast.literal_eval(mcp_tools_str) if mcp_tools_str else []
        return retrievalDomain(
            user_id=user_info['user_id'],
            server_stage=server_stage,
            refer_ids=refer_ids,
            parser_ids=parser_ids,
            email_ids=email_ids,
            sitemap_ids=sitemap_ids,
            question_id_str=question_id_str,
            mcp_tools=mcp_tools
        )

    except DBError as e:
        logging.info(f"[helper.playground.helper_get_retrieval_data_getting_source_data_ids] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.playground.helper_get_retrieval_data_getting_source_data_ids] Exception: {e}")
        raise Exception(e)


async def helper_get_conversation_history_reform(db:AsyncSession, chat_history_query:ChatHistoryQuery, history_data:list):
    try:
        answer_ids = [item['id'] for item in history_data if item['role'] == 'ai']
        conversation_data_list = await chat_history_query.get_conversation_data(db=db, id=answer_ids)
        data = _reform_history_data(data=history_data, answer_ids=answer_ids, conversation_data_list=conversation_data_list)
        return data
    except DBError as e:
        logging.info(f"[helper.playground.helper_get_conversation_history_reform] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.playground.helper_get_conversation_history_reform] Exception: {e}")
        raise Exception(e)


def helper_get_chat_history_title_domain_data(user_info:dict, query_params:getConversationHistoryTitleQueryParams) -> getConversationHistoryTitleDomain:
    try:
        # get params
        info = query_params.dict()

        # set date
        start_date = string_to_datetime(info.get("start_date"), "UTC") if info.get("start_date") else None
        start_date_local = adapt_timezone_str_to_datetime(info.get("start_date", None), info.get("timezone", "Asia/Seoul")) if info.get("start_date") else None
        end_date = get_last_hour_of_day(info.get("end_date"), "UTC") if info.get("end_date") else None

        # result
        return getConversationHistoryTitleDomain(
            company_key=user_info["company_key"],
            asker_id=user_info["user_id"],
            manager_id=info.get("manager_id"),
            issue_status=info.get("issue_status"),
            page=int(info.get("page", 1)),
            per_page=int(info.get("per_page", 10)),
            start_date=start_date,
            end_date=end_date,
            timezone=info.get("timezone", "Asia/Seoul"),
            start_date_local=start_date_local
        )
    except Exception as e:
        logging.error(f"[helper.playground.helper_get_chat_history_title_query_data] Exception: {e}")
        raise DataError(e)


async def helper_get_session_list_and_count(db:AsyncSession, chat_history_query:ChatHistoryQuery, domain_data:getConversationHistoryTitleDomain):
    try:
        session_list, session_count = await chat_history_query.get_session_list(
            db=db,
            domain_data=domain_data
        )
        domain_data.session_list = session_list
        domain_data.session_count = session_count
    except DBError as e:
        logging.error(f"[helper.playground.helper_get_session_list_and_count] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.playground.helper_get_session_list_and_count] Exception: {e}")
        raise e


async def helper_get_chat_history_title(db:AsyncSession, chat_history_query:ChatHistoryQuery, domain_data:getConversationHistoryTitleDomain):
    try:
        # get chat history by session_key
        domain_data.chat_history_rows = await chat_history_query.get_chat_history_by_session_list(
            db=db,
            domain_data=domain_data
        )
        # reform rows for frontend
        _reform_chat_history_data(domain_data=domain_data)

    except DBError as e:
        logging.error(f"[helper.playground.helper_get_chat_history_title] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.playground.helper_get_chat_history_title] Exception: {e}")
        raise e


def _reform_chat_history_data(domain_data:getConversationHistoryTitleDomain):
    """session_key 기준으로 묶어서 표기"""
    try:
        if not domain_data.chat_history_rows:
            domain_data.rows = []
        else:
            middle = dict()
            result = list()
            session_key_checker = set()
            for data in domain_data.chat_history_rows:
                row = dict()
                if data["session_key"] in session_key_checker:
                    if data["reg_date"] < middle[data['session_key']]['date']:
                        middle[data['session_key']]['date'] = data["reg_date"]
                        middle[data['session_key']]['title'] = data.get("chat_title") or data["message"] if data["role"] == "human" else ""
                else:
                    session_key_checker.add(data["session_key"])
                    row["sessionKey"] = data["session_key"]
                    row["date"] = data["reg_date"]
                    row["title"] = data.get("chat_title") or data["message"] if data["role"] == "human" else ""

                    middle[data['session_key']] = row

            for value in middle.values():
                if not domain_data.start_date_local or change_local_datetime(value["date"], domain_data.timezone) >= domain_data.start_date_local:
                    result.append(value)

            result.sort(key=lambda x: x["date"], reverse=True)
            domain_data.rows = result

    except Exception as e:
        logging.error(f"[helper.playground._reform_chat_history_data] Exception: {e}")
        raise Exception(e)


async def helper_get_greetings_data(db:AsyncSession, company_info_query:CompanyInfoQuery, domain_data:getGreetingsDomain):
    try:
        domain_data.greetings = await company_info_query.get_greetings(db=db, domain_data=domain_data)
        if not domain_data.greetings:
            domain_data.greetings = INIT_GREETING_EN if domain_data.lang == ENGLISH else INIT_GREETING_JA if domain_data.lang == JAPANESE else INIT_GREETING_KO

    except DBError as e:
        logging.info(f"[helper.playground.helper_get_greetings_data] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.playground.helper_get_greetings_data] Exception: {e}")
        raise Exception(e)


def helper_new_chat_update_session_key_in_user_info_and_return_identity(domain_data:newChatDomain) -> str:
    try:
        user_id = domain_data.user_id
        session_key = str(uuid4()).replace("-", "")
        domain_data.identity = str({
            "user_id": user_id,
            "session_key": session_key
        })
    except Exception as e:
        logging.error(f"[helper.playground.helper_new_chat_update_session_key_in_user_info_and_return_identity] Exception: {e}")
        raise Exception(e)


def helper_new_chat_make_token_response_data(domain_data:newChatDomain):
    access_token, refresh_token = create_token(sub=domain_data.identity)
    domain_data.access_token = access_token
    domain_data.refresh_token = refresh_token


def helper_get_chat_title_make_domain_data(user_info:dict, server_stage:str):
    if server_stage == DOCKER:
        service = "llm-platform-install"
    elif server_stage == REAL:
        service = "llm-platform-production"
    else:
        service = "llm-platform-staging"

    return getChatTitleDomain(
        session_key=user_info["session_key"],
        user_id=user_info["user_id"],
        company_key=user_info["company_key"],
        service=service
    )


def helper_get_tools_by_session_key_and_answer_id(domain_data: GetMcpToolsDomain):
    for row in domain_data.history_data:
        if row.get("mcp_tools") and row["id"] == domain_data.answer_id:
            domain_data.response = {"tools": row["mcp_tools"]}
        else:
            domain_data.response = {"tools": []}


async def make_title_response_with_llm(llm_proxy_client:LLMProxyClient, domain_data:getChatTitleDomain):
    chat_history = [
        {
            "role": row['role'],
            "message": row['message']
        } for row in domain_data.row
    ]
    async for chunk in agent_make_title(llm_proxy_client=llm_proxy_client, chat_history=chat_history, service=domain_data.service):
        yield chunk


def _reform_history_data(data:list, answer_ids:list, conversation_data_list:list):
    for item in data:
        if item.get('id') in answer_ids:
            for rating in conversation_data_list:
                if item.get('id') == rating.get('id'):
                    item['rating'] = rating.get('rating')
                    item['comment'] = rating.get('memo')
    return data


def get_last_day_of_month(time: datetime):
    return time.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)


async def make_title_response(title:str):
    if title:
        for chunk in title:
            await asyncio.sleep(0.025)
            yield chunk
    else:
        yield ""


async def get_history_data_and_set_to_redis(db:AsyncSession, memory_db_client:RedisClient, chat_history_query:ChatHistoryQuery, domain_data:getConversationHistoryDomain | setHistoryDomain):
    try:
        rows = await chat_history_query.get_chat_history_by_session_key(db=db, domain_data=domain_data)

        # temp for mcp test ====================================
        if rows and domain_data.is_mcp:
            rows = [row for row in rows if row.get("is_mcp")]
        elif rows and not domain_data.is_mcp:
            rows = [row for row in rows if not row.get("is_mcp")]
        else:
            rows = None
        # temp for mcp test ====================================

        if rows:
            await memory_db_client.delete(key=domain_data.session_key) # 기존 데이터 삭제
            conversation_history = []
            for row in rows:
                data = {
                    "id": row['id'],
                    "role": row['role'],
                    "message": row['message'],
                    "rating": row['rating'],
                    "comment": row['memo']
                }
                if domain_data.is_mcp and row.get("is_mcp") and row.get("mcp_tools"):
                    data["mcp_tools"] = row["mcp_tools"]
                await memory_db_client.rpush(key=domain_data.session_key, value=str(data))
                conversation_history.append(data)

        else:
            conversation_history = []

        domain_data.conversation_history = conversation_history

    except DBError as e:
        logging.info(f"[helper.playground.get_history_data_and_set_to_redis] DBError: {e}")
        raise DBError(e)
    except MemoryDBError as e:
        logging.info(f"[helper.playground.get_history_data_and_set_to_redis] MemoryDBError: {e}")
        raise MemoryDBError
    except Exception as e:
        logging.error(f"[helper.playground.get_history_data_and_set_to_redis] Exception: {e}")
        raise Exception(e)


async def helper_update_conversation_history_data_save_to_redis(memory_db_client:RedisClient, domain_data:updateConversationHistoryDomain):
    try:
        await memory_db_client.delete(key=domain_data.session_key)
        for data in domain_data.history_data:
            if data.get("role") == "ai" and data.get("id") == domain_data.id and domain_data.memo:
                data["comment"] = domain_data.memo
            if data.get("role") == "ai" and data.get("id") == domain_data.id and domain_data.rating:
                data["rating"] = domain_data.rating
            await memory_db_client.rpush(key=domain_data.session_key, value=str(data))
    except Exception as e:
        logging.error(f"[helper.playground.helper_update_conversation_history_data_save_to_redis] Exception: {e}")
        raise Exception(e)


def helper_set_history_make_token(domain_data:setHistoryDomain):
    session_key = domain_data.session_key
    user_id = domain_data.user_id
    identity = str({'session_key':session_key, 'user_id': user_id})
    access_token, refresh_token = create_token(identity=identity)
    domain_data.access_token = access_token
    domain_data.refresh_token = refresh_token


async def make_error_message(streaming:bool=True, **kwargs):
    """
    make streaming error message
    """
    message = ""
    if kwargs.get("ExpiredPlanChatError"):
        message = "현재 적용된 플랜이 없습니다.\n관리자에게 문의 바랍니다."

    if kwargs.get("InvalidTokenError"):
        message = "잘못된 사용자 정보입니다. 다시 로그인해주세요."

    if kwargs.get("NoQuestionError"):
        message = "질문을 입력해주세요."

    if kwargs.get("NoCreditError"):
        message = "잔여 질문이 없습니다.\n플랜을 업그레이드하시거나 충전하시기 바랍니다.\n관리자에게 문의 바랍니다."

    if kwargs.get("LLMError"):
        message = "죄송합니다. 에러가 발생해 답변을 제공할 수 없습니다. 계속 같은 메세지를 받으신다면 담당자에게 연락주시면 감사하겠습니다."

    if streaming:
        for m in message:
            await asyncio.sleep(0.025)
            yield m
    else:
        yield message
