from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from models import get_db
from queries.company_info import CompanyInfoQuery
from queries.plan_info import PlanInfoQuery
from auth.dependencies import get_user_info
from payload.company import *
from helper.company import *
from domain.company import *
from utils.error import *
from utils.response import *



router = APIRouter(
    prefix="/company",
    tags=["company"],
)



@router.post("/charge_credit")
@handle_errors()
async def charge_credit(
    payload:chargeCreditPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db),
):
    # set client
    company_info_query = CompanyInfoQuery()
    
    # set value
    company_key = user_info.get("company_key")
    charge_credit = payload.charge_credit
    
    # business logic    
    if not charge_credit:
        logging.info("there is not chargeCredit in payload. please check payload")
        raise DataError("there is not chargeCredit in payload. please check payload")
    elif type(charge_credit) is not int:
        logging.info("type of chargeCredit is wrong. please check payload")
        raise DataError("type of chargeCredit is wrong. please check payload")
    credit_available_after_update = await company_info_query.charge_credit(db, company_key, charge_credit)
    
    # make response and return
    data = {"creditAvailable": credit_available_after_update}
    return Response200(data=data).to_dict()


@router.get("/get_plan")
@handle_errors()
async def get_plan(
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db),
):
    # set client
    plan_info_query = PlanInfoQuery()
    
    # business logic
    plans = await plan_info_query.get_plan_info(db, is_show=True)
    data = [
        {
            "planName": plan["plan_name"],
            "planPrice": plan["plan_price"],
            "initCredit": plan["init_credit"],
            "maxToken": plan["max_token"],
            "model": plan["model"]
        } for plan in plans
    ]
    return Response200(data=data).to_dict()


@router.get("/get_credit")
@handle_errors()
async def get_credit(
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db),
):
    # set domain
    domain_data = getCreditDomain(company_key=user_info.get("company_key"))

    # set client
    company_info_query = CompanyInfoQuery()
    
    # business logic
    credit = await company_info_query.get_credit_available(db, user_info.get("company_key"))
    
    # make response and return
    data = {"creditAvailable": credit}
    return Response200(data=data).to_dict()


@router.post("/update_plan")
@handle_errors()
async def update_plan(
    payload:updatePlanPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db),
):
    # set client
    company_info_query = CompanyInfoQuery()
    
    # set value
    company_key = user_info.get("company_key")
    plan_name = payload.plan_name
    
    # business logic
    if not plan_name:
        logging.info("there is not planName in payload. please check payload")
        raise DataError("there is not planName in payload. please check payload")
    status = plan_to_status(plan_name=plan_name)
    if status == 999:
        logging.info("planName is Invalid. please check database and constant.")
        raise DataError("planName is Invalid. please check database and constant.")
    plan_name_after = await company_info_query.update_plan(db, company_key, status)
    data = {"planName": plan_name_after}
    return Response200(data=data).to_dict()