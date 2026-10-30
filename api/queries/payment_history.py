import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from utils.error import DBError



class PaymentHistoryQuery:
    @staticmethod
    async def insert_payment_history(db:AsyncSession, data:dict):
        try:
            query = text("""
                INSERT INTO payment_history (company_key, user_id, plan_info_id, plan_period, reg_date, type, success, card_number, approval, actual_payment_amount)
                VALUES (:company_key, :user_id, :plan_info_id, :plan_period, :reg_date, :type, :success, :card_number, :approval, :actual_payment_amount)
            """)
            params = {
                "company_key": data["company_key"],
                "user_id": data["user_id"],
                "plan_info_id": data["plan_info_id"],
                "plan_period": data["plan_period"],
                "reg_date": data["reg_date"],
                "type": data["type"],
                "success": data["success"],
                "card_number": data["card_number"],
                "approval": data["approval"],
                "actual_payment_amount": data["actual_payment_amount"]
            }
            result = await db.execute(query, params).scalar_one()
            await db.commit()
            return result
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.payment_history.PaymentHistoryQuery.insert_payment_history] DBError: {e}")
            raise DBError(e)
