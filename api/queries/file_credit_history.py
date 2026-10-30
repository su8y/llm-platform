import logging

import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.error import DBError
from domain.user import loginDomain
from utils.date import *


class FileCreditHistoryQuery:

    @staticmethod
    async def decrease_parser_credit_available(db:AsyncSession, company_key, use_parser_credit, drive_id):
        try:
            credit_query = text("""SELECT * FROM file_credit_history WHERE company_key = :company_key ORDER BY reg_date DESC""")
            credit_params = {'company_key': company_key}
            credit_execute = await db.execute(credit_query, credit_params)
            credit_available = credit_execute.fetchone()._mapping
            remain_credit = credit_available['remain_credit']
            query = text("""
                 INSERT INTO file_credit_history (
                     company_key, type, use_credit, remain_credit, charge_credit, reg_date, reg_date_str, drive_id    
                 ) VALUES (
                     :company_key, :type, :use_credit, :remain_credit, :charge_credit, :reg_date, :reg_date_str, :drive_id
                 ) RETURNING * 
                 """)
            await db.execute(query, {
                'company_key': company_key,
                'type': 'system',
                'use_credit': use_parser_credit,
                'charge_credit': 0,
                'remain_credit': remain_credit - use_parser_credit,
                'reg_date': get_utc_now(),
                'reg_date_str': get_utc_now().strftime("%Y-%m-%d"),
                'drive_id': drive_id
            })
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.company_info.CompanyInfoQuery.decrease_parser_credit_available] DBError: {e}")
            raise DBError(e)

    async def insert_credit_history(db:AsyncSession, company_key:str, charge_credit:int):
        try:
            credit_query = text("""SELECT * FROM file_credit_history WHERE company_key = :company_key ORDER BY reg_date desc """)
            credit_params = {'company_key': company_key}
            credit_execute = await db.execute(credit_query, credit_params)
            credit_available = credit_execute.fetchone()
            remain_credit = 0

            if credit_available:
                credit_available = credit_available._mapping
                remain_credit = credit_available.remain_credit + charge_credit
            else:
                remain_credit = charge_credit

            query = text("""
                INSERT INTO file_credit_history (
                    company_key, type, use_credit, remain_credit, charge_credit, reg_date, reg_date_str
                ) VALUES (
                    :company_key, :type, :use_credit, :remain_credit, :charge_credit, :reg_date, :reg_date_str
                ) RETURNING *
            """
            )
            params = {
                'company_key': company_key,
                'type': 'system',
                'use_credit': 0,
                'charge_credit': charge_credit,
                'remain_credit': remain_credit,
                'reg_date': get_utc_now(),
                'reg_date_str': get_utc_now().strftime("%Y-%m-%d")
            }
            result = await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.credit_history.CreditHistoryQuery.insert_credit_history] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_file_credit(db:AsyncSession, company_key):
        try:
            query = text("""
                (SELECT
                    'total' AS type, SUM(charge_credit) AS credit,
                    MAX(reg_date) AS reg_date,
                    (
                        SELECT remain_credit FROM file_credit_history                                                                                                                                                                                                                                                                                                                               
                        WHERE company_key = :company_key AND charge_credit > 0                                                                                                                                                                                                                                                                                                                      
                        ORDER BY reg_date DESC LIMIT 1
                    ) AS latest_remain_credit
                FROM file_credit_history
                WHERE company_key = :company_key
                    AND charge_credit > 0)

                UNION ALL

                (SELECT 'remain' AS type, remain_credit AS credit, reg_date, NULL AS latest_remain_credit
                FROM file_credit_history
                WHERE company_key = :company_key
                    AND charge_credit <= 0
                ORDER BY reg_date DESC LIMIT 1)
            """)
            params = {'company_key': company_key}
            result = await db.execute(query, params)
            rows = result.fetchall()

            if not rows:
                return {"totalCredit": 0, "remainCredit": 0}

            data = {row._mapping['type']: row._mapping for row in rows}

            total_data = data.get('total')
            remain_data = data.get('remain')

            total_credit = total_data['credit'] if total_data else 0
            total_reg_date = total_data['reg_date'] if total_data else None
            remain_credit = remain_data['credit'] if remain_data else 0
            remain_reg_date = remain_data['reg_date'] if remain_data else None

            if not remain_data or (total_reg_date and remain_reg_date and total_reg_date > remain_reg_date):
                total_latest_credit = total_data['latest_remain_credit'] if total_data else 0
                remain_credit = total_latest_credit

            return {"totalCredit": total_credit, "remainCredit": remain_credit}

        except Exception as e:
            logging.error(f"[queries.file_credit_history.FileCreditHistoryQuery.get_file_credit] DBError: {e}")
            raise DBError(e)
