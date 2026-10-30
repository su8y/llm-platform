from fastapi import APIRouter, Depends

from models import get_db, close_db
from auth.dependencies import get_user_info
from helper.system import *
from queries.cx_email_prompt import CXEmailPromptQuery
from utils.error import *
from client.milvus import MilvusClient



router = APIRouter(
    prefix="/system",
    tags=["system"],
)



@router.post("/insert_email_prompt")
@handle_errors()
async def insert_email_prompt(
    payload:InsertEmailPromptPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # make domain_data
    domain_data = InsertEmailPromptDomain(
        company_key = payload.company_key,
        writer = payload.writer,
        prompt = payload.prompt,
        prompt_name = payload.prompt_name,
        comment = payload.comment
    )

    # set client
    cx_email_prompt_query = CXEmailPromptQuery()

    # business logic
    await cx_email_prompt_query.insert_row(db, domain_data)

    # make response and return
    return Response200().to_dict()