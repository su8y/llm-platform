import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from domain.prompt import *
from module.Mail.prompt import SYSTEM_MESSAGE
from utils.date import adapt_timezone_datetime_to_datetime
from utils.constants import DEFAULT_MAIL_PROMPT_COMMENT
from utils.error import DBError



class MailPromptHistoryQuery:

    @staticmethod
    async def create_prompt(db:AsyncSession, domain_data:insertPromptDomain):
        try:
            query = text("""
                INSERT INTO mail_prompt_history (company_key, prompt_name, prompt, comment, writer, reg_date)
                VALUES (:company_key, :prompt_name, :prompt, :comment, :writer, :reg_date)
            """)
            select_query = text("""
                SELECT id, company_key, prompt_name, reg_date, prompt, comment, writer
                FROM mail_prompt_history
                WHERE id = :id
            """)

            params = {
                "company_key": domain_data.company_key,
                "prompt_name": domain_data.prompt_name,
                "prompt": domain_data.prompt,
                "comment": domain_data.comment,
                "writer": domain_data.user_id,
                "reg_date": domain_data.reg_date
            }

            result = await db.execute(query, params)
            inserted_id = result.lastrowid
            row = (await db.execute(select_query, {"id": inserted_id})).fetchone()
            await db.commit()

            return {
                "id": row.id,
                "company_key": row.company_key,
                "prompt_name": row.prompt_name,
                "reg_date": adapt_timezone_datetime_to_datetime(row.reg_date, "UTC"),
                "prompt": row.prompt,
                "comment": row.comment,
                "writer": row.writer
            }
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.prompt_history.PromptHistoryQuery.create_prompt] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_prompt(db:AsyncSession, domain_data:getPromptDomain):
        try:
            is_llm = True if not domain_data.prompt_id else False  # 실제 LLM 동작할 때 prompt를 가져오는 경우, id를 인자로 입력하지 않음

            if is_llm:
                query = text("""
                    SELECT id, prompt, comment
                    FROM prompt_history
                    WHERE company_key = :company_key
                    ORDER BY reg_date DESC
                    LIMIT 1
                """)
                params = {"company_key": domain_data.company_key}
            else:
                query = text("""
                    SELECT prompt, comment
                    FROM mail_prompt_history
                    WHERE company_key = :company_key AND id = :id
                    LIMIT 1
                """)
                params = {"company_key": domain_data.company_key, "id": domain_data.prompt_id}

            result = await db.execute(query, params)
            row = result.fetchone()

            if not row:
                return {"prompt": SYSTEM_MESSAGE, "comment": DEFAULT_MAIL_PROMPT_COMMENT}

            if is_llm:
                return {"id": row.id, "prompt": row.prompt, "comment": row.comment}
            else:
                return {"prompt": row.prompt, "comment": row.comment}

        except Exception as e:
            logging.error(f"[queries.prompt_history.PromptHistoryQuery.get_prompt] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_prompt_version(db:AsyncSession, domain_data:getVersionDomain):
        try:
            query = text("""
                SELECT id, reg_date
                FROM mail_prompt_history
                WHERE company_key = :company_key
                ORDER BY reg_date DESC
            """)
            print('db : ', db)
            result = await db.execute(query, {"company_key": domain_data.company_key})
            rows = result.fetchall()

            if not rows:
                return [{"prompt_id": 2, "version": "sample"}]

            return [
                {
                    "prompt_id": row.id,
                    "version": adapt_timezone_datetime_to_datetime(row.reg_date, "UTC") if isinstance(row.reg_date, datetime) else row.reg_date
                }
                for row in rows
            ]

        except Exception as e:
            logging.error(f"[queries.mail_prompt_history.PromptHistoryQuery.get_prompt_version] DBError: {e}")
            raise DBError(e)
