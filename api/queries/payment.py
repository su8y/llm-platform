import logging
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.error import DBError
from utils.constants import *
from domain.user import loginDomain


class PaymentQuery:
    
    @staticmethod
    async def insert_plan_payment(db:AsyncSession, domain_data: loginDomain):
        try:
            inserted_ids = []
            
            # 트랜잭션 내에서 여러 레코드 삽입
            async with db.begin_nested():
                for data in domain_data.init_plan:
                    # 각 데이터 항목에 대한 쿼리 실행
                    insert_query = text("""
                        INSERT INTO payment (
                            company_key, plan_info_id, payment_history_id, start_date, end_date, 
                            payment_date, payment_period, payment_status, change_type, use_credit, 
                            reg_date, is_target_renewal, attempt_count
                        ) VALUES (
                            :company_key, :plan_info_id, :payment_history_id, :start_date, :end_date, 
                            :payment_date, :payment_period, :payment_status, :change_type, :use_credit, 
                            :reg_date, :is_target_renewal, :attempt_count
                        ) RETURNING id
                    """)
                    
                    result = await db.execute(insert_query, data)
                    inserted_id = result.scalar_one()
                    inserted_ids.append(inserted_id)
            
            await db.commit()
            return inserted_ids[0] if inserted_ids else None
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.payment.PaymentQuery.insert_plan_payment] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_current_plan_info(db:AsyncSession, company_key:str, current_date:datetime=None):
        try:
            # 기본 쿼리 구성
            query = """
                SELECT 
                    p.id, p.start_date, p.end_date, p.payment_date, p.payment_period, 
                    p.payment_status, p.change_type, p.use_credit, p.is_target_renewal, 
                    p.company_key, ci.credit_available, p.plan_info_id, pi.init_credit, pi.plan_name
                FROM payment p
                JOIN company_info ci ON p.company_key = ci.company_key
                JOIN plan_info pi ON p.plan_info_id = pi.id
                WHERE p.company_key = :company_key
            """
            
            params = {"company_key": company_key}
                
            if current_date:
                query += " AND p.end_date >= :current_date"
                params["current_date"] = current_date
            
            # 정렬 및 결과 제한
            query += " ORDER BY p.start_date ASC"
            
            result = await db.execute(text(query), params)
            rows = result.fetchall()
                
            return [{
                "id": row[0],
                "start_date": row[1],
                "end_date": row[2],
                "payment_date": row[3],
                "payment_period": row[4],
                "payment_status": row[5],
                "change_type": row[6],
                "use_credit": row[7],
                "is_target_renewal": row[8],
                "company_key": row[9],
                "credit_available": row[10],
                "plan_info_id": row[11],
                "init_credit": row[12],
                "plan_name": row[13],
            } for row in rows] if rows else []
        except Exception as e:
            logging.error(f"[queries.payment.PaymentQuery.get_plan_info] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_payment_history(db:AsyncSession, page:int, per_page:int, company_key:str, plan_name=None, type=None):
        try:
            offset = (page - 1) * per_page
            
            # 카운트 쿼리 생성
            count_query = """
                SELECT COUNT(*)
                FROM payment p
                JOIN plan_info pi ON p.plan_info_id = pi.id
                WHERE p.company_key = :company_key 
                AND p.payment_status = 'complete'
            """
            
            # 데이터 쿼리 생성
            data_query = """
                SELECT 
                    pi.plan_name, p.start_date, p.end_date, 
                    pi.init_credit, p.use_credit, pi.plan_price
                FROM payment p
                JOIN plan_info pi ON p.plan_info_id = pi.id
                WHERE p.company_key = :company_key 
                AND p.payment_status = 'complete'
            """
            
            params = {"company_key": company_key, "offset": offset, "per_page": per_page}
            
            # 추가 필터 적용
            if plan_name:
                count_query += " AND pi.plan_name = :plan_name"
                data_query += " AND pi.plan_name = :plan_name"
                params["plan_name"] = plan_name
                
            # 정렬 및 페이지네이션
            data_query += " ORDER BY p.start_date DESC LIMIT :per_page OFFSET :offset"
            
            # 쿼리 실행
            count_result = await db.execute(text(count_query), params)
            count = count_result.scalar()
            
            data_result = await db.execute(text(data_query), params)
            rows = data_result.fetchall()
            
            if count == 0:
                return {"count": 0, "post": []}
                
            # 결과 포맷팅
            formatted_results = [
                {
                    "planName": row[0],
                    "startDate": row[1],
                    "endDate": row[2],
                    "initCredit": row[3],
                    "useCredit": row[4],
                    "paymentPrice": row[5],
                } for row in rows
            ]
            
            return {
                "count": count,
                "post": formatted_results
            }
        except Exception as e:
            logging.error(f"[queries.payment.PaymentQuery.get_payment_history] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_payment_history_count(db:AsyncSession, company_key:str, plan_name=None, type=None):
        try:
            query = """
                SELECT COUNT(*)
                FROM payment p
                JOIN plan_info pi ON p.plan_info_id = pi.id
                LEFT JOIN payment_history ph ON p.payment_history_id = ph.id
                WHERE p.company_key = :company_key 
                AND p.payment_status = 'complete'
            """
            
            params = {"company_key": company_key}
            
            if plan_name:
                query += " AND pi.plan_name = :plan_name"
                params["plan_name"] = plan_name
                
            if type:
                query += " AND ph.type = :type"
                params["type"] = type
                
            result = await db.execute(text(query), params)
            count = result.scalar()
            
            return count
        except Exception as e:
            logging.error(f"[queries.payment.PaymentQuery.get_payment_history_count] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_target_upgrade_ids(db:AsyncSession, company_key:str, current_date:datetime):
        try:
            plan_info_ids = [INIT_PLAN_ID, EXPIRED_PLAN_INFO_ID]
            
            query = text("""
                SELECT id
                FROM payment
                WHERE company_key = :company_key
                    AND start_date <= :current_date
                    AND end_date >= :current_date
                    AND plan_info_id NOT IN :plan_info_ids
            """)
            
            params = {
                "company_key": company_key, 
                "current_date": current_date, 
                "plan_info_ids": tuple(plan_info_ids)
            }
            
            result = await db.execute(query, params)
            rows = result.fetchall()
            
            return [row[0] for row in rows] if rows else []
        except Exception as e:
            logging.error(f"[queries.payment.PaymentQuery.get_target_upgrade_row] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_plan_until_end(db:AsyncSession, company_key:str, current_date:datetime):
        try:
            plan_info_ids = [INIT_PLAN_ID, EXPIRED_PLAN_INFO_ID]
            
            query = text("""
                SELECT id
                FROM payment
                WHERE company_key = :company_key
                    AND (
                        start_date > :current_date
                        OR
                        (start_date <= :current_date AND end_date >= :current_date)
                    )
                    AND plan_info_id NOT IN :plan_info_ids
            """)
            
            params = {
                "company_key": company_key, 
                "current_date": current_date, 
                "plan_info_ids": tuple(plan_info_ids)
            }
            
            result = await db.execute(query, params)
            rows = result.fetchall()
            
            return [row[0] for row in rows] if rows else []
        except Exception as e:
            logging.error(f"[queries.payment.PaymentQuery.get_plan_until_end] DBError: {e}")
            raise DBError(e)
    
    @staticmethod
    async def is_current_plan(db:AsyncSession, company_key:str, current_date:datetime):
        try:
            plan_info_ids = [INIT_PLAN_ID, EXPIRED_PLAN_INFO_ID]
            
            query = text("""
                SELECT id
                FROM payment
                WHERE company_key = :company_key
                    AND start_date <= :current_date
                    AND end_date >= :current_date
                    AND plan_info_id NOT IN :plan_info_ids
            """)
            
            params = {
                "company_key": company_key, 
                "current_date": current_date, 
                "plan_info_ids": tuple(plan_info_ids)
            }
            
            result = await db.execute(query, params)
            row = result.fetchone()
            
            return True if row else False
        except Exception as e:
            logging.error(f"[queries.payment.PaymentQuery.is_current_plan] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_target_downgrade_ids(db:AsyncSession, company_key:str, current_date:datetime):
        try:
            query = text("""
                SELECT id
                FROM payment
                WHERE company_key = :company_key
                    AND start_date > :current_date
            """)
            
            params = {"company_key": company_key, "current_date": current_date}
            result = await db.execute(query, params)
            rows = result.fetchall()
            
            return [row[0] for row in rows] if rows else []
        except Exception as e:
            logging.error(f"[queries.payment.PaymentQuery.get_target_downgrade_ids] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_plan_info_id_all_plan(db:AsyncSession, ids:list, plan_info_id:int, current_date:datetime):
        try:
            plan_info_ids = [INIT_PLAN_ID, EXPIRED_PLAN_INFO_ID]
            
            query = text("""
                UPDATE payment
                SET plan_info_id = :plan_info_id
                WHERE id IN :ids
                    AND (
                        start_date > :current_date
                        OR
                        (start_date <= :current_date AND end_date >= :current_date)
                    )
                    AND plan_info_id NOT IN :plan_info_ids
            """)
            
            params = {
                "ids": tuple(ids), 
                "plan_info_id": plan_info_id, 
                "current_date": current_date, 
                "plan_info_ids": tuple(plan_info_ids)
            }
            
            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.payment.PaymentQuery.update_plan_payment] DBError: {e}")
            raise DBError(e)
    
    @staticmethod
    async def update_before_end_date(db:AsyncSession, ids:list, current_date:datetime):
        try:
            end_date = current_date - timedelta(microseconds=1)
            
            query = text("""
                UPDATE payment
                SET end_date = :end_date
                WHERE id IN :ids
                    AND (start_date <= :current_date AND end_date >= :current_date)
            """)
            
            params = {
                "ids": tuple(ids), 
                "end_date": end_date, 
                "current_date": current_date
            }
            
            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.payment.PaymentQuery.update_before_end_date] DBError: {e}")
            raise DBError(e)
    
    @staticmethod
    async def update_trial_plan(db:AsyncSession, company_key:str, current_date:datetime):
        try:
            query = text("""
                UPDATE payment
                SET end_date = :end_date
                WHERE company_key = :company_key
                    AND start_date <= :current_date
                    AND end_date >= :current_date
                    AND plan_info_id = :plan_info_id
            """)
            
            params = {
                "end_date": current_date - timedelta(microseconds=1), 
                "company_key": company_key, 
                "current_date": current_date, 
                "plan_info_id": 3
            }
            
            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.payment.PaymentQuery.update_trial_plan] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def delete_expired_plan(db:AsyncSession, company_key:str):
        try:
            query = text("""
                DELETE FROM payment
                WHERE company_key = :company_key
                    AND plan_info_id = :plan_info_id
            """)
            
            params = {"company_key": company_key, "plan_info_id": 8}
            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.payment.PaymentQuery.delete_expired_plan] DBError: {e}")
            raise DBError(e)