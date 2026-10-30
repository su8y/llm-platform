import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.error import DBError
from domain.email import *
from domain.system import *



class CXEmailPromptQuery:
    @staticmethod
    async def insert_row(db:AsyncSession, domain_data:InsertEmailPromptDomain):
        try:
            query = text("""
                INSERT INTO cx_email_prompt (
                    company_key,
                    prompt_name,
                    prompt,
                    reg_date,
                    comment,
                    writer
                ) VALUES (
                    :company_key,
                    :prompt_name,
                    :prompt,
                    :reg_date,
                    :comment,
                    :writer
                )
            """)
            params = {
                "company_key": domain_data.company_key,
                "prompt_name": domain_data.prompt_name,
                "prompt": domain_data.prompt,
                "reg_date": domain_data.current_time,
                "comment": domain_data.comment,
                "writer": domain_data.writer
            }
            await db.execute(query, params)
            await db.commit()

        except Exception as e:
            logging.error(f"[queries.cx_email_prompt.CXEmailPromptQuery.insert_row] Exception: {e}")
            raise DBError


    @staticmethod
    async def get_all_email_prompt_by_company_key(db:AsyncSession, domain_data):
        try:
            query = text("""
                SELECT prompt_name, prompt, reg_date, comment, writer
                FROM cx_email_prompt
                WHERE company_key = :company_key
                ORDER BY reg_date DESC
            """)
            params = {"company_key": domain_data.company_key}
            execute = await db.execute(query, params)
            rows = execute.fetchall()

            domain_data.rows = [{
                "promptName": row.prompt_name,
                "prompt": row.prompt,
                "regDate": row.reg_date,
                "comment": row.comment,
                "writer": row.writer
            } for row in rows] if rows else []

        except Exception as e:
            logging.error(f"[queries.cx_email_history.CXEmailHistoryQuery.insert_history_row] Exception: {e}")
            raise DBError