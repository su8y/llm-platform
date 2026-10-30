import ast
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from client.aws import S3Client
from payload.emailrag import *
from domain.emailrag import *
from queries.email_send_history import EmailSendHistoryQuery

from utils.date import *
from utils.error import *



def helper_emailrag_list_make_domain_data(payload: EmailRAGListPayload, user_info:dict):
    try:
        return EmailRAGListDomain(
            company_key=user_info["company_key"],
            subject=payload.subject,
            manager=payload.manager,
            to=payload.to,
            page=payload.page,
            per_page=payload.per_page,
            start_date=string_to_datetime(payload.start_date, "UTC"),
            end_date=get_last_hour_of_day(payload.end_date, "UTC")
        )

    except Exception as e:
        logging.error(f"[helper.emailrag.helper_emailrag_list_make_domain_data] Exception: {e}")
        raise Exception(e)


async def helper_emailrag_list_get_rows(db:AsyncSession, email_send_history_query:EmailSendHistoryQuery, domain_data: EmailRAGListDomain):
    try:
        domain_data.row, domain_data.row_count = await email_send_history_query.outbox_list(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.emailrag.helper_emailrag_list_get_rows] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.emailrag.helper_emailrag_list_get_rows] Exception: {e}")
        raise Exception(e)


def helper_email_list_make_response(domain_data: EmailRAGListDomain):
    try:

        domain_data.response = {"email": domain_data.row, "count": domain_data.row_count}
    except DBError as e:
        logging.error(f"[helper.emailrag.helper_email_list_make_response] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.emailrag.helper_email_list_make_response] Exception: {e}")
        raise Exception(e)


async def helper_get_emailrag_detail_get_row(db:AsyncSession, email_send_history_query:EmailSendHistoryQuery, domain_data: EmailRAGDetailDomain):
    try:
        domain_data.row = await email_send_history_query.get_outbox_detail(db, domain_data)

        target_change_types = ["toMail", "toName", "ccMail", "ccName", "bccMail", "bccName", "attachments"]
        for target_change_type in target_change_types:
            if domain_data.row.get(target_change_type) and isinstance(domain_data.row[target_change_type], str) and domain_data.row[target_change_type][0] == "[" and domain_data.row[target_change_type][-1] == "]":
                domain_data.row[target_change_type] = ast.literal_eval(domain_data.row[target_change_type])
                if len(domain_data.row[target_change_type]) == 0:
                    domain_data.row[target_change_type] = []
            else:
                domain_data.row[target_change_type] = []

    except DBError as e:
        logging.error(f"[helper.emailrag.helper_get_emailrag_detail_get_row] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.emailrag.helper_get_emailrag_detail_get_row] Exception: {e}")
        raise Exception(e)


async def helper_get_emailrag_download_html_from_s3(s3_client: S3Client, domain_data: EmailRAGDetailDomain):
    try:
        path = domain_data.row.get('thread')
        if not path:
            raise Exception
        path_split = path.split(":")
        bucket = path_split[0]
        key = path_split[1]

        html_content, is_error = await s3_client.get_file_from_s3(bucket, key)
        if is_error:
            raise AWSError("Failed to download html file from s3")
        domain_data.row["thread"] = html_content
    except AWSError as e:
        logging.error(f"[helper.emailrag.helper_get_emailrag_download_html_from_s3] AWSError: {e}")
        raise AWSError
    except Exception as e:
        logging.error(f"[helper.emailrag.helper_get_emailrag_download_html_from_s3] Exception: {e}")
        raise Exception(e)


def helper_get_emailrag_image_info(domain_data: EmailRAGDetailDomain):
    try:
        if domain_data.row.get("thread") and domain_data.row.get("cid_images"):
            bucket = os.getenv("CX_S3_BUCKET_NAME", "cx-email-html")
            cid_images:list[dict] = ast.literal_eval(domain_data.row["cid_images"])
            domain_data.row["imageInfo"] = [
                {
                    "cid": cid_image["contentId"],
                    "imageURL": S3Client.get_public_url(bucket, cid_image["s3Key"])
                } for cid_image in cid_images
            ]
        else:
            domain_data.row["imageInfo"] = []

    except Exception as e:
        logging.error(f"[helper.emailrag.helper_get_emailrag_image_info] Exception: {e}")
        raise Exception(e)


def helper_get_emailrag_make_response(domain_data: EmailRAGDetailDomain):
    try:
        domain_data.response = {
            "messageId": domain_data.row["messageId"],
            "subject": domain_data.row["subject"],
            "toName": domain_data.row["toName"],
            "toMail": domain_data.row["toMail"],
            "fromName": domain_data.row["fromName"],
            "fromMail": domain_data.row["fromMail"],
            "ccName": domain_data.row["ccName"],
            "ccMail": domain_data.row["ccMail"],
            "bccName": domain_data.row["bccName"],
            "bccMail": domain_data.row["bccMail"],
            "sentAt": domain_data.row["sentAt"],
            "receivedAt": domain_data.row["receivedAt"],
            "keyword": domain_data.row["keyword"],
            "comment": domain_data.row["comment"],
            "manager": domain_data.row["manager"],
            "thread": domain_data.row["thread"],
            "attachments": domain_data.row["attachments"],
            "company": domain_data.row["company"],
            "imageInfo": domain_data.row["imageInfo"],
        }

    except Exception as e:
        logging.error(f"[helper.emailrag.helper_get_emailrag_image_info] Exception: {e}")
        raise Exception(e)
