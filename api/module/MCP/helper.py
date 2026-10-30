import ast
import time
import asyncio
from datetime import timedelta
from uuid import uuid4
from pytz import timezone

from bs4 import BeautifulSoup

from client.redis import RedisClient
from client.mysql import MySQLClient

from domain.playground import chatDomain
from module.MCP.dto import MCPArgs
from utils.error import *


def make_mcpArgs(args:chatDomain) -> MCPArgs:
    """
    make llmArgs in order to seperated Action \n\n
    - redis_save:bool -> save conversation_history Y/n
    """
    try:
        return MCPArgs(
            service=args.service,
            vendor=args.vendor,
            model=args.model,
            question=args.question,
            answer_id=args.answer_id,
            session_key=args.session_key,
            company_key=args.company_key,
            credit_available=args.credit_available,
            info=args.info,
            start_time=args.start_time,
            llm_proxy_client=args.llm_proxy_client,
            main_db_client=args.main_db_client,
            memory_db_client=args.memory_db_client,
            s3_client=args.s3_client,
            redis_save=True,
            streaming=True,
            time_info={},
            mcp_token=args.mcp_token,
            is_mcp=args.is_mcp,
            chat_info={**args.info, **{"is_mcp": True}},
            lang=args.lang,
            store_name=args.store_name
        )
    except DataError as e:
        logging.error(f"[module.MCP.helper.make_mcpArgs] DataError: {e}")
        raise e
    except Exception as e:
        logging.error(f"[module.MCP.helper.make_mcpArgs] Exception: {e}")
        raise e


async def get_system_prompt(mcpArgs:MCPArgs):
    """
    get prompt from db.epic.prompt_history
    """
    try:
        prompt_result = await mcpArgs.main_db_client.fetch_one(
            query="""
                SELECT
                    id,
                    prompt
                FROM prompt_history
                WHERE company_key = %s
                ORDER BY reg_date DESC
                LIMIT 1
            """,
            params=(mcpArgs.company_key)
        )
        pid = prompt_result[0] if prompt_result else None
        prompt = prompt_result[1] if prompt_result else DEFAULT_PROMPT

        get_elapsed(mcpArgs, "ElapsedPromptMySQLQuery")

        return prompt, pid
    except DBError as e:
        logging.error(f"[module.MCP.helper.get_system_prompt] DBError: {e.message}")
        raise DBError(e.message)
    except Exception as e:
        logging.error(f"[module.MCP.helper.get_system_prompt] Exception: {e}")
        raise e


async def get_mcp_url_and_tools(mcpArgs:MCPArgs):
    try:
        prompt_result = await mcpArgs.main_db_client.fetch_one(
            query="""
                SELECT
                    mcp_server,
                    mcp_token,
                    mcp_allowed_tools
                FROM company_info
                WHERE company_key = %s
            """,
            params=(mcpArgs.company_key)
        )
        mcp_server = prompt_result[0] if prompt_result else None
        mcp_token = prompt_result[1] if prompt_result else None
        mcp_allowed_tools = prompt_result[2] if prompt_result else None

        get_elapsed(mcpArgs, "ElapsedMCPInfoMySQLQuery")

        return mcp_server, mcp_token, mcp_allowed_tools
    except DBError as e:
        logging.error(f"[module.MCP.helper.get_system_prompt] DBError: {e.message}")
        raise DBError(e.message)
    except Exception as e:
        logging.error(f"[module.MCP.helper.get_system_prompt] Exception: {e}")
        raise e



async def get_conversation_history(mcpArgs:MCPArgs):
    """get conversation history from Redis"""
    try:
        count = await mcpArgs.memory_db_client.llen(mcpArgs.session_key)
        if count == 0:
            conversations = []
        else:
            conversations = await mcpArgs.memory_db_client.lrange(mcpArgs.session_key, -40, -1)

        get_elapsed(mcpArgs, "ElapsedConvHistoryRedis")

        return decode_data_from_redis(conversations)

    except DBError as e:
        logging.error(f"[module.LLM.helper.get_conversation_history] DBError: {e}")
        raise DBError(e)
    except MemoryDBError as e:
        logging.error(f"[module.LLM.helper.get_conversation_history] MemoryDBError: {e}")
        raise MemoryDBError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_conversation_history] Exception: {e}")
        raise e


def decode_data_from_redis(list_data):
    """
    decode string data from redis -> dict
    """
    try:
        if len(list_data) == 0:
            result = []
        else:
            result = list(map(lambda string_data: ast.literal_eval(string_data), list_data))
        return result

    except Exception as e:
        logging.error(f"[module.LLM.helper.decode_data_from_redis] Exception: {e}")
        raise e


def redis_format(role, message, id=None, mcp_tools=None):
    """Redis input data format"""
    try:
        form = {
            "message": message,
            "role": role
        }
        if mcp_tools and role == "human":
            form["mcp_tools"] = mcp_tools
            form["id"] = id
        if id != None and role == "ai":
            form["id"] = id
            form["rating"] = None
        return str(form)
    except Exception as e:
        logging.error(f"[module.LLM.helper.redis_format] Exception: {e}")
        raise e


def make_chat_history_data(chat_info:dict, role:str, message:str, token:int, reg_date:datetime=None, id:str=None, elapsed_info:str=None):
    try:
        chat_info['reg_date'] = reg_date or datetime.now(timezone('UTC'))
        chat_info['issue_status'] = "needSolve"
        chat_info['role'] = role
        chat_info['message'] = message
        chat_info['id'] = id or str(uuid4()).replace("-", "")
        chat_info['token'] = token
        chat_info['elapsed_info'] = elapsed_info
        chat_info['is_mcp'] = True
        chat_info["mcp_tools"] = str(chat_info["mcp_tools"]) if chat_info.get("mcp_tools") else None
        chat_info["model"] = chat_info.get("model")
        return chat_info
    except Exception as e:
        logging.error(f"[module.LLM.helper.make_chat_history_data] Exception: {e}")
        raise e


async def record_credit_history(main_db_client:MySQLClient, company_key:str, credit_available:int, current_time:datetime):
    try:
        await main_db_client.execute(
            query="UPDATE payment SET use_credit = use_credit + 1 WHERE company_key = %s AND start_date <= %s AND end_date >= %s",
            params=(company_key, current_time, current_time)
        )

        row = await main_db_client.fetch_one(
            query="SELECT id FROM credit_history WHERE company_key = %s AND credit_type = %s AND DATE(reg_date) = DATE(%s);",
            params=(company_key, 0, current_time)
        )
        if row:
            credit_history_id = row[0]
            await main_db_client.execute(
                query="UPDATE credit_history SET credit = credit + 1, after_credit_available = after_credit_available - 1 WHERE id = %s",
                params=(credit_history_id)
            )
        else:
            payment_id_row = await main_db_client.fetch_one(
                query="SELECT id FROM payment WHERE company_key = %s AND start_date <= %s AND end_date >= %s",
                params=(company_key, current_time, current_time)
            )
            payment_id = payment_id_row[0]
            await main_db_client.execute(
                query="INSERT INTO credit_history (company_key, reg_date, credit_type, credit, after_credit_available, payment_id) VALUES (%s, %s, %s, %s, %s, %s)",
                params=(company_key, current_time, 0, 1, credit_available - 1, payment_id)
            )
    except DBError as e:
        logging.error(f"[module.LLM.helper.record_credit_history] DBError: {e}")
    except Exception as e:
        logging.error(e)
        # send_slack_message(message=f"[llm-platform-api][faild record_credit_history] {e}🫠", channel="#casual")


def make_human_message(question, retrieval_data=None, language_message=None):
    result = f"<{USER_QUESTION_NAME}>\n{question}\n</{USER_QUESTION_NAME}>"
    if retrieval_data:
        result = f"<{RAG_NAME}>\n{retrieval_data}\n</{RAG_NAME}>\n\n\n{result}"
    if language_message:
        result = result + f"\n\n\n<{LANG_NAME}>\n{language_message}\n</{LANG_NAME}>"
    return result


async def make_error_message_for_LLM(streaming:bool=True):
    try:
        message = "죄송합니다. 에러가 발생해 답변을 제공할 수 없습니다. 계속 같은 메세지를 받으신다면 담당자에게 연락주시면 감사하겠습니다."
        if streaming:
            for m in message:
                await asyncio.sleep(0.025)
                yield m
        else:
            yield message

    except Exception as e:
        logging.error(f"[module.LLM.helper.make_error_message] Exception: {e}")
        raise e


def get_elapsed(mcpArgs:MCPArgs, key:str):
    try:
        end_time = time.time()
        elapsed = timedelta(seconds=float(end_time - mcpArgs.start_time)).total_seconds()
        mcpArgs.time_info[key] = elapsed
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_elapsed] Exception: {e}")
        raise e


def write_log_for_debug_message(system_message=None, conversation_history=None, human_message=None):
    logging.info("*"*100)
    logging.info(f"[시스템 프롬프트] {system_message}")
    logging.info("*"*100)
    logging.info(f"[대화 이력] {conversation_history}")
    logging.info("*"*100)
    logging.info(f"[사용자 프롬프트] {human_message}")
    logging.info("*"*100)
