from fastapi import APIRouter, Depends

from models import get_db
from auth.dependencies import get_user_info
from helper.monitoring import *
from utils.error import *



router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"],
)



@router.post("/get_chat_history")
@handle_errors()
async def get_chat_history(
    payload:getChatHistoryPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    chat_history_query = ChatHistoryQuery()
    
    # business logic
    domain_data:getChatHistoryDomain = helper_get_chat_history_make_domain_data(payload, user_info)
    await helper_get_session_list_and_count(db, chat_history_query, domain_data)
    if domain_data.session_count == 0: # if there is not session, no need IO to get chat history
        data = {"rows": [], "issueCount": 0, "count": 0}
    else:
        await helper_get_chat_history_from_db_and_reform(db, chat_history_query, domain_data)
        data = {"rows": domain_data.rows, "issueCount": domain_data.issue_count, "count": domain_data.session_count}

    # make response and return
    return Response200(data=data).to_dict()


@router.post("/get_chat_history_detail_head")
@handle_errors()
async def get_chat_history_detail_head(
    payload:getChatHistoryDetailHeadPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    chat_history_query = ChatHistoryQuery()
    user_info_query = UserInfoQuery()

    # business logic
    domain_data = helper_get_chat_history_head_make_domain_data(payload, user_info)
    await helper_get_chat_history_head(db, chat_history_query, user_info_query, domain_data)

    # make response and return
    if domain_data.rating:
        domain_data.reformed_rows["rating"] = domain_data.rating
    if domain_data.id_list:
        domain_data.reformed_rows["idList"] = domain_data.id_list
    return Response200(data=domain_data.reformed_rows).to_dict()


@router.post("/get_chat_history_detail_tail")
@handle_errors()
async def get_chat_history_detail_tail(
    payload:getChatHistoryDetailTailPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    chat_history_query = ChatHistoryQuery()

    # business logic
    domain_data:getChatHistoryDetailTailDomain = helper_get_chat_history_tail_make_domain_data(payload, user_info)
    await helper_get_chat_history_tail(db, chat_history_query, domain_data)
    
    # make response and return 
    data:dict = domain_data.reformed_rows
    if domain_data.count:
        data["count"] = domain_data.count
    return Response200(data=data).to_dict()


@router.post("/get_chat_rating")
@handle_errors()
async def get_chat_rating(
    payload:getChatRatingPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    chat_history_query = ChatHistoryQuery()

    # business logic
    domain_data:getChatRatingDomain = helper_get_chat_rating_make_domain_data(payload, user_info)
    await helper_get_chat_rating(db, chat_history_query, domain_data)
    
    # make response and return 
    data:dict = domain_data.reformed_rows
    return Response200(data=data).to_dict()


@router.post("/get_chat_count")
@handle_errors()
async def get_chat_count(
    payload:getChatCountPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    chat_history_query = ChatHistoryQuery()
    
    # business logic
    domain_data:getChatCountDomain = helper_get_chat_count_make_domain_data(payload, user_info)
    await helper_get_chat_count(db, chat_history_query, domain_data)
    
    # make response and return
    data:dict = domain_data.reformed_rows
    return Response200(data=data).to_dict()


@router.post("/update_chat_history")
@handle_errors()
async def update_chat_history(
    payload:updateChatHistoryPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    chat_history_query = ChatHistoryQuery()
    
    # business logic
    domain_data:updateChatHistoryDomain = helper_update_chat_history_make_domain_data(payload, user_info)
    await helper_update_chat_history(db, chat_history_query, domain_data)
    
    # make response and return
    data:dict = domain_data.update_result
    return Response200(data=data).to_dict()


@router.post("/get_top")
@handle_errors()
async def get_top(
    payload:getTopPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    return Response200(data=None).to_dict()
    
    # set client
    ask_top_query = AskTopQuery()
    
    # business logic
    query_data = helper_get_top_make_query_data(payload, user_info)
    data = await helper_get_top(db, ask_top_query, query_data)
    
    # make response and return
    return Response200(data=data).to_dict()




# =======================
# Routes for Testing Tasks
# =======================
# @router.post("/run_ask_keyword")
# @handle_errors()
# async def run_ask_keyword(
#     user_info:dict = Depends(get_user_info),
#     db:AsyncSession = Depends(get_db)
# ):
#     # check admin
#     if not user_info["is_admin"]:
#         raise ForbiddenError("You are not admin")

#     # payload
#     payload = request.json

#     # set client
#     from utils.database import MySQLClientAlchemy
#     mysql_client = MySQLClientAlchemy()
    
#     # business logic
#     args = helper_run_ask_keyword_make_args_data(payload)
#     if type(args["target_date"]) == str:
#         task = AskKeyword(mysql_client=mysql_client, company_key=args["company_key"], period=args["period"], target_date=args["target_date"], model=args["model"])
#         task.run()    
#     elif type(args["target_date"]) == list: #TODO: temporary code. will delete after building AskKeyword Task
#         for target_date in args["target_date"]:
#             task = AskKeyword(mysql_client=mysql_client, company_key=args["company_key"], period=args["period"], target_date=target_date, model=args["model"])
#             task.run()
    
#     # make response and return
#     return response_200(data=None)
