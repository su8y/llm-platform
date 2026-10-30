import os
import re
import io
import ast
import copy
import time
import json
import asyncio
import base64
from io import BytesIO
from uuid import uuid4
from PIL import Image

from client.aws import SESClient, S3Client
from client.smtp import SMTPClient
from sqlalchemy.ext.asyncio import AsyncSession

from queries.company_info import CompanyInfoQuery
from queries.cx_email import CXEmailQuery
from queries.cx_email_history import CXEmailHistoryQuery
from queries.cx_email_references import CXEmailReferencesQuery
from queries.cx_email_temp import CXEmailTempQuery
from queries.email_send_history import EmailSendHistoryQuery
from queries.vector import VectorQuery
from queries.email_cid_images import EmailCIDImagesQuery
from queries.user_info import UserInfoQuery
from queries.mail_prompt_history import MailPromptHistoryQuery
from domain.email import *
from domain.prompt import *
from payload.email import *

from utils.date import *
from utils.error import *
from utils.text import html_to_text, html_to_markdown
from utils.vector import get_token_length



def helper_inbox_list_make_domain_data(payload:InboxListPayload, user_info:dict) -> InboxListDomain:
    start_date = string_to_datetime(payload.start_date, "UTC")
    end_date = get_last_hour_of_day(payload.end_date, "UTC")

    return InboxListDomain(
        company_key=user_info["company_key"],
        page=payload.page,
        per_page=payload.per_page,
        subject=payload.subject,
        start_date=start_date,
        end_date=end_date,
        from_=payload.from_,
        manager=payload.manager,
        status=payload.status
    )

async def helper_inbox_list_get_rows_and_count(db:AsyncSession, cx_email_query:CXEmailQuery, domain_data:InboxListDomain):
    try:
        domain_data.rows, domain_data.count = await cx_email_query.get_inbox_list(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.email.helper_inbox_list_get_rows_and_count] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_inbox_list_get_rows_and_count] Exception: {e}")
        raise Exception(e)


def helper_inbox_list_reform_row(domain_data:InboxListDomain):
    try:
        domain_data.reform_rows = [{
            "kind": row.get("kind") or "",
            "id": row.get("id") or 0,
            "subject": row.get("subject") or "",
            "status": row.get("status") or "",
            "receivedAt": row.get("received_at") or get_utc_now(),
            "fromName": row.get("from_name") or "",
            "fromMail": row.get("from_mail") or "",
            "manager": row.get("manager") or "",
        } for row in domain_data.rows] if domain_data.rows else []
    except Exception as e:
        logging.error(f"[helper.email.helper_inbox_list_reform_row] Exception: {e}")
        raise Exception(e)


async def helper_get_inbox_get_row(db:AsyncSession, cx_email_query:CXEmailQuery, domain_data:GetInboxDomain):
    try:
        domain_data.row = await cx_email_query.get_inbox_detail(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.email.helper_get_inbox_get_row] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_get_inbox_get_row] Exception: {e}")
        raise Exception(e)

async def helper_insert_prompt(db:AsyncSession, prompt_history_query:MailPromptHistoryQuery, domain_data:insertPromptDomain):
    try:
        data = await prompt_history_query.create_prompt(
            db=db,
            domain_data=domain_data
        )
        return data
    except DBError as e:
        logging.error(f"[helper.prompt.helper_insert_prompt] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.prompt.helper_insert_prompt] Exception: {e}")
        raise e


async def helper_update_company(db:AsyncSession, cx_email_query:CXEmailQuery, domain_data:UpdateCompanyDomain):
    try:
        await cx_email_query.update_company(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.email.helper_get_inbox_get_row] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_get_inbox_get_row] Exception: {e}")
        raise Exception(e)


def helper_get_inbox_reform_row(domain_data:GetInboxDomain):
    try:
        liststring_columns: list[str] = ["cc_name", "cc_mail", "references"]
        for column in liststring_columns:
            if domain_data.row.get(column) and isinstance(domain_data.row[column], str) and domain_data.row[column][0] == "[" and domain_data.row[column][-1] == "]":
                domain_data.row[column] = ast.literal_eval(domain_data.row[column])

        domain_data.reform_row = {
            "id": domain_data.row.get("id") or 0,
            "messageId": domain_data.row.get("message_id") or "",
            "subject": domain_data.row.get("subject") or "",
            "toName": domain_data.row.get("to_name") or "",
            "toMail": domain_data.row.get("to_mail") or "",
            "company": domain_data.row.get("company") or "",
            "fromName": domain_data.row.get("from_name") or "",
            "fromMail": domain_data.row.get("from_mail") or "",
            "ccName": domain_data.row.get("cc_name") or [],
            "ccMail": domain_data.row.get("cc_mail") or [],
            "receivedAt": domain_data.row.get("received_at") or get_utc_now(),
            "references": domain_data.row.get("references") or [],
            "status": domain_data.row.get("status") or "",
            "content": domain_data.row.get("content") or "",
            "keyword": domain_data.row.get("keyword") or "",
            "templates": domain_data.row.get("templates") or [],
            "kind": domain_data.row.get("kind") or "",
            "manager": domain_data.row.get("manager") or "",
            "lastContent": domain_data.row.get("last_content") or "",
            "comment": domain_data.row.get("comment") or "",
            "answeringContent": "",
            "thread": domain_data.row.get("html_s3_key") or domain_data.row.get("content"),
            "attachments": domain_data.row.get("attachments"),
            "hasTemp": domain_data.row.get("has_temp")
        }
        if domain_data.reform_row.get("status") in ["answering", "sent"]:
            domain_data.reform_row["answeringContent"] = domain_data.row.get("answering_content") or ""
        else:
            domain_data.reform_row["answeringContent"] = None

        if domain_data.row.get("cid_images"):
            bucket = os.getenv("CX_S3_BUCKET_NAME", "cx-email-html")
            cid_images:list[dict] = ast.literal_eval(domain_data.row["cid_images"])
            domain_data.reform_row["imageInfo"] = [
                {
                    "cid": cid_image["contentId"],
                    "imageURL": S3Client.get_public_url(bucket, cid_image["s3Key"])
                } for cid_image in cid_images
            ]
        else:
            domain_data.reform_row["imageInfo"] = None

    except Exception as e:
        logging.error(f"[helper.email.helper_get_inbox_reform_row] Exception: {e}")
        raise Exception(e)


async def helper_get_inbox_download_s3_file(s3_client: S3Client, domain_data:GetInboxDomain):
    try:
        bucket = "cx-email-html"
        key = domain_data.reform_row.get('thread')

        html_content, is_error = await s3_client.get_file_from_s3(bucket, key)
        if is_error:
            raise AWSError("Failed to download html file from s3")
        domain_data.reform_row["thread"] = html_content

    except AWSError as e:
        logging.error(f"[helper.email.helper_get_inbox_download_s3_file] AWSError: {e}")
    except Exception as e:
        logging.error(f"[helper.email.helper_get_inbox_download_s3_file] Exception: {e}")


async def helper_get_inbox_history(db:AsyncSession, cx_email_history_query: CXEmailHistoryQuery, domain_data: GetInboxHistoryDomain):
    try:
        domain_data.response = await cx_email_history_query.get_history_of_email(db, domain_data)
    except DBError as dbe:
        logging.error(f"[helper.email.helper_get_manager_list] DBError: {dbe}")
        raise DBError
    except Exception as e:
        logging.error(f"[helper.email.helper_get_manager_list] Exception: {e}")
        raise Exception


async def helper_get_manager_list(db:AsyncSession, user_info_query: UserInfoQuery, domain_data: GetManagerListDomain):
    try:
        domain_data.response = await user_info_query.get_user_list(db, domain_data)
    except DBError as dbe:
        logging.error(f"[helper.email.helper_get_manager_list] DBError: {dbe}")
        raise DBError
    except Exception as e:
        logging.error(f"[helper.email.helper_get_manager_list] Exception: {e}")
        raise Exception


async def helper_set_manager(db:AsyncSession, cx_email_query: CXEmailQuery, domain_data: SetManagerDomain):
    try:
        await cx_email_query.set_manager(db, domain_data)
    except DBError as dbe:
        logging.error(f"[helper.email.helper_set_manager] DBError: {dbe}")
        raise DBError
    except Exception as e:
        logging.error(f"[helper.email.helper_set_manager] Exception: {e}")
        raise Exception


def helper_change_status_make_action_code(domain_data: ChangeStatusDomain):
    try:
        if domain_data.status == EMAIL_SPAM:
            domain_data.action_code = EMAIL_HISTORY_EDIT_TO_SPAM
        elif domain_data.status == EMAIL_PENDING:
            domain_data.action_code = EMAIL_HISTORY_EDIT_TO_PENDING
        elif domain_data.status == EMAIL_ANSWERING:
            domain_data.action_code = EMAIL_HISTORY_EDIT_TO_ANSWERING
        elif domain_data.status == EMAIL_SENT:
            domain_data.action_code = EMAIL_HISTORY_EDIT_TO_SENT
        elif domain_data.status == EMAIL_CLOSED:
            domain_data.action_code = EMAIL_HISTORY_EDIT_TO_CLOSED

    except Exception as e:
        logging.error(f"[helper.email.helper_change_status_make_action_code] Exception: {e}")
        raise Exception(e)


async def  helper_check_and_enroll_manager(db:AsyncSession, cx_email_query:CXEmailQuery, domain_data: ChangeStatusDomain):
    try:
        row = await cx_email_query.get_inbox_detail(db, domain_data)
        if not row["manager"]:
            domain_data.manager_id = domain_data.user_id
            await cx_email_query.set_manager(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.email.helper_change_status_change_status] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_change_status_change_status] Exception: {e}")
        raise Exception(e)


async def helper_change_status_change_status(db:AsyncSession, cx_email_query:CXEmailQuery, domain_data: ChangeStatusDomain):
    try:
        await cx_email_query.change_status(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.email.helper_change_status_change_status] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_change_status_change_status] Exception: {e}")
        raise Exception(e)


async def helper_update_receive_comment(db: AsyncSession, cx_email_query: CXEmailQuery, domain_data: UpdateReceiveCommentDomain):
    try:
        await cx_email_query.update_comment(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.email.helper_update_receive_comment] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_update_receive_comment] Exception: {e}")
        raise Exception(e)


def helper_create_answer_make_domain_data(payload:CreateAnswerPayload, user_info:dict, server_stage:str) -> CreateEmailContentDomain:
    # set service
    if server_stage == DOCKER:
        service = "llm-platform-install"
    elif server_stage == REAL:
        service = "llm-platform-production"
    else:
        service = "llm-platform-staging"

    return CreateEmailContentDomain(
        id=payload.id,
        service=service,
        vendor=payload.vendor or BASE_MAIL_VENDOR,
        model=payload.model or BASE_MAIL_MODEL,
        question=payload.question,
        session_key=user_info["session_key"],
        company_key=user_info["company_key"],
        vector_db_index=user_info["vector_db_index"],
        vector_db_namespace=user_info["vector_db_namespace"],
        credit_available=user_info["credit_available"],
        user_id=user_info["user_id"],
        start_time=time.time(),
        action_code=EMAIL_HISTORY_CREATE_CONTENT,
        current_time=get_utc_now()
    )


async def helper_get_send_info(db: AsyncSession, cx_email_temp_query: CXEmailTempQuery, domain_data: GetSendInfoDomain):
    try:
        domain_data.response = await cx_email_temp_query.get_row(db, domain_data)
        target_change_types = ["toMail", "toName", "ccMail", "ccName", "bccMail", "bccName", "attachments"]
        for target_change_type in target_change_types:
            if domain_data.response.get(target_change_type) and isinstance(domain_data.response[target_change_type], str) and domain_data.response[target_change_type][0] == "[" and domain_data.response[target_change_type][-1] == "]":
                domain_data.response[target_change_type] = ast.literal_eval(domain_data.response[target_change_type])
            else:
                domain_data.response[target_change_type] = []

    except DBError as e:
        logging.error(f"[helper.email.helper_get_send_info] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_get_send_info] Exception: {e}")
        raise Exception(e)


def helper_save_send_info_make_domain_data(payload: SaveSendInfoPayload, user_info:dict):
    try:
        return SaveSendInfoDomain(
            id = payload.id,
            cx_email_id = payload.id,
            user_id = user_info["user_id"],
            company_key = user_info["company_key"],
            current_time = get_utc_now(),
            action_code = EMAIL_HISTORY_EDIT_CONTENT,
            to_mail = payload.to_mail,
            to_name = payload.to_name,
            cc_mail = payload.cc_mail,
            cc_name = payload.cc_name,
            bcc_mail = payload.bcc_mail,
            bcc_name = payload.bcc_name,
            subject = payload.subject,
            answering_content = payload.answering_content,
            comment = payload.comment,
            attachments = payload.attachments
        )
    except Exception as e:
        logging.error(f"[helper.email.helper_save_send_info_make_domain_data] Exception: {e}")


async def helper_save_send_info_check_diff_attach_and_delete(db: AsyncSession, cx_email_temp_query: CXEmailTempQuery, s3_client: S3Client, domain_data: SaveSendInfoDomain):
    try:
        domain_data.ex_row = await cx_email_temp_query.get_row(db, domain_data)
        if domain_data.ex_row.get("attachments"):
            before_attachments_str = domain_data.ex_row["attachments"]
            before_attachments_key = [obj["s3Key"] for obj in ast.literal_eval(before_attachments_str)]
            after_attachments_key = [obj["s3Key"] for obj in domain_data.attachments] if domain_data.attachments else []
            attachments_target_delete_keys = list(set(before_attachments_key) - set(after_attachments_key))
            if attachments_target_delete_keys:
                tasks = []
                for key in attachments_target_delete_keys:
                    tasks.append(s3_client.delete_on_s3("cx-email-html", key))
                await asyncio.gather(*tasks)

    except AWSError as e:
        logging.error(f"[helper.email.helper_save_send_info_delete_attach_in_s3] DBError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_save_send_info_delete_attach_in_s3] Exception: {e}")
        raise Exception(e)


async def helper_save_send_info_update_row(db: AsyncSession, cx_email_temp_query: CXEmailTempQuery, domain_data: SaveSendInfoDomain):
    try:
        await cx_email_temp_query.update_row(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.email.helper_save_send_info_update_row] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_save_send_info_update_row] Exception: {e}")
        raise Exception(e)


async def helper_create_answer_check_status(domain_data:CreateEmailContentDomain):
    try:
        if domain_data.status == "sent":
            raise DataError("Email is already sent")
        if domain_data.status == "answering":
            query = "SELECT status FROM cx_email WHERE id = %s"
            execute = await domain_data.main_db_client.execute(query, (domain_data.id,))
            result = execute.fetchone()
            if result and result[0] == "sent":
                raise DataError("Email is already sent")
    except DataError as e:
        logging.error(f"[helper.email.helper_create_answer_check_status] DataError: {e}")
        raise DataError(e)
    except DBError as e:
        logging.error(f"[helper.email.helper_create_answer_check_status] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_create_answer_check_status] Exception: {e}")
        raise Exception(e)


async def helper_send_email_reform_reply_cc(domain_data:SendEmailDomain):
    try:
        if isinstance(domain_data.reply_cc, str):
            domain_data.reply_cc = domain_data.reply_cc.replace(" ", "").split(",")
    except Exception as e:
        logging.error(f"[helper.email.helper_send_email_reform_reply_cc] Exception: {e}")
        raise Exception(e)


async def helper_send_email_send_mail_by_smtp(smtp_client:SMTPClient, domain_data:SendEmailDomain):
    try:
        data = {
            "to": domain_data.reply_to,
            "from": domain_data.reply_from,
            "from_name": domain_data.reply_from_name,
            "cc": domain_data.reply_cc,
            "subject": domain_data.reply_subject,
            "content": domain_data.email_html,
            "is_html": True
        } if domain_data.server_stage == REAL else {
            "to": os.getenv("STAGING_MAIL_ADDRESS", "staging@example.com"),
            "from": domain_data.reply_from,
            "from_name": domain_data.reply_from_name,
            "cc": None,
            "subject": domain_data.reply_subject,
            "content": domain_data.email_html,
            "is_html": True
        }
        await smtp_client.send_email(data)

    except Exception as e :
        logging.error(f"[helper.email.helper_send_email_send_mail_by_dream_mailer] ERROR: Fail to send email by smtp server.")
        raise Exception(e)


async def helper_save_send_info_upload_attach(s3_client:S3Client, domain_data:SaveAttachDomain):
    try:
        _uuid = str(uuid4())
        tasks = list()
        for attachment in domain_data.attachments:
            file_data = BytesIO(attachment.file.read())
            bucket = "cx-email-html"
            s3_key = f"{domain_data.company_key}/attachments/{_uuid}/{attachment.filename}"
            tasks.append(s3_client.put_object_to_s3(bucket_name=bucket, object_name=s3_key, file_data=file_data))
            domain_data.response.append({
                "filename": attachment.filename,
                "size": attachment.size,
                "s3Key": s3_key,
                "contentType": attachment.content_type
            })
        await asyncio.gather(*tasks)
    except Exception as e:
        logging.error(f"[helper.email.helper_save_send_info_upload_attach] Exception: {e}")
        raise Exception(e)


async def helper_check_has_thread_get_first_message_id_and_references(db:AsyncSession, cx_email_query:CXEmailQuery, domain_data:CheckHasThreadDomain):
    try:
        domain_data.received_references_rows = await cx_email_query.get_all_thread_data_by_id(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.email.helper_check_is_thread_get_first_message_id_and_references] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_check_is_thread_get_first_message_id_and_references] Exception: {e}")
        raise Exception(e)


def helper_check_has_thread(domain_data: CheckHasThreadDomain):
    try:
        if not domain_data.received_references_rows:
            pass
        else:
            for row in domain_data.received_references_rows:
                if row.get("references") and isinstance(row["references"], str) and row["references"][0] == "[" and row["references"][-1] == "]":
                    references = ast.literal_eval(row["references"])
                    if row["target_message_id"] in references:
                        raise HasThreadError

                    if row.get("target_references") and isinstance(row["target_references"], str) and row["target_references"][0] == "[" and row["target_references"][-1] == "]":
                        target_references = ast.literal_eval(row["target_references"])
                        before_message_id = target_references[-1]
                        if before_message_id in references and row["target_time"] < row["compare_time"]:
                            raise HasThreadError

    except HasThreadError:
        raise HasThreadError
    except Exception as e:
        logging.error("whole error")
        logging.error(f"[helper.email.helper_check_has_thread] Exception: {e}")
        raise Exception(e)


async def helper_check_hash_thread_get_sent_row(db:AsyncSession, cx_email_query:CXEmailQuery, domain_data:CheckHasThreadDomain):
    try:
        domain_data.sent_rows = await cx_email_query.get_sent_rows(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.email.helper_check_hash_thread_get_sent_row] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_check_hash_thread_get_sent_row] Exception: {e}")
        raise Exception(e)


def helper_check_has_sent_thread(domain_data):
    try:
        if domain_data.sent_rows:
            raise HasThreadError
    except HasThreadError:
        raise HasThreadError
    except Exception as e:
        logging.error("whole error")
        logging.error(f"[helper.email.helper_check_has_thread] Exception: {e}")
        raise Exception(e)


def helper_send_email_make_domain_data(payload:SendEmailPayload, user_info:dict, server_stage:str):
    try:
        return SendEmailDomain(
            id=int(payload.id),
            company_key=user_info["company_key"],
            server_stage=server_stage,
            email_html=payload.email_html,
            vector_db_index=user_info["vector_db_index"],
            vector_db_namespace=user_info["vector_db_namespace"],
            current_time=get_utc_now(),
            image_info=payload.image_info,
            user_id=user_info["user_id"],
            action_code=EMAIL_HISTORY_SENT
        )

    except Exception as e:
        logging.error(f"[helper.email.helper_send_email_make_domain_data] DataError: {e}")
        raise DataError(e)


async def helper_send_email_get_data_from_cx_email(db: AsyncSession, cx_email_query:CXEmailQuery, domain_data:SendEmailDomain):
    try:
        data = await cx_email_query.get_send_data(db, domain_data)
        if not data:
            raise DataError("Email not found")
        domain_data.from_message_id=data["message_id"]
        domain_data.received_subject=data["received_subject"]
        domain_data.reply_subject=data["reply_subject"]
        domain_data.reply_from=data["reply_from"]
        domain_data.reply_from_name=data["reply_from_name"]
        domain_data.reply_to=data["reply_to"] if isinstance(data["reply_to"], list) else ast.literal_eval(data["reply_to"])
        domain_data.reply_to_name=data["reply_to_name"] if isinstance(data["reply_to_name"], list) else ast.literal_eval(data["reply_to_name"])
        domain_data.reply_cc=data["reply_cc"] if isinstance(data["reply_cc"], list) else ast.literal_eval(data["reply_cc"])
        domain_data.reply_cc_name=data["reply_cc_name"] if isinstance(data["reply_cc_name"], list) else ast.literal_eval(data["reply_cc_name"])
        domain_data.reply_bcc=data["reply_bcc"] if isinstance(data["reply_bcc"], list) else ast.literal_eval(data["reply_bcc"])
        domain_data.reply_bcc_name=data["reply_bcc_name"] if isinstance(data["reply_bcc_name"], list) else ast.literal_eval(data["reply_bcc_name"])
        domain_data.keyword=data["keyword"]
        domain_data.references=data["references"] if isinstance(data["references"], list) or not data["references"] else ast.literal_eval(data["references"])
        domain_data.manager_id=data["manager_id"]
        domain_data.comments=data["comment"]
        domain_data.received_at=data["received_at"]
        domain_data.attachments=data["attachments"]
        domain_data.vector_content=str({"received": {"title": domain_data.reply_subject, "content": data["question_content"]}, "sent": {"title": domain_data.received_subject, "content":html_to_text(domain_data.email_html).split(EMAIL_THREAD_SPLITTER)[0]}})
        domain_data.llm_content=str({"received": {"title": domain_data.reply_subject, "content": data["question_content"]}, "sent": {"title": domain_data.received_subject, "content":html_to_markdown(domain_data.email_html).split(EMAIL_THREAD_SPLITTER)[0]}})

        for field_name, field in [('reply_to', domain_data.reply_to), ('reply_cc', domain_data.reply_cc), ('reply_bcc', domain_data.reply_bcc)]:
            if isinstance(field, list) and os.getenv("INTENTIONAL_ERROR_MAIL_ADDRESS", "error@example.com") in field:
                logging.error(f"[helper.email.helper_send_email_get_data_from_cx_email] intentional error: {field_name}={field}")
                raise Exception("Email intentional error")


    except DBError as e:
        logging.error(f"[helper.email.helper_send_email_get_data_from_cx_email] cx_email_id: {domain_data.id} | DBError: {e}")
        raise DBError(e)
    except DataError as e:
        logging.error(f"[helper.email.helper_send_email_get_data_from_cx_email] cx_email_id: {domain_data.id} | DataError: {e}")
        raise DataError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_send_email_get_data_from_cx_email] cx_email_id: {domain_data.id} | Exception: {e}")
        raise Exception(e)


async def helper_send_email_download_attachments(s3_client:S3Client, domain_data:SendEmailDomain):
    try:
        if domain_data.attachments:
            attachments = ast.literal_eval(domain_data.attachments)
            tasks = []
            for attachment in attachments:
                domain_data.attachments_info_for_ses.append({
                    "filename": attachment["filename"],
                    "content_type": attachment["contentType"]
                })
                tasks.append(s3_client.get_file_from_s3("cx-email-html", attachment["s3Key"]))
            attachments_datas = await asyncio.gather(*tasks)
            for attachment_data, attachment in zip(attachments_datas, domain_data.attachments_info_for_ses):
                if attachment_data[1]:
                    raise AWSError
                file_data = attachment_data[0]  # bytes 객체 그대로 사용
                attachment["file_data"] = file_data

    except AWSError as e:
        logging.error(f"[helper.email.helper_send_email_download_attachments] cx_email_id: {domain_data.id} | AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_send_email_download_attachments] cx_email_id: {domain_data.id} | Exception: {e}")
        raise Exception(e)


async def helper_send_email_get_cid_and_image(db:AsyncSession, s3_client:S3Client, cx_email_query:CXEmailQuery, domain_data:SendEmailDomain):
    try:
        # 1. get add image object
        cid_images = list()
        if domain_data.image_info:
            for enum, image_info in enumerate(domain_data.image_info, start=1):
                image_data, is_error = await s3_client.get_file_from_s3(image_info["bucket"], image_info["key"])
                if is_error:
                    raise AWSError

                # base64 encoding
                domain_data.cid_and_image.append({
                    "cid": image_info.get("cid"),
                    "image": base64.b64encode(image_data).decode("utf-8"),
                    "filename": f"{image_info.get('cid')}_img_{enum}.png",
                    "mimeType": "image/png"
                })

                # cid_images for email_send_history
                cid_images.append({
                    "contentId": image_info.get("cid"),
                    "s3Key": image_info["key"],
                    "contentType": "image/png"
                })
            domain_data.cid_images = str(cid_images)

        # 2. get thread image cid and object
        cid_images_str = await cx_email_query.get_cid_images_by_message_id(db, domain_data)
        if cid_images_str:
            cid_images_list:list[dict] = ast.literal_eval(cid_images_str)
            for cid_image in cid_images_list:
                image_data, is_error = await s3_client.get_file_from_s3("cx-email-html", cid_image['s3Key'])
                if is_error:
                    raise AWSError

                # base64 encoding
                domain_data.cid_and_image.append({
                    "cid": cid_image["contentId"],
                    "image": base64.b64encode(image_data).decode("utf-8"),
                    "filename": f"{cid_image['filename']}",
                    "mimeType": "image/png"
                })

    except DBError as e:
        logging.error(f"[helper.email.helper_send_email_get_cid_and_image] cx_email_id: {domain_data.id} | DBError: {e}")
        raise DBError(e)
    except AWSError as e:
        logging.error(f"[helper.email.helper_send_email_get_cid_and_image] cx_email_id: {domain_data.id} | AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_send_email_get_cid_and_image] cx_email_id: {domain_data.id} | Exception: {e}")
        raise Exception(e)


async def helper_send_email_send_mail_by_dream_mailer(domain_data:SendEmailDomain):
    try:
        from utils.mail import send_mail_by_dream_mailer
        data = {
            'templateName': domain_data.template_name,
            'email': domain_data.reply_to,
            'cc': domain_data.reply_cc,
            'subject': domain_data.reply_subject,
            'content': domain_data.email_html,
            'inReplyTo': domain_data.from_message_id,
            'jiraIssue': '',
            'references': domain_data.references,
            'managerId': domain_data.manager_id,
            'comments': domain_data.comments
        }
        domain_data.response = await send_mail_by_dream_mailer(
            template_name=domain_data.template_name,
            data=data,
            service_code=1
        )
    except Exception as e:
        logging.error(f"[helper.email.helper_send_email_send_mail_by_dream_mailer] Exception: {e}")
        raise Exception(e)


async def helper_send_email_load_smtp_setting(db:AsyncSession, smtp_setting_query, domain_data:SendEmailDomain):
    """회사에 활성 SMTP 설정이 있으면 SMTP 로 발송한다(설치형 기본 경로). 없으면 SES."""
    try:
        from helper.mail_setting import smtp_config_from_row
        row = await smtp_setting_query.get_by_company(db, domain_data.company_key)
        domain_data.smtp_config = smtp_config_from_row(row) if row and row.get("is_active") else None
    except AppError:
        raise
    except Exception as e:
        logging.error(f"[helper.email.helper_send_email_load_smtp_setting] cx_email_id: {domain_data.id} | Exception: {e}")
        raise Exception(e)


def _as_address_list(value) -> list:
    if not value:
        return []
    return [v for v in (value if isinstance(value, list) else [value]) if v]


async def helper_send_email_send_mail_by_smtp_setting(smtp_client:SMTPClient, domain_data:SendEmailDomain):
    """회사 SMTP 설정으로 실제 수신자에게 발송한다. Message-ID 를 직접 만들어 스레드 추적에 쓴다."""
    from utils.mime_builder import build_raw_message, new_message_id
    config = domain_data.smtp_config
    to_list, cc_list, bcc_list = _as_address_list(domain_data.reply_to), _as_address_list(domain_data.reply_cc), _as_address_list(domain_data.reply_bcc)
    if not to_list:
        raise DataError("No recipient address")
    message_id = new_message_id(config["from_address"])
    references = (domain_data.references or []) + ([domain_data.from_message_id] if domain_data.from_message_id else [])
    message = build_raw_message(
        from_address=config["from_address"], from_name=config.get("from_name") or domain_data.reply_from_name,
        to_address_list=to_list, cc_address_list=cc_list, bcc_address_list=bcc_list,
        subject=domain_data.reply_subject or "", body_html=domain_data.email_html or "",
        attachments=domain_data.attachments_info_for_ses, in_reply_to=domain_data.from_message_id, references=references or None,
        image_data=domain_data.cid_and_image, reply_to=domain_data.reply_from if isinstance(domain_data.reply_from, str) else None,
        message_id=message_id,
    )
    await smtp_client.send_raw(config, message, sender=config["from_address"], recipients=to_list + cc_list + bcc_list)
    domain_data.to_message_id = message_id.strip("<>")


async def helper_send_email_send_mail_by_ses(ses_client:SESClient, domain_data:SendEmailDomain):
    try:
        if domain_data.server_stage == REAL:
            args = {
                "from_address": domain_data.reply_from,
                "to_address_list": domain_data.reply_to.copy() if isinstance(domain_data.reply_to, list) else [domain_data.reply_to.copy()],
                "subject": domain_data.reply_subject,
                "body_html": domain_data.email_html,
                "cc_address_list": domain_data.reply_cc.copy() if isinstance(domain_data.reply_cc, list) else [domain_data.reply_cc.copy()],
                "bcc_address_list": domain_data.reply_bcc.copy() if isinstance(domain_data.reply_bcc, list) else [domain_data.reply_bcc.copy()],
                "attachments": domain_data.attachments_info_for_ses,
                "in_reply_to": domain_data.from_message_id,
                "references": domain_data.references + [domain_data.from_message_id] if domain_data.references else [domain_data.from_message_id],
                "image_data": domain_data.cid_and_image
            }
        else:
            args = {
                "from_address": domain_data.reply_from,
                "to_address_list": [os.getenv("STAGING_MAIL_ADDRESS", "staging@example.com")],
                "subject": f"{domain_data.reply_subject} === 받는 메일: {domain_data.reply_to}, 참조 메일: {domain_data.reply_cc}, 숨은 참조 메일: {domain_data.reply_bcc}",
                "body_html": domain_data.email_html,
                "cc_address_list": [os.getenv("STAGING_MAIL_ADDRESS", "staging@example.com") for _ in domain_data.reply_cc] if isinstance(domain_data.reply_cc, list) and domain_data.reply_cc else [],
                "bcc_address_list": [os.getenv("STAGING_MAIL_ADDRESS", "staging@example.com") for _ in domain_data.reply_bcc] if isinstance(domain_data.reply_bcc, list) and domain_data.reply_bcc else [],
                "attachments": domain_data.attachments_info_for_ses,
                "in_reply_to": domain_data.from_message_id,
                "references": domain_data.references + [domain_data.from_message_id] if domain_data.references else [domain_data.from_message_id],
                "image_data": domain_data.cid_and_image
            }

            # protect to occur human error
            addresses_list = [args["to_address_list"], args["cc_address_list"], args["bcc_address_list"]]
            for i, addresses in enumerate(addresses_list):
                if addresses:
                    addresses_list[i] = [
                        addr for addr in addresses
                        if addr.split("@")[-1] == os.getenv("STAGING_MAIL_ALLOWED_DOMAIN", "example.com")
                    ]
            logging.info(f"[client.aws.SESClient.send_mail_with_raw] to: {args.get('to_address_list')}")
            logging.info(f"[client.aws.SESClient.send_mail_with_raw] cc: {args.get('cc_address_list')}")
            logging.info(f"[client.aws.SESClient.send_mail_with_raw] bcc: {args.get('bcc_address_list')}")

            if not args.get("to_address_list"):
                domain_data.to_message_id = f"MessageID_YOU_CAN_SEND_ONLY_ALLOWED_DOMAIN_{str(uuid4()).replace('-', '')[:8]}"
                raise Exception("[helper.email.helper_send_email_send_mail_by_ses] is not to_address")

        domain_data.to_message_id = await ses_client.send_mail_with_raw(
            from_address=args["from_address"],
            to_address_list=args["to_address_list"],
            subject=args["subject"],
            body_html=args["body_html"],
            attachments=args["attachments"],
            cc_address_list=args["cc_address_list"],
            bcc_address_list=args["bcc_address_list"],
            in_reply_to=args["in_reply_to"],
            references=args["references"],
            image_data=args["image_data"]
        )
        logging.info(f"[helper.email.helper_send_email_send_mail_by_ses] | cx_email_id:{domain_data.id} & email_send_history_id:{domain_data.row_id} | is success to send email by ses. message_id is {domain_data.to_message_id}")

    except AWSError as e:
        logging.error(f"[helper.email.helper_send_email_send_mail_by_ses] cx_email_id: {domain_data.id}, AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_send_email_send_mail_by_ses] cx_email_id: {domain_data.id}, Exception: {e}")
        raise Exception(e)


async def helper_send_email_update_cx_email_status(db:AsyncSession, cx_email_query:CXEmailQuery, domain_data:SendEmailDomain):
    try:
        await cx_email_query.update_status(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.email.helper_send_email_update_comment_and_manager_id] cx_email_id: {domain_data.id} & email_send_history_id:{domain_data.row_id} | DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_send_email_update_comment_and_manager_id] cx_email_id: {domain_data.id} & email_send_history_id:{domain_data.row_id} | Exception: {e}")
        raise Exception(e)


async def helper_send_email_upload_html_to_s3(s3_client:S3Client, domain_data:SendEmailDomain):
    # for Binding Pinecone <-> S3
    try:
        file_data = BytesIO(domain_data.email_html.encode('utf-8'))
        domain_data.s3_bucket = "cx-email-html"
        domain_data.s3_key = f"{domain_data.company_key}/send/{str(uuid4())}.html"
        await s3_client.upload_file(file_data=file_data, bucket=domain_data.s3_bucket, key=domain_data.s3_key, content_type="text/html")

    except AWSError as e:
        logging.error(f"[helper_send_email_upload_html_to_s3] cx_email_id: {domain_data.id} & email_send_history_id:{domain_data.row_id} | AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[helper_send_email_upload_html_to_s3] cx_email_id: {domain_data.id} & email_send_history_id:{domain_data.row_id} | Exception: {e}")
        raise Exception(e)


async def helper_send_email_update_email_send_history_row(db:AsyncSession, email_send_history_query:EmailSendHistoryQuery, domain_data:SendEmailDomain):
    try:
        await email_send_history_query.update_row_after_send_mail(db, domain_data)
    except DBError as e:
        logging.error(f"[helper_send_email_update_row_after_send_email] cx_email_id: {domain_data.id} & email_send_history_id:{domain_data.row_id} | DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper_send_email_update_row_after_send_email] cx_email_id: {domain_data.id} & email_send_history_id:{domain_data.row_id} | DBError: {e}")
        raise Exception(e)


async def helper_send_email_insert_answer_row(db:AsyncSession, email_rag_query:EmailSendHistoryQuery, domain_data:SendEmailDomain):
    try:
        domain_data.row_id = await email_rag_query.insert_outbox(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.email.helper_send_email_insert_answer_row] cx_email_id: {domain_data.id} | DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_send_email_insert_answer_row] cx_email_id: {domain_data.id} | Exception: {e}")
        raise Exception(e)


async def helper_send_email_insert_refereces_row(db: AsyncSession, cx_email_references_query: CXEmailReferencesQuery, domain_data: SendEmailDomain):
    try:
        if domain_data.references:
            references = ast.literal_eval(domain_data.references) if isinstance(domain_data.references, str) and domain_data.references[0] == "[" and domain_data.references[-1] == "]" else domain_data.references
            domain_data.first_message_id = references[0]
        elif domain_data.from_message_id:
            domain_data.first_message_id = domain_data.from_message_id
        else:
            domain_data.first_message_id = domain_data.to_message_id

        await cx_email_references_query.insert_references_row(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.email.helper_send_email_insert_refereces_row] cx_email_id: {domain_data.id} & email_send_history_id:{domain_data.row_id} | DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_send_email_insert_refereces_row] cx_email_id: {domain_data.id} & email_send_history_id:{domain_data.row_id} | Exception: {e}")
        raise Exception(e)


async def helper_send_email_check_is_vector_content_over_token(domain_data:SendEmailDomain):
    try:
        token_length = get_token_length(text=domain_data.vector_content)
        if token_length > 40000:
            domain_data.is_over_token = True
        else:
            domain_data.is_over_token = False
    except Exception as e:
        logging.error(f"[helper.email.helper_send_email_check_is_email_html_over_token] cx_email_id: {domain_data.id} | Exception: {e}")


async def helper_send_email_chunking_thread(llm_proxy_client:LLMProxyClient, domain_data:SendEmailDomain):
    try:
        logging.info(f"[api.email.send_email] cx_email_id:{domain_data.id} is start to insert vector in vectorDB.")
        content_after_chunking = _chunking_text(domain_data.vector_content, EMBEDDING_MODEL, 500, 150)

        if domain_data.server_stage == DOCKER:
            service = "llm-platform-install"
        elif domain_data.server_stage == REAL:
            service = "llm-platform-production"
        else:
            service = "llm-platform-staging"

        batch_size = 10
        domain_data.vector_values = []
        for i in range(0, len(content_after_chunking), batch_size):
            batched_vector_values = content_after_chunking[i:i+batch_size]
            tasks = [llm_proxy_client.embeddings(text=content, service=service) for content in batched_vector_values]
            vector_values_per_batch = await asyncio.gather(*tasks)
            domain_data.vector_values.extend(vector_values_per_batch)

        for chunk, _value in enumerate(domain_data.vector_values, start=1):
            domain_data.vector_metadatas.append({
                "id": domain_data.row_id,
                "company_key": domain_data.company_key,
                "is_show": True,
                "is_on": True,
                "page": 1,
                "data_type": "email",
                "chunk": chunk,
                "content": content_after_chunking[chunk - 1]
            })
            # for update, delete
            domain_data.vector_table_datas.append({
                "email_id": domain_data.row_id,
                "company_key": domain_data.company_key,
                "is_show": True,
                "is_on": True,
                "page": 1,
                "data_type": "email",
                "chunk": chunk
            })

    except LLMProxyError as e:
        logging.error(f"[helper_send_email_chunking_thread] cx_email_id: {domain_data.id} & email_send_history_id:{domain_data.row_id} | LLMProxyError: {e}")
        raise LLMProxyError(e)
    except Exception as e:
        logging.error(f"[helper_send_email_chunking_thread] cx_email_id: {domain_data.id} & email_send_history_id:{domain_data.row_id} | Exception: {e}")
        raise Exception(e)


async def helper_send_email_insert_answer_vector_row(db:AsyncSession, vector_query:VectorQuery, domain_data:SendEmailDomain):
    try:
        ids_int = await vector_query.bulk_insert_vector_from_email(db, domain_data)
        domain_data.vector_ids = [f"email-{str(_id)}" for _id in ids_int]
    except DBError as e:
        logging.error(f"[helper_send_email_insert_answer_vector_row] cx_email_id: {domain_data.id} & email_send_history_id:{domain_data.row_id} | DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper_send_email_insert_answer_vector_row] cx_email_id: {domain_data.id} & email_send_history_id:{domain_data.row_id} | Exception: {e}")
        raise Exception(e)


async def helper_send_email_insert_question_and_answer_to_vector_db(vector_db_client:PineconeClient|MilvusClient, domain_data:SendEmailDomain):
    try:
        if len(domain_data.vector_ids) == len(domain_data.vector_values) == len(domain_data.vector_metadatas):
            await vector_db_client.insert_many(ids=domain_data.vector_ids, values=domain_data.vector_values, metadatas=domain_data.vector_metadatas)
    except VectorDBError as e:
        logging.error(f"[helper_send_email_insert_answer_vector_row] cx_email_id: {domain_data.id} & email_send_history_id:{domain_data.row_id} | VectorDBError: {e}")
        raise VectorDBError(e)
    except Exception as e :
        logging.error(f"[helper_send_email_insert_answer_vector_row] cx_email_id: {domain_data.id} & email_send_history_id:{domain_data.row_id} | Exception: {e}")
        raise Exception(e)


async def helper_delete_sent_email_getting_chunk_metadatas(db:AsyncSession, vector_query:VectorQuery, domain_data:DeleteSentEmailDomain):
    try:
        domain_data.vector_id, domain_data.vector_metadata = await vector_query.get_vector_ids_and_metadatas_by_email_id(db, domain_data)
    except DBError as e:
        logging.error(f"[helper_delete_sent_email_getting_chunk] email_send_history_id: {domain_data.email_send_history_id} | DBError: {e}")
        raise DBError(e)
    except Exception as e :
        logging.error(f"[helper_delete_sent_email_getting_chunk] email_send_history_id: {domain_data.email_send_history_id} | Exception: {e}")
        raise Exception(e)


async def helper_delete_sent_email_updating_data_in_vector_db(vector_db_client:PineconeClient|MilvusClient, domain_data:DeleteSentEmailDomain):
    try:
        if not domain_data.vector_metadata:
            logging.error(f"[helper_delete_sent_email_updating_data_in_vector_db] email_send_history_id: {domain_data.email_send_history_id} | No Data")
            raise Exception(f"No data in main_db_client: id={domain_data.vector_id}, metadata={domain_data.vector_metadata}")

        domain_data.target_delete_ids = []
        domain_data.target_update_metadata = []
        for _id, metadata in zip(domain_data.vector_id, domain_data.vector_metadata):
            domain_data.target_delete_ids.append(f"email-{str(_id)}")
            domain_data.target_update_metadata.append({**metadata, "is_on": False, "is_show": False})

        await vector_db_client.update(ids=domain_data.target_delete_ids, metadatas=domain_data.target_update_metadata)

    except VectorDBError as e:
        logging.error(f"[helper_delete_sent_email_updating_data_in_vector_db] email_send_history_id: {domain_data.email_send_history_id} | VectorDBError: {e}")
        raise VectorDBError(e)
    except Exception as e :
        logging.error(f"[helper_delete_sent_email_updating_data_in_vector_db] email_send_history_id: {domain_data.email_send_history_id} | Exception: {e}")
        raise Exception(e)


async def helper_delete_sent_email_updating_row_in_main_db(db:AsyncSession, vector_query:VectorQuery, email_send_history_query:EmailSendHistoryQuery, domain_data:DeleteSentEmailDomain):
    try:
        await vector_query.update_is_on_of_vector_table_by_email_id(db, domain_data)
        await email_send_history_query.update_soft_deletion(db, domain_data)

    except DBError as e:
        logging.error(f"[helper_delete_sent_email_updating_data_in_vector_db] email_send_history_id: {domain_data.email_send_history_id} | DBError: {e}")
    except Exception as e :
        logging.error(f"[helper_delete_sent_email_updating_data_in_vector_db] email_send_history_id: {domain_data.email_send_history_id} | Exception: {e}")
        raise Exception(e)


async def helper_delete_sent_email_getting_chunk(db:AsyncSession, vector_query:VectorQuery, domain_data:DeleteSentEmailDomain):
    try:
        domain_data.vector_id = await vector_query.get_ids_by_email_send_history_id(db, domain_data)
    except DBError as e:
        logging.error(f"[helper_delete_sent_email_getting_chunk] email_send_history_id: {domain_data.email_send_history_id} | DBError: {e}")
        raise DBError(e)
    except Exception as e :
        logging.error(f"[helper_delete_sent_email_getting_chunk] email_send_history_id: {domain_data.email_send_history_id} | Exception: {e}")
        raise Exception(e)


async def helper_delete_sent_email_deleting_data_in_vector_db(vector_db_client:PineconeClient|MilvusClient, domain_data:DeleteSentEmailDomain):
    try:
        domain_data.target_delete_ids = [f"email-{str(_id)}" for _id in domain_data.vector_id]
        _filter = {"data_type": "email"}
        await vector_db_client.remove(id=domain_data.target_delete_ids, filter=_filter)
    except VectorDBError as e:
        logging.error(f"[helper_send_email_insert_answer_vector_row] email_send_history_id:{domain_data.email_send_history_id} | VectorDBError: {e}")
        raise VectorDBError(e)
    except Exception as e :
        logging.error(f"[helper_send_email_insert_answer_vector_row] email_send_history_id:{domain_data.email_send_history_id} | Exception: {e}")
        raise Exception(e)


async def helper_delete_sent_email_deleting_row_in_main_db(db:AsyncSession, vector_query:VectorQuery, email_send_history_query:EmailSendHistoryQuery, domain_data:DeleteSentEmailDomain):
    try:
        await vector_query.delete_vector_by_email_send_history_id(db, domain_data)
        await email_send_history_query.delete_by_id(db, domain_data)
    except DBError as e:
        logging.error(f"[helper_delete_sent_email_deleting_row_in_main_db] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper_delete_sent_email_deleting_row_in_main_db] Exception: {e}")
        raise Exception(e)



async def helper_get_ses_bounce_update_bounce(db:AsyncSession, email_send_history_query:EmailSendHistoryQuery, domain_data:GetSESBounceDomain):
    try:
        await email_send_history_query.update_bounce_message(db, domain_data)
    except DBError as e:
        logging.error(f"[helper_get_ses_bounce_update_bounce] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper_get_ses_bounce_update_bounce] Exception: {e}")
        raise Exception(e)


def helper_get_ses_bounce_make_domain_data(body: str|bytes|dict):
    try:
        if isinstance(body, str | bytes):
            payload = json.loads(body)
        elif isinstance(body, dict):
            payload = body
        else:
            error_message = f"requestBody should be string or dict. But type of requestBody is {type(body)}."
            logging.info(f"[helper_get_ses_bounce_make_domain_data] ValueError: {error_message}")
            raise Exception(error_message)

        if payload.get('notificationType') == 'Bounce':
            return GetSESBounceDomain(
                message_id=payload['mail']['messageId'],
                is_bounce=True,
                bounce_type=payload['bounce']['bounceType'],
                bounce_sub_type=payload['bounce']['bounceSubType'],
                bounced_recipients = json.dumps(payload['bounce']['bouncedRecipients'], indent=4)
            )
        else:
            return GetSESBounceDomain()

    except Exception as e:
        logging.error(f"[helper_get_ses_bounce_make_domain_data] Exception: {e}")
        raise Exception(e)


async def helper_inbox_file_download(s3_client: S3Client, s3_key: str) -> bytes:
    try:
        bucket = os.getenv("CX_S3_BUCKET_NAME", "cx-email-html")
        key = s3_key
        response = await s3_client.download_file(bucket=bucket, key=key)
        return response
    except AWSError as e:
        logging.error(f"[helper.email.helper_inbox_file_download] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_inbox_file_download] Exception: {e}")
        raise Exception(e)


async def helper_inbox_file_streaming(s3_client: S3Client, s3_key:str):
    try:
        bucket = os.getenv("CX_S3_BUCKET_NAME", "cx-email-html")
        key = s3_key
        return await s3_client.stream_file(bucket, key)
    except AWSError as e:
        logging.error(f"[helper.email.helper_inbox_file_streaming] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[helper.email.helper_inbox_file_streaming] Exception: {e}")
        raise Exception(e)


async def helper_init_answer_check_has_row(db: AsyncSession, cx_email_temp_query:CXEmailTempQuery, domain_data: InitAnswerDomain):
    try:
        domain_data.has_row = await cx_email_temp_query.check_has_row(db, domain_data)
    except DBError as dbe:
        logging.error(f"[helper.email.helper_init_answer_check_has_row] DBError: {dbe}")
        raise DBError
    except Exception as e:
        logging.error(f"[helper.email.helper_init_answer_check_has_row] Exception: {e}")
        raise Exception(e)


async def helper_get_to_address(db:AsyncSession, company_info_query:CompanyInfoQuery, domain_data: InitAnswerDomain | SaveSendInfoDomain):
    try:
        domain_data.company_email_address, domain_data.company_email_name = await company_info_query.get_to_address(db, domain_data)
    except DBError as dbe:
        logging.error(f"[helper.email.helper_init_answer_get_to_address] DBError: {dbe}")
        raise DBError
    except Exception as e:
        logging.error(f"[helper.email.helper_init_answer_get_to_address] Exception: {e}")
        raise Exception(e)


async def helper_init_answer_get_all_info(db:AsyncSession, cx_email_query:CXEmailQuery, domain_data: InitAnswerDomain):
    try:
        domain_data.cx_email_row = await cx_email_query.get_inbox_detail(db, domain_data)
    except DBError as dbe:
        logging.error(f"[helper.email.helper_init_answer_get_all_info] DBError: {dbe}")
        raise DBError
    except Exception as e:
        logging.error(f"[helper.email.helper_init_answer_get_all_info] Exception: {e}")
        raise Exception(e)


async def helper_init_answer_insert_answer_temp_row(db: AsyncSession, cx_email_temp_query: CXEmailTempQuery, domain_data: InitAnswerDomain):
    try:
        await cx_email_temp_query.insert_row(db, domain_data)
    except DBError as dbe:
        logging.error(f"[helper.email.helper_init_answer_insert_answer_temp_row] DBError: {dbe}")
        raise DBError
    except Exception as e:
        logging.error(f"[helper.email.helper_init_answer_insert_answer_temp_row] Exception: {e}")
        raise Exception(e)


async def helper_init_answer_update_has_temp_to_true(db: AsyncSession, cx_email_query: CXEmailQuery, domain_data: InitAnswerDomain):
    try:
        await cx_email_query.update_has_temp_to_true(db, domain_data)
    except DBError as dbe:
        logging.error(f"[helper.email.helper_init_answer_update_has_temp_to_true] DBError: {dbe}")
        raise DBError
    except Exception as e:
        logging.error(f"[helper.email.helper_init_answer_update_has_temp_to_true] Exception: {e}")
        raise Exception(e)


async def helper_inbox_file_get_presign_url(s3_client: S3Client, s3_key:str) -> str:
    try:
        bucket = os.getenv("CX_S3_BUCKET_NAME", "cx-email-html")
        presign_url = await s3_client.get_presigned_url(
            bucket,
            s3_key,
            3600,
            "get_object"
        )

        return presign_url["url"]
    except AWSError as e:
        logging.error(f"[drive.helper.download_thumbnail] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[drive.helper.download_thumbnail] Exception: {e}")
        raise Exception(e)


async def helper_upload_base64_image_to_s3(s3_client:S3Client, domain_data:UploadBase64Domain):
    try:
        for base64_data in domain_data.image:
            base64_data = base64_data.replace("data:image/png;base64,", "").replace("data:image/jpeg;base64,", "")
            base64_data = base64_data.replace("data:image/webp;base64,", "").replace("data:image/jpg;base64,", "")
            image_data = base64.b64decode(base64_data)
            if len(image_data) > 1024 * 1024 * 10:
                return {
                    "success": False,
                    "error": {
                        "name": "MulterError",
                        "message": "File too large",
                        "code": "LIMIT_FILE_SIZE",
                        "field": "upload",
                        "storageErrors": []
                    }
                }

        for base64_data in domain_data.image:
            cid = f"{str(uuid4()).replace('-', '')}-llmPlatformEmailServiceV1"
            base64_data = base64_data.replace("data:image/png;base64,", "").replace("data:image/jpeg;base64,", "")
            base64_data = base64_data.replace("data:image/webp;base64,", "").replace("data:image/jpg;base64,", "")
            image_data = base64.b64decode(base64_data)
            image = Image.open(io.BytesIO(image_data))
            image_meta = {
                "width": image.width,
                "height": image.height,
                "format": image.format.lower()
            }

            quality_width_limit = 820
            if image_meta["width"] > quality_width_limit:
                image = image.resize((quality_width_limit, int(image_meta["height"] * (quality_width_limit / image_meta["width"]))))
            quality_size_limit = 1024 * 300
            if len(image_data) >= quality_size_limit:
                image.save(io.BytesIO(), format=image_meta["format"], quality=80)

            buffer = io.BytesIO()
            image.save(buffer, format=image_meta["format"])
            size = buffer.tell()
            buffer.seek(0)

            bucket = "cx-email-html"
            filename = str(uuid4()).replace("-", "") + ".png"
            key = f"{domain_data.company_key}/cid-images/{cid}/" + filename
            await s3_client.put_object_to_s3(bucket, key, buffer)
            domain_data.response.append(
                {
                    "cid": cid, # neccessary
                    "bucket": bucket,
                    "key": key
                }
            )
            domain_data.insert_rows.append(
                {
                    "content_id": cid,
                    "s3_key": key,
                    "content_type": "image/png",
                    "size": size,
                    "filename": filename,
                    "current_date": domain_data.current_date
                }
            )

    except AWSError as e:
        logging.error(f"[helper.reference.helper_upload_base64_to_s3] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_upload_base64_to_s3] Exception: {e}")
        raise e


async def helper_record_history(db:AsyncSession, cx_email_history_query:CXEmailHistoryQuery, domain_data):
    try:
        await cx_email_history_query.insert_history_row(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.reference.helper_record_history] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_record_history] Exception: {e}")
        raise e


async def helper_upload_base64_insert_row_in_email_cid_images(db:AsyncSession, email_cid_images: EmailCIDImagesQuery, domain_data: UploadBase64Domain):
    try:
        await email_cid_images.insert_row(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.reference.helper_upload_base64_insert_row_in_email_cid_images] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_upload_base64_insert_row_in_email_cid_images] Exception: {e}")
        raise e


def helper_get_dashboard_chart_make_domain_data(payload:GetDashboardChartPayload, user_info:dict):
    try:
        start_date = string_to_datetime(payload.start_date, "UTC")
        end_date = get_last_hour_of_day(payload.end_date, "UTC")
        current_date = get_utc_now()
        diff_date = (current_date - start_date).days

        return GetDashboardChartDomain(
            company_key=user_info["company_key"],
            start_date=start_date,
            end_date=end_date,
            current_date=current_date,
            diff_date=diff_date,
            client_timezone=payload.timezone
        )
    except Exception as e:
        logging.error(f"[helper_dashboard_status_make_domain_data] Exception: {e}")
        raise e


async def helper_get_dashboard_chart_get_data_from_db(db:AsyncSession, cx_email_query:CXEmailQuery, domain_data:GetDashboardChartDomain):
    try:
        await cx_email_query.get_dashboard_chart(db, domain_data)
    except DBError as e:
        logging.error(f"[helper_dashboard_status_get_data_from_db] DBError: {e}")
        raise DBError
    except Exception as e:
        logging.error(f"[helper_dashboard_status_get_data_from_db] Exception: {e}")
        raise e


def helper_get_dashboard_chart_make_response(domain_data:GetDashboardChartDomain):
    try:
        domain_data.response["all"] = domain_data.row["all"]
        if domain_data.response["all"]["countAll"] == 0:
            domain_data.response["all"] = list()

        domain_data.response["parsed"] = list()
        domain_data.response["answering"] = list()
        if domain_data.row["parsed_days_data"] or domain_data.row["answering_days_data"]:
            parsed_rows = _parse_csv_string(domain_data.row["parsed_days_data"])
            answering_rows = _parse_csv_string(domain_data.row["answering_days_data"])
            pending_values_set = set(parsed_rows.values()) if parsed_rows else None
            answering_values_set = set(answering_rows.values()) if answering_rows else None
            is_pending_act = False if not pending_values_set or len(pending_values_set) <= 1 and tuple(pending_values_set)[0] == 0 else True
            is_answering_act = False if not answering_values_set or len(answering_values_set) <= 1 and tuple(answering_values_set)[0] == 0 else True

            if is_pending_act or is_answering_act:
                for i in range(0, domain_data.diff_date+1):
                    if is_pending_act:
                        parsed_count = parsed_rows.get(i, 0)
                        domain_data.response["parsed"].append({"days": i, "count": parsed_count})

                    if is_answering_act:
                        answering_count = answering_rows.get(i, 0)
                        domain_data.response["answering"].append({"days": i, "count": answering_count})

    except Exception as e:
        logging.error(f"[helper_get_dashboard_chart_make_response] Exception: {e}")
        raise e


def helper_get_dashboard_line_make_domain_data(payload:GetDashboardLinePayload, user_info:dict):
    try:
        start_date = string_to_datetime(payload.start_date, "UTC")
        start_date_datetime_local = adapt_timezone_str_to_datetime(payload.start_date, payload.timezone)
        end_date = get_last_hour_of_day(payload.end_date, "UTC")
        end_date_datetime_local = adapt_timezone_str_to_datetime(payload.end_date, payload.timezone)

        return GetDashboardLineDomain(
            company_key=user_info["company_key"],
            start_date=start_date,
            start_date_local=start_date_datetime_local,
            end_date=end_date,
            end_date_local=end_date_datetime_local,
            client_timezone=payload.timezone
        )
    except Exception as e:
        logging.error(f"[helper_dashboard_status_make_domain_data] Exception: {e}")
        raise e


async def helper_get_dashboard_line_get_data_from_db(db:AsyncSession, cx_email_query:CXEmailQuery, email_send_history: EmailSendHistoryQuery, domain_data:GetDashboardLineDomain):
    try:
        tasks = list()
        tasks.append(cx_email_query.get_in_count_per_days(db, domain_data))
        tasks.append(email_send_history.get_out_count_per_days(db, domain_data))
        await asyncio.gather(*tasks)
    except DBError as e:
        logging.error(f"[helper_dashboard_status_get_data_from_db] DBError: {e}")
        raise DBError
    except Exception as e:
        logging.error(f"[helper_dashboard_status_get_data_from_db] Exception: {e}")
        raise e


def helper_get_dashboard_line_make_response(domain_data:GetDashboardLineDomain):
    try:
        date_format = "%Y-%m-%d"
        re_basic_form = {"X": [day.strftime(date_format) for day in (domain_data.start_date_local + timedelta(days=i) for i in range((domain_data.end_date_local - domain_data.start_date_local).days + 1))], "data": [0 for _ in range((domain_data.end_date_local - domain_data.start_date_local).days + 1)]}
        se_basic_form = {"X": [day.strftime(date_format) for day in (domain_data.start_date_local + timedelta(days=i) for i in range((domain_data.end_date_local - domain_data.start_date_local).days + 1))], "data": [0 for _ in range((domain_data.end_date_local - domain_data.start_date_local).days + 1)]}
        result = {"received": re_basic_form, "sent": se_basic_form}
        received_dates = domain_data.cx_email_row.keys() if domain_data.cx_email_row else None
        sent_dates = domain_data.email_send_history_row.keys() if domain_data.email_send_history_row else None

        if received_dates or sent_dates:
            for enum, (received, sent) in enumerate(zip(result["received"]["X"], result["sent"]["X"])):
                if received_dates and received in received_dates:
                    result["received"]["data"][enum] = domain_data.cx_email_row[received]
                if sent_dates and sent in sent_dates:
                    result["sent"]["data"][enum] = domain_data.email_send_history_row[sent]

        domain_data.response = result

    except Exception as e:
        logging.error(f"[helper_get_dashboard_line_make_response] Exception: {e}")
        raise e


def helper_get_dashboard_manager_count_make_domain_data(payload:GetDashboardManagerCntPayload, user_info:dict):
    try:
        start_date = string_to_datetime(payload.start_date, "UTC")
        end_date = get_last_hour_of_day(payload.end_date, "UTC")

        return GetDashboardManagerCntDomain(
            company_key=user_info["company_key"],
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        logging.error(f"[helper_dashboard_status_make_domain_data] Exception: {e}")
        raise e


async def helper_get_dashboard_manager_count_get_data_from_db(db:AsyncSession, cx_email_query:CXEmailQuery, domain_data:GetDashboardManagerCntDomain):
    try:
        await cx_email_query.get_dashboard_manager_cnt(db, domain_data)
    except DBError as e:
        logging.error(f"[helper_dashboard_status_get_data_from_db] DBError: {e}")
        raise DBError
    except Exception as e:
        logging.error(f"[helper_dashboard_status_get_data_from_db] Exception: {e}")
        raise e


def helper_get_dashboard_manager_count_make_response(domain_data:GetDashboardManagerCntDomain):
    try:
        domain_data.response = domain_data.row
        if not domain_data.response:
            domain_data.response = list()
        else:
            to_none = ["", "null", None]  # None 타입도 추가
            for del_key in to_none:
                if del_key in domain_data.response.keys():
                    value = domain_data.response.pop(del_key)
                    if "none" not in domain_data.response:
                        domain_data.response["none"] = 0
                    domain_data.response["none"] += value

    except Exception as e:
        logging.error(f"[helper_dashboard_status_make_response] Exception: {e}")
        raise e


def _strip_html_tags(html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    return text


def _chunking_text(text: str, model_name: str, max_tokens: int, overlap_tokens: int = 100):
    import tiktoken
    encoding = tiktoken.encoding_for_model(model_name)
    tokens = encoding.encode(text)

    chunks = []
    start_idx = 0

    while start_idx < len(tokens):
        end_idx = min(start_idx + max_tokens, len(tokens))
        chunks.append(tokens[start_idx:end_idx])
        start_idx = end_idx - overlap_tokens if end_idx < len(tokens) else len(tokens)

    return [encoding.decode(chunk) for chunk in chunks] if len(chunks) > 0 else [""]


def _parse_csv_string(csv_string):
    if not csv_string:
        return {}
    result = {}
    for item in csv_string.split(','):
        days, count = item.split(':')
        result[int(days)] = int(count)
    return result
