from fastapi import APIRouter, Depends

from models import get_db
from auth.dependencies import get_user_info
from queries.payment_history import PaymentHistoryQuery
from queries.credit_history import CreditHistoryQuery
from queries.plan_info import PlanInfoQuery
from queries.file_credit_history import FileCreditHistoryQuery

from helper.plan import *
from utils.error import *



router = APIRouter(
    prefix="/plan",
    tags=["plan"],
)



@router.post("/insert_payment")
@handle_errors()
async def insert_payment(
    payload:insertPaymentPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db),
):
    # check internal admin
    if user_info["user_id"] != "admin":
        return Response403().to_dict()

    # payload
    insert_data = helper_insert_payment_makging_data(payload, user_info)

    # client
    payment_history_query = PaymentHistoryQuery()

    # business logic
    result = await payment_history_query.insert_payment_history(db, insert_data)
    data = helper_insert_payment_reform(result)

    return Response200(data=data).to_dict()


@router.post("/insert_plan")
@handle_errors()
async def insert_plan(
    payload:insertPlanPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db),
):
    # check internal admin
    if user_info["user_id"] != "admin":
        return Response403().to_dict()

    # payload
    data = helper_insert_plan_making_payment_data(payload)

    # client
    payment_query = PaymentQuery()
    company_info_query = CompanyInfoQuery()
    credit_history_query = CreditHistoryQuery()

    # business logic
    await check_is_current_plan(db, payment_query, data) # if current plan is exist, raise error
    insert_datas = helper_insert_plan_making_insert_row_data(data)
    first_payment_id = await payment_query.insert_plan_payment(db, insert_datas) # create payment row: make plan
    credit_available = await company_info_query.adapt_plan(db, data["target_company_key"], data["plan_info_id"], data["expired_date"]) # update credit_available: fulfill credit
    await credit_history_query.insert_credit_history(db, data["target_company_key"], True, credit_available, data["reg_date"], first_payment_id) # create credit_history row: record credit

    # make response and return
    return Response200().to_dict()


@router.get("/get_all_plan")
@handle_errors()
async def get_all_plan(
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db),
):
    # client
    plan_info_query = PlanInfoQuery()

    # business logic
    result = await plan_info_query.get_plan_info(db, is_show=True)
    data = reform_all_plan(result)

    # make response and return
    return Response200(data=data).to_dict()


@router.get("/get_credit")
@handle_errors()
async def get_credit(
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db),
):
    # client
    company_info_query = CompanyInfoQuery()

    # business logic
    data = await company_info_query.get_credit(db, user_info["company_key"])

    # make response and return
    return Response200(data=data).to_dict()


@router.get("/get_current_credit")
@handle_errors()
async def get_credit(
    query_params: getCurrentCreditParams = Depends(),
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # domain_data
    domain_data: GetCurrentPlanDomain = helper_get_current_credit_make_domain_data(query_params, user_info)

    # client
    company_info_query = CompanyInfoQuery()
    file_credit_query = FileCreditHistoryQuery()

    # business logic
    domain_data.credit_info = await company_info_query.get_current_credit(db, domain_data)
    domain_data.file_credit_info = await file_credit_query.get_file_credit(db, domain_data.company_key)

    result = {
        "questionCredit": domain_data.credit_info,
        "fileCredit": domain_data.file_credit_info
    }

    # make response and return
    if domain_data.credit_info["useAbleCredit"] == domain_data.params_current_credit:
        return Response9004().to_dict()
    return Response200(data=result).to_dict()


@router.get("/get_current_plan")
@handle_errors()
async def get_current_plan(
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db),
):
    # client
    payment_query = PaymentQuery()

    # business logic
    result = await payment_query.get_current_plan_info(db=db, company_key=user_info["company_key"], current_date=get_utc_now())
    data = reform_plan_info(result)

    # make response and return
    return Response200(data=data).to_dict()


@router.post("/get_plan_history")
@handle_errors()
async def get_plan_history(
    payload:getPlanHistoryPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db),
):
    # payload
    query_data = helper_get_plan_history_query_data(payload, user_info)

    # client
    payment_query = PaymentQuery()

    # business logic
    data = await payment_query.get_payment_history(
        db,
        page=query_data["page"],
        per_page=query_data["per_page"],
        company_key=query_data["company_key"],
        plan_name=query_data["plan_name"],
        type=query_data["payment_history_type"]
    )

    # make response and return
    return Response200(data=data).to_dict()


@router.post("/upgrade_plan")
@handle_errors()
async def upgrade_next_month_plan(
    payload:changePlanPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db),
):
    # payload
    query_data = helper_change_plan_query_data(payload, user_info)

    # client
    payment_query = PaymentQuery()
    company_info_query = CompanyInfoQuery()
    credit_history_query = CreditHistoryQuery()

    # business logic
    is_upgrade = helper_checking_is_upgrade(query_data)
    if is_upgrade: # 업그레이드인 경우
        target_upgrade_ids = await payment_query.get_target_upgrade_ids(db, query_data["company_key"], query_data["current_time"])
        if not target_upgrade_ids:
            logging.info("[api.plan.plan.upgrade_plan] target_upgrade_row is empty")
            raise DataError("[api.plan.plan.upgrade_plan] target_upgrade_row is empty")
        else:
            await payment_query.update_plan_info_id_all_plan(db, target_upgrade_ids, query_data["plan_info_id"], query_data["current_time"])
            credit_available = await company_info_query.upgrade_plan(db, query_data["company_key"], query_data["plan_info_id"]) # info_id, credit, expired_date!
            await credit_history_query.insert_credit_history(db, query_data["company_key"], True, credit_available, query_data["current_time"], target_upgrade_ids)
    else: # 다운그레이드인 경우
        is_current_plan = await payment_query.is_current_plan(db, query_data["company_key"], query_data["current_time"])
        if not is_current_plan:
            logging.info("[api.plan.plan.downgrade_plan] current plan is not exist")
            raise DataError("[api.plan.plan.downgrade_plan] current plan is not exist")
        else:
            target_downgrade_ids = await payment_query.get_target_downgrade_ids(db, query_data["company_key"], query_data["current_time"])
            await payment_query.update_plan_info_id_all_plan(db, target_downgrade_ids, query_data["plan_info_id"], query_data["current_time"])

    # make response and return
    return Response200().to_dict()
