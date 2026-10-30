import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.error import DBError
from domain.email import *



class CXEmailTempQuery:
    @staticmethod
    async def insert_row(db: AsyncSession, domain_data: InitAnswerDomain):
        try:
            query = text("""
                INSERT INTO cx_email_temp (
                    company_key,
                    cx_email_id,
                    user_id,
                    reg_date,
                    update_date,
                    from_mail,
                    from_name,
                    to_mail,
                    to_name,
                    cc_mail,
                    cc_name,
                    bcc_mail,
                    bcc_name,
                    subject
                ) VALUES (
                    :company_key,
                    :cx_email_id,
                    :user_id,
                    :reg_date,
                    :update_date,
                    :from_mail,
                    :from_name,
                    :to_mail,
                    :to_name,
                    :cc_mail,
                    :cc_name,
                    :bcc_mail,
                    :bcc_name,
                    :subject
                )
            """)
            params = {
                "company_key": domain_data.company_key,
                "cx_email_id": domain_data.id,
                "user_id": domain_data.user_id,
                "reg_date": domain_data.current_time,
                "update_date": domain_data.current_time,
                "from_mail": (from_mail := domain_data.company_email_address or domain_data.cx_email_row["to_mail"]),
                "from_name": domain_data.company_email_name or from_mail,
                "to_mail": f'["{domain_data.cx_email_row["from_mail"]}"]',
                "to_name": f'["{domain_data.cx_email_row["from_name"]}"]',
                "cc_mail": str(domain_data.cx_email_row['cc_mail']),
                "cc_name": str(domain_data.cx_email_row['cc_name']),
                "bcc_mail": "[]",
                "bcc_name": "[]",
                "subject": domain_data.cx_email_row['subject']
            }
            await db.execute(query, params)
            await db.commit()

        except Exception as e:
            logging.error(f"[queries.cx_email_temp.CXEmailTempQuery.insert_row] Exception: {e}")
            raise DBError


    @staticmethod
    async def get_row(db: AsyncSession, domain_data: GetSendInfoDomain|SaveSendInfoDomain):
        try:
            query = text("""
                SELECT
                    cx_email_id,
                    user_id,
                    reg_date,
                    update_date,
                    from_mail,
                    from_name,
                    to_mail,
                    to_name,
                    cc_mail,
                    cc_name,
                    bcc_mail,
                    bcc_name,
                    subject,
                    answering_content,
                    comment,
                    attachments,
                    is_create
                FROM cx_email_temp
                WHERE cx_email_id = :cx_email_id
            """)
            params = {
                "cx_email_id": domain_data.cx_email_id
            }

            result = await db.execute(query, params)
            row = result.fetchone()

            return {
                "id": row.cx_email_id,
                "lastEditUserId": row.user_id,
                "regDate": row.reg_date,
                "updateDate": row.update_date,
                "fromMail": row.from_mail,
                "fromName": row.from_name,
                "toMail": row.to_mail,
                "toName": row.to_name,
                "ccMail": row.cc_mail,
                "ccName": row.cc_name,
                "bccMail": row.bcc_mail,
                "bccName": row.bcc_name,
                "subject": row.subject,
                "answeringContent": row.answering_content,
                "comment": row.comment,
                "attachments": row.attachments,
                "isCreate": row.is_create
            } if row else False

        except Exception as e:
            logging.error(f"[queries.cx_email_temp.CXEmailTempQuery.get_row] Exception: {e}")
            raise DBError


    @staticmethod
    async def check_has_row(db: AsyncSession, domain_data: InitAnswerDomain):
        try:
            query = text("""
                SELECT id
                FROM cx_email_temp
                WHERE cx_email_id = :cx_email_id
            """)
            params = {
                "cx_email_id": domain_data.id,
            }

            result = await db.execute(query, params)
            row = result.fetchone()

            return True if row else False

        except Exception as e:
            logging.error(f"[queries.cx_email_temp.CXEmailTempQuery.check_has_row] Exception: {e}")
            raise DBError


    @staticmethod
    async def update_row(db: AsyncSession, domain_data: SaveSendInfoDomain):
        try:
            query = text("""
                UPDATE cx_email_temp
                SET
                    user_id = :user_id,
                    from_mail = :from_mail,
                    from_name = :from_name,
                    to_mail = :to_mail,
                    to_name = :to_name,
                    cc_mail = :cc_mail,
                    cc_name = :cc_name,
                    bcc_mail = :bcc_mail,
                    bcc_name = :bcc_name,
                    subject = :subject,
                    answering_content = :answering_content,
                    comment = :comment,
                    attachments = :attachments
                WHERE cx_email_id = :cx_email_id
                    AND company_key = :company_key
            """)
            params = {
                "user_id": domain_data.user_id,
                "from_mail": domain_data.company_email_address,
                "from_name": domain_data.company_email_name,
                "to_mail": domain_data.to_mail if isinstance(domain_data.to_mail, str) else str(domain_data.to_mail),
                "to_name": domain_data.to_name if isinstance(domain_data.to_name, str) else str(domain_data.to_name),
                "cc_mail": domain_data.cc_mail if isinstance(domain_data.cc_mail, str) else str(domain_data.cc_mail),
                "cc_name": domain_data.cc_name if isinstance(domain_data.cc_name, str) else str(domain_data.cc_name),
                "bcc_mail": domain_data.bcc_mail if isinstance(domain_data.bcc_mail, str) else str(domain_data.bcc_mail),
                "bcc_name": domain_data.bcc_name if isinstance(domain_data.bcc_name, str) else str(domain_data.bcc_name),
                "subject": domain_data.subject,
                "answering_content": domain_data.answering_content,
                "comment": domain_data.comment,
                "attachments": domain_data.attachments if isinstance(domain_data.attachments, str) else str(domain_data.attachments) if domain_data.attachments else None,
                "cx_email_id": domain_data.cx_email_id,
                "company_key": domain_data.company_key
            }

            await db.execute(query, params)
            await db.commit()

        except Exception as e:
            logging.error(f"[queries.cx_email_temp.CXEmailTempQuery.update_row] Exception: {e}")
            raise DBError