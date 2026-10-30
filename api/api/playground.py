from fastapi import APIRouter, Depends

from queries.chat_title import ChatTitleQuery
from models import get_db, close_db
from auth.dependencies import get_user_info
from helper.playground import *
from payload.playground import *
from response.streaming import *
from module.LLM.activate import *
from module.MCP.activate import *



router = APIRouter(
    prefix="/playground",
    tags=["playground"],
)



@router.post("/chat")
async def chat(
    payload:chatPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db),
    response:ResponseQueue = Depends(get_response_queue)
):
    """ask Question and get 'STREAM' Answer"""
    logging.info(f"session_key: {user_info.get('session_key')} | [user_info] {user_info}")
    try:
        # check server stage
        server_stage = os.getenv("SERVER_STAGE", "development")

        # make domain_data
        domain_data:chatDomain = helper_chat_make_domain_data(
            payload=payload,
            user_info=user_info,
            server_stage=server_stage
        )

        # business logic
        helper_chat_checking_payload_and_user_info(domain_data)
        await helper_chat_change_args_data_for_proxy(db, CompanyInfoQuery(), domain_data)
        await close_db(db)

        # set Client
        domain_data.s3_client = S3Client()
        domain_data.llm_proxy_client = LLMProxyClient()
        domain_data.main_db_client = MySQLClient()
        domain_data.memory_db_client = RedisClient()
        if domain_data.service != SERVICE_LLM_PLATFORM_INSTALL:
            domain_data.vector_db_client = PineconeClient(
                index_name=domain_data.vector_db_index,
                namespace=domain_data.vector_db_namespace
            )
        else:
            domain_data.vector_db_client = MilvusClient(collection_name=f"_{domain_data.vector_db_namespace}")

        logging.info(f"session_key: {domain_data.session_key} | ==================== START Analysis model: {domain_data.model}")
        logging.info(f"session_key: {domain_data.session_key} | ==================== START Analysis question: {domain_data.question}")
        logging.info(f"session_key: {domain_data.session_key} | ==================== START Analysis answer_id: {domain_data.answer_id}")
        logging.info(f"session_key: {domain_data.session_key} | ==================== START Analysis session_key: {domain_data.session_key}")
        logging.info(f"session_key: {domain_data.session_key} | ==================== START Analysis company_key: {domain_data.company_key}")
        logging.info(f"session_key: {domain_data.session_key} | ==================== START Analysis vector_db_index: {domain_data.vector_db_index}")
        logging.info(f"session_key: {domain_data.session_key} | ==================== START Analysis vector_db_namespace: {domain_data.vector_db_namespace}")
        logging.info(f"session_key: {domain_data.session_key} | ==================== START Analysis info: {domain_data.info}")

        module = RunLLM(args=domain_data) if not domain_data.is_mcp else RunMCP(args=domain_data)

        return await streaming_response(
            response=response,
            generator=module.activate(),
            answer_id=domain_data.answer_id,
            start_time=domain_data.start_time,
            session_key=domain_data.session_key
        )

    except ExpiredPlanChatError as e:
        logging.error(f"session_key: {user_info.get('session_key')} | [api.playground.chat] 🔴 ExpiredPlanChatError: {e}")
        return await streaming_response(
            response=response,
            generator=make_error_message(streaming=payload.streaming, **{"ExpiredPlanChatError": True}),
            is_error=True
        )
    except NoCreditError as e:
        logging.error(f"session_key: {user_info.get('session_key')} | [api.playground.chat] 🔴 NoCreditError: {e}")
        return await streaming_response(
            response=response,
            generator=make_error_message(streaming=payload.streaming, **{"NoCreditError": True}),
            is_error=True
        )
    except InvalidTokenError as e:
        logging.error(f"session_key: {user_info.get('session_key')} | [api.playground.chat] 🔴 InvalidTokenError: {e}")
        return await streaming_response(
            response=response,
            generator=make_error_message(streaming=payload.streaming, **{"InvalidTokenError": True}),
            is_error=True
        )
    except DataError as e:
        logging.error(f"session_key: {user_info.get('session_key')} | [api.playground.chat] 🔴 Exception: {e}")
        return await streaming_response(
            response=response,
            generator=make_error_message(streaming=payload.streaming, **{"LLMError": True}),
            is_error=True
        )
    except Exception as e:
        logging.error(f"session_key: {user_info.get('session_key')} | [api.playground.chat] 🔴 Exception: {e}")
        return await streaming_response(
            response=response,
            generator=make_error_message(streaming=payload.streaming, **{"LLMError": True}),
            is_error=True
        )


@router.get("/get_chat_title")
@handle_errors()
async def get_chat_title(
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    server_stage = os.getenv("SERVER_STAGE", "development")

    # client
    llm_proxy_client = LLMProxyClient()
    chat_title_query = ChatTitleQuery()

    # business logic
    domain_data:getChatTitleDomain = helper_get_chat_title_make_domain_data(user_info, server_stage)
    domain_data.row = await chat_title_query.get_chat_title(db=db, domain_data=domain_data)
    if domain_data.row and isinstance(domain_data.row, list) and len(domain_data.row) > 0 and isinstance(domain_data.row[0], dict):
        domain_data.title = domain_data.row[0]["title"]
    else:
        chat_history_query = ChatHistoryQuery()
        domain_data.row = await chat_history_query.get_chat_history_by_session_key(db=db, domain_data=domain_data)
        if domain_data.row:
            async for chunk in make_title_response_with_llm(llm_proxy_client=llm_proxy_client, domain_data=domain_data):
                domain_data.title += chunk

            await chat_title_query.insert_chat_title(
                db=db,
                domain_data=domain_data
            )

    # response
    await close_db(db)
    return StreamingResponse(make_title_response(domain_data.title), media_type='text/plain')


@router.get("/get_mcp_tools")
@handle_errors()
async def get_mcp_tools(
    payload: GetMcpToolsPayload,
    user_info:dict = Depends(get_user_info),
):
    # client
    memory_db_client = RedisClient()

    # business logic
    domain_data = GetMcpToolsDomain(session_key=user_info["session_key"], answer_id=payload.answer_id)
    # business logic
    domain_data.history_data = await RunLLM.get_conversation_history(
        memory_db_client=memory_db_client,
        session_key=domain_data.session_key
    )
    if not domain_data.history_data:
        domain_data.response = {"tools": None}
    else:
        helper_get_tools_by_session_key_and_answer_id(
            domain_data=domain_data
        )

    return Response200(data=domain_data.response).to_dict()


@router.post("/get_retrieval_data")
@handle_errors()
async def get_retrieval_data(
    payload:retrievalPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    """Res RAG Data FROM PINECONE"""
    # check server stage
    server_stage = os.getenv("SERVER_STAGE", "development")

    # set Client
    s3_client = S3Client()
    main_db_client = MySQLClient()
    chat_history_query = ChatHistoryQuery()

    # business logic
    domain_data:retrievalDomain = await helper_get_retrieval_data_getting_source_data_ids(db, chat_history_query, payload, user_info, server_stage)
    domain_data.question = await chat_history_query.get_question(db=db, domain_data=domain_data)
    if not domain_data.refer_ids and not domain_data.parser_ids and domain_data.email_ids and domain_data.sitemap_ids: # there is not RAG data in Database
        domain_data.retrieval_data = []
    else:
        domain_data.retrieval_data = await RunLLM.get_retrieval_data(
            refer_ids=domain_data.refer_ids,
            parser_ids=domain_data.parser_ids,
            email_ids=domain_data.email_ids,
            sitemap_ids=domain_data.sitemap_ids,
            main_db_client=main_db_client,
            s3_client=s3_client
        )

    # make response and return
    data = {
        "retrieval_data":domain_data.retrieval_data,
        "question":domain_data.question,
        "mcp_tools": domain_data.mcp_tools
    }
    return Response200(data=data).to_dict()



@router.get("/get_conversation_history")
@handle_errors()
async def get_conversation_history(
    query_params:GetConversationHistoryQueryParams=Depends(),
    user_info:dict=Depends(get_user_info),
    db:AsyncSession=Depends(get_db)
):
    """send Conversation Data in Redis to Client"""
    # args
    domain_data = getConversationHistoryDomain(
        session_key=user_info["session_key"] if not int(query_params.is_mcp) else f"mcp_{user_info['session_key']}",
        is_mcp=False if not query_params.is_mcp else True
    )

    # set client
    memory_db_client = RedisClient()
    chat_history_query = ChatHistoryQuery()

    # business logic
    history_data = await RunLLM.get_conversation_history(
        memory_db_client=memory_db_client,
        session_key=domain_data.session_key
    )

    if history_data:
        domain_data.conversation_history = history_data
    else:
        await get_history_data_and_set_to_redis(
            db=db,
            memory_db_client=memory_db_client,
            chat_history_query=chat_history_query,
            domain_data=domain_data
        )

    data = domain_data.conversation_history
    return Response200(data=data).to_dict()


@router.get("/get_conversation_history_title")
@handle_errors()
async def get_conversation_history_title(
    query_params: getConversationHistoryTitleQueryParams = Depends(),
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    chat_history_query = ChatHistoryQuery()

    #business logic
    domain_data:getConversationHistoryTitleDomain = helper_get_chat_history_title_domain_data(user_info, query_params)
    await helper_get_session_list_and_count(db, chat_history_query, domain_data)
    await helper_get_chat_history_title(db, chat_history_query, domain_data)

    # make response and return
    data = {"rows": domain_data.rows, "count": domain_data.session_count}
    return Response200(data=data).to_dict()


@router.get("/get_greetings")
@handle_errors()
async def get_greetings(
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    company_info_query = CompanyInfoQuery()

    # business logic
    domain_data = getGreetingsDomain(company_key=user_info["company_key"])
    await helper_get_greetings_data(db, company_info_query, domain_data)

    # make response and return
    data = {"greetings":domain_data.greetings}
    return Response200(data=data).to_dict()


@router.get("/get_credit")
@handle_errors()
async def get_credit(
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    domain_data = getCreditDomain(company_key=user_info["company_key"])

    # set client
    company_info_query = CompanyInfoQuery()

    # business logic
    domain_data.credit = await company_info_query.get_credit_available(db=db, domain_data=domain_data)

    # make response and return
    data = {"creditAvailable": domain_data.credit}
    return Response200(data=data).to_dict()


@router.post("/new_chat")
@handle_errors()
async def new_chat(
    user_info:dict = Depends(get_user_info)
):
    # business logic
    domain_data = newChatDomain(user_id=user_info["user_id"], session_key=user_info["session_key"])
    helper_new_chat_update_session_key_in_user_info_and_return_identity(domain_data=domain_data)
    helper_new_chat_make_token_response_data(domain_data=domain_data)

    data = {"accessToken": domain_data.access_token, "refreshToken": domain_data.refresh_token}
    return Response200(data=data).to_dict()


@router.post("/update_rating")
@handle_errors()
async def update_rating(
    payload:updateRatingPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    memory_db_client = RedisClient()
    chat_history_query = ChatHistoryQuery()

    # business logic
    domain_data = updateConversationHistoryDomain(
        id=payload.id,
        session_key=user_info["session_key"],
        rating=payload.rating
    )
    await chat_history_query.update_conversation_history(
        db=db,
        domain_data=domain_data
    )
    domain_data.history_data = await RunLLM.get_conversation_history(
        memory_db_client=memory_db_client,
        session_key=domain_data.session_key
    )
    await helper_update_conversation_history_data_save_to_redis(memory_db_client, domain_data)

    # make response and return
    data = {"id":domain_data.id, "rating": domain_data.rating}
    return Response200(data=data).to_dict()


@router.post("/update_comment")
@handle_errors()
async def update_comment(
    payload:updateCommentPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    memory_db_client = RedisClient()
    chat_history_query = ChatHistoryQuery()

    # business logic
    domain_data:updateConversationHistoryDomain = updateConversationHistoryDomain(
        id=payload.id,
        session_key=user_info["session_key"],
        memo=payload.comment,
    )
    await chat_history_query.update_conversation_history(
        db=db,
        domain_data=domain_data
    )
    domain_data.history_data =await RunLLM.get_conversation_history(
        memory_db_client=memory_db_client,
        session_key=domain_data.session_key
    )
    await helper_update_conversation_history_data_save_to_redis(memory_db_client, domain_data)

    # make response and return
    data = {"id":domain_data.id, "comment": domain_data.memo}
    return Response200(data=data).to_dict()


@router.post("/set_history")
@handle_errors()
async def set_history(
    payload:setHistoryPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    memory_db_client = RedisClient()
    chat_history_query = ChatHistoryQuery()

    # business logic
    domain_data:setHistoryDomain = setHistoryDomain(session_key=payload.session_key, user_id=user_info["user_id"])
    await get_history_data_and_set_to_redis(db=db, memory_db_client=memory_db_client, chat_history_query=chat_history_query, domain_data=domain_data)
    helper_set_history_make_token(domain_data=domain_data)

    # make response and return
    data = {
        "conversationHistory": domain_data.conversation_history,
        "accessToken": domain_data.access_token,
        "refreshToken": domain_data.refresh_token
    }
    return Response200(data=data).to_dict()
