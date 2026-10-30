import logging
from uuid import uuid4
import time
from typing import Type

from sqlalchemy.ext.asyncio import AsyncSession

from client.redis import RedisClient
from queries.company_info import CompanyInfoQuery
from queries.chat_history import ChatHistoryQuery
from module.LLM.activate import RunLLM
from payload.chatbot import *
from domain.chatbot import *
from domain import playground
from utils.error import *
from utils.response import *
from utils.constants import *



async def helper_check_chatbot_key(memory_db_client:RedisClient, domain_data:checkChatbotKeyDomain):
    exists = await memory_db_client.exists(keys=[domain_data.chatbot_key])
    if exists:
        await memory_db_client.expire(key=domain_data.chatbot_key, time=1800)
        domain_data.is_live = True


async def helper_chat_making_args(db:AsyncSession, company_info_query:CompanyInfoQuery, payload:chatPayload, server_stage:str):
    try:
        model = payload.model
        question = payload.question
        if not question:
            raise NoQuestionError
        session_key = payload.chatbot_key
        if not session_key:
            raise NoChatbotKeyError
        pinecone_info = await company_info_query.get_pinecone_info(db, LLM_PLATFORM_CHATBOT_COMPANY_KEY)
        pinecone_index = pinecone_info.get("vector_db_index")
        pinecone_namespace = pinecone_info.get("vector_db_namespace")
        answer_id = str(uuid4()).replace("-", "")
        info = {"session_key": session_key, "company_key": LLM_PLATFORM_CHATBOT_COMPANY_KEY}
        domain_data = chatDomain(
            service="llm-platform-install" if server_stage == DOCKER else "llm-platform",
            vendor=BASE_VENDOR,
            model=model,
            question=question,
            answer_id=answer_id,
            session_key=session_key,
            company_key=LLM_PLATFORM_CHATBOT_COMPANY_KEY,
            credit_available=-1,
            vector_db_index=pinecone_index,
            vector_db_namespace=pinecone_namespace,
            info=info,
            start_time=time.time(),
        )
        if pinecone_namespace:
            domain_data.vector_db_namespace = pinecone_namespace
        
        return domain_data
    
    except NoQuestionError as nqe:
        logging.error(f"[api.helper.chatbot.helper_chat_making_args] NoQuestionError: {nqe}")
        raise NoQuestionError(nqe)
    except NoChatbotKeyError as ncke:
        logging.error(f"[api.helper.chatbot.helper_chat_making_args] NoChatbotKeyError: {ncke}")
        raise NoChatbotKeyError(ncke)
    except DBError as dbe:
        logging.error(f"[api.helper.chatbot.helper_chat_making_args] DBError: {dbe}")
        raise DBError(dbe)
    except Exception as e:
        logging.error(f"[api.helper.chatbot.helper_chat_making_args] Exception: {e}")
        raise Exception(e)


def reform_history_data(domain_data:getConversationHistoryDomain): # data:list, answer_ids:list, ratings_list:list
    for item in domain_data.history_data:
        if item.get('id') in domain_data.answer_ids:
            for rating in domain_data.ratings_list:
                if item.get('id') == rating.get('id'):
                    item['rating'] = rating.get('rating')
    return domain_data.history_data


def make_error_message(**kwargs):
    if kwargs.get("no_question"):
        message = "질문이 전달되지 않았습니다. 질문을 입력했는지 확인해주세요. 질문을 기입하고 요청을 했는데, 계속 같은 메세지가 나온다면 담당자에게 문의해주시길 바랍니다."
        for m in message:
            time.sleep(0.025)
            yield m

    if kwargs.get("page_name", None):
        message = "유효한 pathname이 아닙니다."
        for m in message:
            time.sleep(0.025)
            yield m

    if kwargs.get("exception", None):
        message = "알 수 없는 에러가 발생했습니다. 담당자에게 말씀해주시면 신속히 처리하겠습니다. 감사합니다."
        for m in message:
            time.sleep(0.025)
            yield m
    
    if kwargs.get("company_key", None):
        message = "ID가 없습니다. 서비스 등록을 완료했는데 계속 같은 메세지가 뜨면 담당자에게 연락해주시길 바랍니다"
        for m in message:
            time.sleep(0.025)
            yield m

    if kwargs.get("noRegis", None):
        message = "EPIC 서비스에 등록된 URL이 아닙니다. 담당자에게 연락해주시길 바랍니다."
        for m in message:
            time.sleep(0.025)
            yield m

    if kwargs.get("noCredit"):
        message = "현재 사용량이 많아 에러가 발생한 상황입니다. 관리자에게 말씀해주시면 신속히 처리하겠습니다. 죄송합니다."
        for m in message:
            time.sleep(0.025)
            yield m

    if kwargs.get("referer", None):
        message = "접근 권한이 없습니다. 만약, LLM Platform 화면인데 현재 메세지가 나온다면 관리자에게 말씀해주세요. 신속히 처리하겠습니다. 감사합니다."
        for m in message:
            time.sleep(0.025)
            yield m

    if kwargs.get("session_key", None):
        message = "접근 권한이 없습니다. 만약, LLM Platform 화면인데 현재 메세지가 나온다면 관리자에게 말씀해주세요. 신속히 처리하겠습니다. 감사합니다."
        for m in message:
            time.sleep(0.025)
            yield m
    
    if kwargs.get("LLMError", None):
        message = "에러가 발생했습니다. 담당자에게 말씀해주시면 신속히 처리하겠습니다. 감사합니다."
        for m in message:
            time.sleep(0.025)
            yield m

    
async def helper_get_conversation_history(db:AsyncSession, memory_db_client:RedisClient, chat_history_query:ChatHistoryQuery, RunLLM:Type[RunLLM], domain_data:getConversationHistoryDomain):
    try:
        if not domain_data.session_key:
            domain_data.history_data = []
        else:
            domain_data.history_data = await RunLLM.get_conversation_history(memory_db_client=memory_db_client, session_key=domain_data.session_key)
            domain_data.answer_ids = [item['id'] for item in domain_data.history_data if item['role'] == 'ai']
            domain_data.ratings_list = await chat_history_query.get_rating(db=db, id=domain_data.answer_ids) if domain_data.answer_ids else []
    
    except DBError as dbe:
        logging.error(f"[api.helper.chatbot.helper_get_conversation_history] DBError: {dbe}")
        raise DBError(dbe)
    except MemoryDBError as mde:
        logging.error(f"[api.helper.chatbot.helper_get_conversation_history] MemoryDBError: {mde}")
        raise MemoryDBError(mde)
    except Exception as e:
        logging.error(f"[api.helper.chatbot.helper_get_conversation_history] Exception: {e}")
        raise Exception(e)