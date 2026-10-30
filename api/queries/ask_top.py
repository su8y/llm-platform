import logging

from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.error import DBError



class AskTopQuery:
    @staticmethod
    async def get_top(db: AsyncSession, company_key: str, start_date: datetime, end_date: datetime):
        try:
            query = text(
                """
                    SELECT rank1, rank1_count, rank2, rank2_count, rank3, rank3_count
                    FROM ask_top
                    WHERE company_key = :company_key
                    AND created_at >= :start_date
                    AND created_at <= :end_date
                """
            )
            params = {
                "company_key": company_key,
                "start_date": start_date,
                "end_date": end_date
            }
            result = await db.execute(query, params)
            rows = result.fetchall()
            return [
                {
                    "rank1": row[0], "rank1_count": row[1],
                    "rank2": row[2], "rank2_count": row[3],
                    "rank3": row[4], "rank3_count": row[5],
                } for row in rows
            ] if rows else None
        
        except Exception as e:
            logging.error(f"[queries.ask_top.AskTopQuery.get_top] Exception: {e}")
            raise DBError(e)