import logging

import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.error import DBError
from domain.user import loginDomain


class CreditHistoryQuery:

    @staticmethod
    async def insert_credit_history(db:AsyncSession, domain_data:loginDomain):
        try:
            credit_query = text("""SELECT credit_available FROM company_info WHERE company_key = :company_key""")
            credit_params = {'company_key': domain_data.company_key}
            credit_execute = await db.execute(credit_query, credit_params)
            credit_available = credit_execute.fetchone()[0]
            query = text("""
                INSERT INTO credit_history (
                    company_key, credit_type, credit, after_credit_available, reg_date, payment_id
                ) VALUES (
                    :company_key, :credit_type, :credit, :after_credit_available, :reg_date, :payment_id
                ) RETURNING *
            """
            )
            params = {
                'company_key': domain_data.company_key,
                'credit_type': domain_data.credit_type,
                'credit': domain_data.credit,
                'after_credit_available': credit_available + domain_data.credit,
                'reg_date': domain_data.reg_date,
                'payment_id': domain_data.first_payment_id
            }
            result = await db.execute(query, params)
            return result.fetchone()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.credit_history.CreditHistoryQuery.insert_credit_history] DBError: {e}")
            raise DBError(e)