from fastapi import APIRouter, Depends

from models import get_db
from auth.dependencies import get_user_info
from helper.emailrag import *
from payload.emailrag import *
from domain.emailrag import *
from utils.error import *



router = APIRouter(
    prefix="/emailrag",
    tags=["emailrag"],
)



@router.post("/emailrag_list")
@handle_errors()
async def emailrag_list(
    payload: EmailRAGListPayload,
    user_info: dict = Depends(get_user_info),
    db: AsyncSession = Depends(get_db)
):
    # domain_data
    domain_data:EmailRAGListDomain = helper_emailrag_list_make_domain_data(payload, user_info)

    # set client
    email_send_history_query = EmailSendHistoryQuery()

    # business logic
    await helper_emailrag_list_get_rows(db, email_send_history_query, domain_data)
    helper_email_list_make_response(domain_data)

    # return response
    return Response200(data=domain_data.response).to_dict()


@router.post("/get_emailrag_detail")
@handle_errors()
async def get_emailrag_detail(
        payload: EmailRAGDetailPayload,
        user_info: dict = Depends(get_user_info),
        db: AsyncSession = Depends(get_db)
):
    # domain_data
    domain_data = EmailRAGDetailDomain(
        company_key = user_info["company_key"],
        row_id = payload.id
    )

    # set client
    s3_client = S3Client()
    email_send_history_query = EmailSendHistoryQuery()

    # business logic
    await helper_get_emailrag_detail_get_row(db, email_send_history_query, domain_data)
    if domain_data.row.get("thread"):
        await helper_get_emailrag_download_html_from_s3(s3_client, domain_data)
        helper_get_emailrag_image_info(domain_data)
        helper_get_emailrag_make_response(domain_data)

    # return response
    return Response200(data=domain_data.response).to_dict()
