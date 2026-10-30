from fastapi import APIRouter, Depends

from models import get_db
from auth.dependencies import get_user_info
from helper.prompt import *
from utils.error import *



router = APIRouter(
    prefix="/prompt",
    tags=["prompt"],
)



@router.post("/insert_prompt")
@handle_errors()
async def insert_prompt(
    payload:insertPromptPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # client
    prompt_history_query = PromptHistoryQuery()
    
    # business logic
    domain_data:insertPromptDomain = helper_insert_prompt_make_domain_data(payload, user_info)
    data = await helper_insert_prompt(db, prompt_history_query, domain_data)

    # make response and return
    return Response200(data=data).to_dict()


# TODO: change to GET
@router.post("/get_version")
@handle_errors()
async def get_version(
    payload:getVersionPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # client
    prompt_history_query = PromptHistoryQuery()

    # business logic
    domain_data = getVersionDomain(company_key=user_info['company_key'])
    data = await prompt_history_query.get_prompt_version(db, domain_data)

    # make response and return
    return Response200(data=data).to_dict()


@router.post("/get_prompt")
@handle_errors()
async def get_prompt(
    payload:getPromptPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # client
    prompt_history_query = PromptHistoryQuery()
    
    # business logic
    domain_data = getPromptDomain(company_key=user_info['company_key'], prompt_id=payload.prompt_id)
    data = await prompt_history_query.get_prompt(db, domain_data)

    # make response and return
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
    await helper_get_greetings(db, company_info_query, domain_data)

    # make response and return
    return Response200(data=domain_data.greetings).to_dict()


@router.post("/update_greetings")
@handle_errors()
async def update_greetings(
    payload:updateGreetingsPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    company_info_query = CompanyInfoQuery()

    # business logic
    domain_data = updateGreetingsDomain(company_key=user_info['company_key'], greetings=payload.greetings)
    await helper_update_greetings(db, company_info_query, domain_data)

    # make response and return
    return Response200().to_dict()