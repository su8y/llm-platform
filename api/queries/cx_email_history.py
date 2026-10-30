import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.error import DBError
from domain.email import *



class CXEmailHistoryQuery:
    @staticmethod
    async def insert_history_row(db: AsyncSession, domain_data):
        try:
            query = text("""
                INSERT INTO cx_email_history (
                    company_key,
                    cx_email_id,
                    user_id,
                    action_code,
                    reg_date
                ) VALUES (
                    :company_key,
                    :cx_email_id,
                    :user_id,
                    :action_code,
                    :reg_date
                )
            """)
            params = {
                "company_key": domain_data.company_key,
                "cx_email_id": domain_data.id,
                "user_id": domain_data.user_id,
                "action_code": domain_data.action_code,
                "reg_date": domain_data.current_time,
            }
            await db.execute(query, params)
            await db.commit()

        except Exception as e:
            logging.error(f"[queries.cx_email_history.CXEmailHistoryQuery.insert_history_row] Exception: {e}")
            raise DBError


    @staticmethod
    async def get_history_of_email(db: AsyncSession, domain_data):
        try:
            query = text("""
                SELECT
                    user_id,
                    action_code,
                    reg_date
                FROM cx_email_history
                WHERE company_key = :company_key
                    AND cx_email_id = :cx_email_id
                ORDER BY reg_date DESC
            """)
            params = {
                "company_key": domain_data.company_key,
                "cx_email_id": domain_data.id,
            }
            execute = await db.execute(query, params)
            rows = execute.fetchall()

            return [{
                "userId": row.user_id,
                "actionCode": row.action_code,
                "regDate": row.reg_date
            } for row in rows] if rows else None

        except Exception as e:
            logging.error(f"[queries.cx_email.CXEmailQuery.insert_history_row] Exception: {e}")
            raise DBError