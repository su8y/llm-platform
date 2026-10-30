from fastapi import APIRouter, Depends

from auth.dependencies import get_user_info

from models import get_db
from helper.admin import *
from utils.error import *



router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)



@router.post("/get_members")
@handle_errors()
async def get_members(
    payload:getMembersPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):  
    # check auth
    if user_info["user_auth"] != 1:
        raise ForbiddenError("You are not admin")
    
    # set client
    invite_history_query = InviteHistoryQuery()

    # business logic
    domain_data:getMembersDomain = helper_get_member_making_domain_data(payload, user_info)
    await helper_get_member_from_db(db, invite_history_query, domain_data)

    # make response and return
    helper_get_members_reform(domain_data) # response data
    data = {
        "rows": domain_data.reform_row,
        "count": domain_data.count
    }
    return Response200(data=data)


@router.get("/get_auth_name")
@handle_errors()
async def get_auth_name(
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # check auth
    if user_info["user_auth"] != 1:
        raise ForbiddenError("You are not admin")
    
    # set client
    user_auth_query = UserAuthQuery()

    # business logic
    domain_data = getAuthNameDomain(company_key=user_info["company_key"])
    domain_data.rows = await user_auth_query.get_auth_name(db, domain_data)

    # make response and return
    return Response200(data=domain_data.rows)


@router.post("/change_auth")
@handle_errors()
async def change_auth(
    payload:changeAuthPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # check auth
    if user_info["user_auth"] != 1:
        raise ForbiddenError("You are not admin")
    
    # set client
    user_auth_query = UserAuthQuery()
    user_info_query = UserInfoQuery()

    # business logic
    domain_data = helper_change_auth_making_domain_data(payload, user_info)
    await helper_change_auth_get_auth_name(db, user_auth_query, domain_data)
    await helper_change_auth_from_db(db, user_info_query, domain_data)
    
    # make response and return
    return Response200().to_dict()


@router.post("/change_lang")
@handle_errors()
async def change_lang(
    payload:changeLangPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # check admin request
    if user_info["user_auth"] != 1:
        raise ForbiddenError("You are not admin")

    # set client
    user_info_query = UserInfoQuery()

    # business logic
    domain_data = changeLangDomain(
        user_id=payload.user_id,
        lang=payload.lang
    )
    await user_info_query.update_lang(db, domain_data)

    # make response and return
    return Response200().to_dict()


@router.post("/invite_member")
@handle_errors()
async def invite_member(
    payload:inviteMemberPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # check admin requester
    if user_info["user_auth"] != 1:
        raise ForbiddenError("You are not admin")

    # set_client
    company_info_query = CompanyInfoQuery()
    invite_history_query = InviteHistoryQuery()

    # business logic
    domain_data:inviteMemberDomain = helper_invite_member_making_domain_data(payload, user_info)
    await helper_invite_member_checking_already_email_address(db, invite_history_query, domain_data) # if success, there is not in history!
    await helper_invite_member_making_query_data_and_mail_data(db, company_info_query, domain_data)
    await invite_history_query.insert_invite_history(db, domain_data)
    await send_invitation_mail_by_dream_mailer(domain_data) # request to render-api -> message queue -> dream-mailer -> aws ses -> user's email
    await helper_invite_member_update_success_in_db(db, invite_history_query, domain_data)

    # make response and return
    return Response200().to_dict()


@router.post("/reinvite_member")
@handle_errors()
async def reinvite_member(
    payload:reInviteMemberPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # check admin requester
    if user_info["user_auth"] != 1:
        raise ForbiddenError("You are not admin")

    # set client
    company_info_query = CompanyInfoQuery()
    invite_history_query = InviteHistoryQuery()
    
    # business logic
    domain_data:reInviteMemberDomain = helper_reinvite_member_making_domain_data(payload, user_info)
    await helper_reinvite_member_checking_already_email_address(db, invite_history_query, domain_data)
    await helper_reinvite_member_making_query_data_and_mail_data(db, company_info_query, domain_data)
    await invite_history_query.insert_invite_history(db, domain_data)
    await send_invitation_mail_by_dream_mailer(domain_data) # request to render-api -> message queue -> dream-mailer -> aws ses -> user's email
    await helper_invite_member_update_success_in_db(db, invite_history_query, domain_data)

    return Response200().to_dict()


@router.get("/accept")
@handle_errors()
async def update_accept(
    query_params:acceptQueryParams = Depends(),
    db:AsyncSession = Depends(get_db)
):
    # set client
    invite_history_query = InviteHistoryQuery()

    # business logic
    domain_data = acceptDomain(acceptance=query_params.acceptance)
    helper_accept_invitation_decode_invitation_key(domain_data)
    domain_data.row = await invite_history_query.get_id_and_expire_time(db, domain_data)
    helper_accept_invitation_making_invitation_front_url(domain_data)

    # make response and return redirect to register frontend url
    return redirect(url=domain_data.redirect_url)
    

@router.post("/delete_user")
@handle_errors()
async def delete_user(
    payload:deleteUserPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # check admin requester
    if user_info["user_auth"] != 1:
        raise ForbiddenError("You are not admin")

    # set client
    user_info_query = UserInfoQuery()
    invite_history_query = InviteHistoryQuery()

    # business logic
    domain_data = deleteUserDomain(
        user_id=payload.user_id,
        invite_history_id=payload.invite_history_id,
        company_key=user_info["company_key"]
    )
    await user_info_query.delete(db, domain_data)
    await invite_history_query.delete_by_id(db, domain_data)

    # make response and return
    return Response200().to_dict()