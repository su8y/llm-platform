import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from utils.error import DBError



class PlanInfoQuery:
    
    @staticmethod
    async def insert_metadata(db:AsyncSession, **kwargs):
        try:
            query = text("""
                INSERT INTO plan_info (id, plan_name, plan_price, init_credit, model)
                VALUES (:id, :plan_name, :plan_price, :init_credit, :model)
            """)
            await db.execute(query, kwargs)
            await db.commit()
        except Exception as e:
            logging.error(f"[queries.plan_info.PlanInfoQuery.insert_metadata] DBError: {e}")
            raise DBError(e)

    
    @staticmethod
    async def get_plan_info(db:AsyncSession, is_show:bool):
        try:
            query = text("""
                SELECT * FROM plan_info WHERE is_show = :is_show
            """)
            result = await db.execute(query, {"is_show": is_show}).fetchall()
            return [
                {
                    "id": row[0],
                    "plan_name": row[1],
                    "plan_price": row[2],
                    "init_credit": row[3],
                } for row in result
            ]
        except Exception as e:
            logging.error(f"[queries.plan_info.PlanInfoQuery.get_plan_info] DBError: {e}")
            raise DBError(e)