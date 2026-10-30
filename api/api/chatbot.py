from fastapi import APIRouter, Depends

from models import get_db, close_db
from response.streaming import *
from helper.chatbot import *



router = APIRouter(
    prefix="/chatbot",
    tags=["chatbot"],
)



@router.post("/check_chatbot_key")
@handle_errors()
async def check_chatbot_key(payload: checkChatbotKeyPayload):
    # set client
    memory_db_client = RedisClient()

    # business logic
    domain_data:checkChatbotKeyDomain = checkChatbotKeyDomain(chatbot_key=payload.chatbot_key)
    await helper_check_chatbot_key(memory_db_client=memory_db_client, domain_data=domain_data)

    # make response and return
    return Response200(data={"isLive": domain_data.is_live}).to_dict()


@router.get("/get_chatbot_key")
@handle_errors()
async def get_chatbot_key():
    return Response200(data={"chatbotKey": str(uuid4()).replace("-", "")}).to_dict()


@router.post("/chat")
async def chat(
    request: Request,
    payload: chatPayload,
    db:AsyncSession = Depends(get_db),
    response:ResponseQueue = Depends(get_response_queue)
):
    try:
        # server stage
        server_stage = os.getenv("SERVER_STAGE", "development")

        # check request from white list
        referer = request.headers.get("referer")
        if referer not in CHATBOT_ALLOW:
            logging.info(f"==================== NOT ALLOWED REFERER: {referer}")
            raise NoChatbotRefererError(str(referer))

        # make domain data
        company_info_query = CompanyInfoQuery()
        domain_data:chatDomain = await helper_chat_making_args(db, company_info_query, payload, server_stage)
        await close_db(db)

        # set client
        domain_data.llm_proxy_client = LLMProxyClient()
        domain_data.main_db_client = MySQLClient()
        domain_data.vector_db_client = PineconeClient(index_name=domain_data.vector_db_index, namespace=domain_data.vector_db_namespace) if server_stage != DOCKER else MilvusClient(collection_name=f"_{domain_data.vector_db_namespace}")
        domain_data.memory_db_client = RedisClient()
        domain_data.s3_client = S3Client()

        # business logic
        logging.info(f"session_key: {domain_data.session_key} | ==================== START Analysis model: {domain_data.model}")
        logging.info(f"session_key: {domain_data.session_key} | ==================== START Analysis question: {domain_data.question}")
        logging.info(f"session_key: {domain_data.session_key} | ==================== START Analysis answer_id: {domain_data.answer_id}")
        logging.info(f"session_key: {domain_data.session_key} | ==================== START Analysis session_key: {domain_data.session_key}")
        logging.info(f"session_key: {domain_data.session_key} | ==================== START Analysis company_key: {domain_data.company_key}")
        logging.info(f"session_key: {domain_data.session_key} | ==================== START Analysis pinecone_index: {domain_data.vector_db_index}")
        logging.info(f"session_key: {domain_data.session_key} | ==================== START Analysis pinecone_namespace: {domain_data.vector_db_namespace}")
        logging.info(f"session_key: {domain_data.session_key} | ==================== START Analysis info: {domain_data.info}")
        return await streaming_response(
            response=response,
            generator=RunLLM(args=domain_data).activate(),
            answer_id=domain_data.answer_id,
            start_time=domain_data.start_time,
            session_key=domain_data.session_key
        )

    except NoChatbotRefererError as e:
        logging.info(f"session_key: {payload.chatbot_key} | [api.chatbot.chat] 🔴 NoChatbotRefererError: {e} is Not ALLOWED Referer")
        return await streaming_response(
            response=response,
            generator=make_error_message(streaming=payload.streaming, **{"referer": True}),
            is_error=True
        )

    except ExpiredPlanChatError as e:
        logging.info(f"session_key: {payload.chatbot_key} | [api.chatbot.chat] 🔴 ExpiredPlanChatError: {e}")
        return await streaming_response(
            response=response,
            generator=make_error_message(streaming=payload.streaming, **{"ExpiredPlanChatError": True}),
            is_error=True
        )
    except NoCreditError as e:
        logging.info(f"session_key: {payload.chatbot_key} | [api.chatbot.chat] 🔴 NoCreditError: {e}")
        return await streaming_response(
            response=response,
            generator=make_error_message(streaming=payload.streaming, **{"NoCreditError": True}),
            is_error=True
        )
    except InvalidTokenError as e:
        logging.info(f"session_key: {payload.chatbot_key} | [api.chatbot.chat] 🔴 InvalidTokenError: {e}")
        return await streaming_response(
            response=response,
            generator=make_error_message(streaming=payload.streaming, **{"InvalidTokenError": True}),
            is_error=True
        )
    except DataError as e:
        logging.info(f"session_key: {payload.chatbot_key} | [api.chatbot.chat] 🔴 Exception: {e}")
        return await streaming_response(
            response=response,
            generator=make_error_message(streaming=payload.streaming, **{"LLMError": True}),
            is_error=True
        )
    except Exception as e:
        logging.info(f"session_key: {payload.chatbot_key} | [api.chatbot.chat] 🔴 Exception: {e}")
        return await streaming_response(
            response=response,
            generator=make_error_message(streaming=payload.streaming, **{"LLMError": True}),
            is_error=True
        )


@router.post("/get_conversation_history")
@handle_errors()
async def get_conversation_history(
    request: Request,
    payload: getConversationHistoryPayload,
    db:AsyncSession = Depends(get_db)
):
    # data
    domain_data = getConversationHistoryDomain(session_key=payload.session_key)

    # set client
    memory_db_client = RedisClient()
    chat_history_query = ChatHistoryQuery()

    # business logic
    await helper_get_conversation_history(
        db=db,
        memory_db_client=memory_db_client,
        chat_history_query=chat_history_query,
        RunLLM=RunLLM,
        domain_data=domain_data
    )

    # make response and return
    domain_data.history_data = reform_history_data(domain_data=domain_data)
    return Response200(data=domain_data.history_data).to_dict()
