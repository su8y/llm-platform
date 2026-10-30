import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.error import DBError
from domain.email import SendEmailDomain



class CXEmailReferencesQuery:
    @staticmethod
    async def insert_references_row(db: AsyncSession, domain_data: SendEmailDomain):
        try:
            query = text("""
                INSERT INTO cx_email_references (
                    first_message_id,
                    message_id,
                    created_at
                ) VALUES (
                    :first_message_id,
                    :message_id,
                    :created_at
                )
            """)
            params = {
                "first_message_id": domain_data.first_message_id,
                "message_id": domain_data.to_message_id,
                "created_at": domain_data.current_time
            }
            await db.execute(query, params)
            await db.commit()

        except Exception as e:
            logging.error(f"[queries.cx_email_history.CXEmailHistoryQuery.insert_history_row] Exception: {e}")
            raise DBError