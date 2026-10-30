import os
import logging
from uuid import uuid4
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.error import DBError
from domain.playground import *
from domain.prompt import *
from domain.user import *
from domain.drive import *
from domain.plan import *



class CompanyInfoQuery:

    @staticmethod
    async def register(
        db:AsyncSession,
        domain_data:registerDomain,
    ):

        try:
            query = text("""
                INSERT INTO company_info (
                    company_key, company_name, master_id, reg_date, lang, expired_date,
                    plan_info_id, credit_available, parser_credit_available, vector_db_index, vector_db_namespace
                ) VALUES (
                    :company_key, :company_name, :master_id, :reg_date, :lang, :expired_date,
                    :plan_info_id, :credit_available, :parser_credit_available, :vector_db_index, :vector_db_namespace
                )
            """)

            await db.execute(query, {
                "company_key": domain_data.company_key,
                'company_name': domain_data.company_name,
                'master_id': domain_data.user_id,
                'reg_date': domain_data.reg_date,
                'lang': domain_data.lang,
                'expired_date': domain_data.expired_date,
                'plan_info_id': domain_data.plan_info_id,
                'credit_available': domain_data.credit_available,
                'parser_credit_available': domain_data.parser_credit_available,
                'vector_db_index': domain_data.vector_db_index,
                'vector_db_namespace': domain_data.vector_db_namespace
            })
            await db.commit()

            # 결과를 직접 딕셔너리로 변환
            return {
                "company_key": domain_data.company_key,  # company_key 위치에 따라 인덱스 조정 필요
                "company_name": domain_data.company_name,
                "master_id": domain_data.user_id,
                "reg_date": domain_data.reg_date,
                "status": 0,  # 기본값
                "credit_available": domain_data.credit_available,  # 기본값
                "parser_credit_available": domain_data.parser_credit_available,  # 기본값
                "plan_info_id": domain_data.plan_info_id,  # 초기값
                "model": None,  # 초기값
                "vector_db_index": domain_data.vector_db_index,  # 기본값
                "vector_db_namespace": domain_data.vector_db_namespace,
                "greetings": None,
                "lang": domain_data.lang,
                "trial_expired_day_cnt": None,
                "expired_date": domain_data.expired_date
            }

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.company_info.CompanyInfoQuery.register] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_pinecone_info(db:AsyncSession, company_key:str):
        try:
            query = text("SELECT vector_db_index, vector_db_namespace FROM company_info WHERE company_key = :company_key")
            result = await db.execute(query, {"company_key": company_key})
            row = result.fetchone()
            return {"vector_db_index": row[0], "vector_db_namespace": row[1]} if row else None

        except Exception as e:
            logging.error(f"[queries.company_info.CompanyInfoQuery.get_pinecone_info] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_company_info(db:AsyncSession, company_key:str):
        try:
            query = text("""
                SELECT ci.*, pi.model 
                FROM company_info ci
                LEFT JOIN plan_info pi ON ci.plan_info_id = pi.id
                WHERE ci.company_key = :company_key
            """)
            result = await db.execute(query, {"company_key": company_key})
            row = result.fetchone()

            if not row:
                return None

            # 결과를 직접 딕셔너리로 변환
            model_value = row[-1]  # model은 마지막 열로 가정
            return {
                "company_key": row[0],
                "company_name": row[1],
                "master_id": row[3],  # 열 위치는 DB 스키마에 따라 조정 필요
                "reg_date": row[4],
                "status": row[5],
                "credit_available": row[7],
                "parser_credit_available": row[14],
                "plan_info_id": row[6],
                "model": model_value,
                "vector_db_index": row[8],
                "vector_db_namespace": row[9],
                "greetings": row[10],
                "lang": row[11],
                "trial_expired_day_cnt": row[12],
                "expired_date": row[13]
            }

        except Exception as e:
            logging.error(f"[queries.company_info.CompanyInfoQuery.get_company_info] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_company_list(db:AsyncSession, status:int=None):
        try:
            if status is None:
                query = text("SELECT * FROM company_info")
                result = await db.execute(query)
            else:
                query = text("SELECT * FROM company_info WHERE status = :status")
                result = await db.execute(query, {"status": status})

            rows = result.fetchall()
            if not rows:
                return []

            # 결과를 직접 딕셔너리 리스트로 변환
            companies = []
            for row in rows:
                companies.append({
                    "company_key": row[0],
                    "company_name": row[1],
                    "master_id": row[3],
                    "reg_date": row[4],
                    "status": row[5],
                    "credit_available": row[7],
                    "parser_credit_available": row[14],
                    "plan_info_id": row[6],
                    "model": None,  # model 정보는 별도 쿼리 필요
                    "vector_db_index": row[8],
                    "vector_db_namespace": row[9],
                    "greetings": row[10],
                    "lang": row[11],
                    "trial_expired_day_cnt": row[12],
                    "expired_date": row[13]
                })
            return companies

        except Exception as e:
            logging.error(f"[queries.company_info.CompanyInfoQuery.get_company_list] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_info_by_company_name(db:AsyncSession, domain_data:registerDomain):
        try:
            query = text("""
                SELECT ci.*, pi.model 
                FROM company_info ci
                LEFT JOIN plan_info pi ON ci.plan_info_id = pi.id
                WHERE ci.company_name = :company_name
            """)
            result = await db.execute(query, {"company_name": domain_data.company_name})
            row = result.fetchone()

            if not row:
                return None

            # 결과를 직접 딕셔너리로 변환
            model_value = row[-1]  # model은 마지막 열로 가정
            return {
                "company_key": row[0],
                "company_name": row[1],
                "master_id": row[3],
                "reg_date": row[4],
                "status": row[5],
                "credit_available": row[7],
                "parser_credit_available": row[14],
                "plan_info_id": row[6],
                "model": model_value,
                "vector_db_index": row[8],
                "vector_db_namespace": row[9],
                "greetings": row[10],
                "lang": row[11],
                "trial_expired_day_cnt": row[12],
                "expired_date": row[13]
            }

        except Exception as e:
            logging.error(f"[queries.company_info.CompanyInfoQuery.get_info_by_company_name] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_company_name_by_company_key(db:AsyncSession, company_key):
        try:
            query = text("SELECT company_name FROM company_info WHERE company_key = :company_key")
            result = await db.execute(query, {"company_key": company_key})
            row = result.fetchone()
            return row[0] if row else None

        except Exception as e:
            logging.error(f"[queries.company_info.CompanyInfoQuery.get_company_name_by_company_key] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_credit_available(db:AsyncSession, domain_data:getCreditDomain):
        try:
            query = text("SELECT credit_available FROM company_info WHERE company_key = :company_key")
            result = await db.execute(query, {"company_key": domain_data.company_key})
            row = result.fetchone()
            return row[0] if row else None

        except Exception as e:
            logging.error(f"[queries.company_info.CompanyInfoQuery.get_credit_available] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_greetings(db:AsyncSession, domain_data:getGreetingsDomain):
        try:
            query = text("SELECT greetings FROM company_info WHERE company_key = :company_key")
            result = await db.execute(query, {"company_key": domain_data.company_key})
            row = result.fetchone()
            return row[0] if row else None

        except Exception as e:
            logging.error(f"[queries.company_info.CompanyInfoQuery.get_greetings] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_credit(db:AsyncSession, company_key):
        try:
            query = text("""
                SELECT ci.credit_available, pi.init_credit 
                FROM company_info ci
                LEFT JOIN plan_info pi ON ci.plan_info_id = pi.id
                WHERE ci.company_key = :company_key
            """)
            result = await db.execute(query, {"company_key": company_key})
            row = result.fetchone()
            return {"useAbleCredit": row[0], "totalCredit": row[1]} if row else {"useAbleCredit": 0, "totalCredit": 0}

        except Exception as e:
            logging.error(f"[queries.company_info.CompanyInfoQuery.get_credit] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_current_credit(db:AsyncSession, domain_data:GetCurrentPlanDomain):
        try:
            query = text("""
                SELECT ci.credit_available, pi.init_credit
                FROM company_info ci
                LEFT JOIN plan_info pi
                    ON ci.plan_info_id = pi.id
                WHERE ci.company_key = :company_key
            """)
            result = await db.execute(query, {"company_key": domain_data.company_key})
            row = result.fetchone()
            return {"useAbleCredit": row[0], "totalCredit": row[1]} if row else {"useAbleCredit": 0, "totalCredit": 0}

        except Exception as e:
            logging.error(f"[queries.company_info.CompanyInfoQuery.get_credit] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_mcp_token(db, domain_data):
        try:
            query = text("""
                SELECT ci.mcp_token
                FROM company_info ci
                WHERE ci.company_key = :company_key
            """)
            result = await db.execute(query, {"company_key": domain_data.company_key})
            row = result.fetchone()
            return row[0] if row else None

        except Exception as e:
            logging.error(f"[queries.company_info.CompanyInfoQuery.get_model] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_model(db:AsyncSession, company_key):
        try:
            query = text("""
                SELECT pi.model 
                FROM company_info ci
                LEFT JOIN plan_info pi ON ci.plan_info_id = pi.id
                WHERE ci.company_key = :company_key
            """)
            result = await db.execute(query, {"company_key": company_key})
            row = result.fetchone()
            return row[0] if row else None

        except Exception as e:
            logging.error(f"[queries.company_info.CompanyInfoQuery.get_model] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def update_email_setting(db:AsyncSession, company_key:str, email_available:bool, from_address:str, from_name:str) -> None:
        """AI 메일 기능 플래그와 발신 주소를 설정한다. 이미 입력된 발신 주소/이름은 유지한다."""
        try:
            query = text("""
                UPDATE company_info
                SET email_available = :email_available,
                    email_from_address = COALESCE(email_from_address, :from_address),
                    email_from_name = COALESCE(email_from_name, :from_name)
                WHERE company_key = :company_key
            """)
            await db.execute(query, {
                "company_key": company_key,
                "email_available": email_available,
                "from_address": from_address,
                "from_name": from_name,
            })
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.company_info.CompanyInfoQuery.update_email_setting] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_to_address(db:AsyncSession, domain_data):
        try:
            query = text("""
                SELECT email_from_address, email_from_name
                FROM company_info
                WHERE company_key = :company_key
            """)
            result = await db.execute(query, {"company_key": domain_data.company_key})
            row = result.fetchone()
            return (row[0], row[1]) if row else (None, None)

        except Exception as e:
            logging.error(f"[queries.company_info.CompanyInfoQuery.get_to_address] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_store(db, company_key):
        try:
            query = text("""
                    SELECT store_name, company_name
                    FROM company_info
                    WHERE company_key = :company_key
                """)
            params = {"company_key": company_key}
            result = await db.execute(query, params)
            row = result.fetchone()
            return (row.store_name, row.company_name) if row else (False, False)

        except Exception as e:
            logging.error(f"[queries.company_info.CompanyInfoQuery.get_store] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def update_plan(db:AsyncSession, company_key):
        try:
            query = text("""
                UPDATE company_info 
                SET status = 1
                WHERE company_key = :company_key
                RETURNING status
            """)
            result = await db.execute(query, {"company_key": company_key})
            row = result.fetchone()
            await db.commit()
            return row[0]

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.company_info.CompanyInfoQuery.update_plan] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def charge_credit(db:AsyncSession, company_key, charge_credit):
        try:
            query = text("""
                UPDATE company_info 
                SET credit_available = COALESCE(credit_available, 0) + :charge_credit
                WHERE company_key = :company_key
                RETURNING credit_available
            """)
            result = await db.execute(query, {
                "company_key": company_key,
                "charge_credit": charge_credit
            })
            row = result.fetchone()
            await db.commit()
            return row[0]

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.company_info.CompanyInfoQuery.charge_credit] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def adapt_plan(db:AsyncSession, domain_data:loginDomain):
        try:
            # 먼저 회사 정보 확인
            check_query = text("SELECT 1 FROM company_info WHERE company_key = :company_key")
            result = await db.execute(check_query, {"company_key": domain_data.company_key})
            exists = result.fetchone()
            if not exists:
                logging.info(f"[queries.company_info.CompanyInfoQuery.adapt_plan] company_key {domain_data.company_key} not found")
                raise DBError(f"[queries.company_info.CompanyInfoQuery.adapt_plan] company_key {domain_data.company_key} not found")

            # 초기 크레딧 가져오기
            init_credit_query = text("SELECT init_credit FROM plan_info WHERE id = :plan_info_id")
            result = await db.execute(init_credit_query, {"plan_info_id": domain_data.plan_info_id})
            init_credit = result.fetchone()[0]

            # 플랜 업데이트
            update_query = text("""
                UPDATE company_info 
                SET plan_info_id = :plan_info_id, 
                    status = 1, 
                    credit_available = :init_credit,
                    expired_date = :expired_date
                WHERE company_key = :company_key
            """)

            await db.execute(update_query, {
                "company_key": domain_data.company_key,
                "plan_info_id": domain_data.plan_info_id,
                "init_credit": init_credit,
                "expired_date": domain_data.expired_date
            })
            await db.commit()

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.company_info.CompanyInfoQuery.adapt_plan] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def upgrade_plan(db:AsyncSession, company_key, plan_info_id):
        try:
            # 먼저 회사 정보 확인
            check_query = text("""
                SELECT credit_available 
                FROM company_info 
                WHERE company_key = :company_key
            """)
            result = await db.execute(check_query, {"company_key": company_key})
            row = result.fetchone()
            if not row:
                logging.info(f"[queries.company_info.CompanyInfoQuery.upgrade_plan] company_key {company_key} not found")
                raise DBError(f"[queries.company_info.CompanyInfoQuery.upgrade_plan] company_key {company_key} not found")

            current_credit = row[0]

            # 초기 크레딧 가져오기
            init_credit_query = text("SELECT init_credit FROM plan_info WHERE id = :plan_info_id")
            result = await db.execute(init_credit_query, {"plan_info_id": plan_info_id})
            init_credit = result.fetchone()[0]

            # 플랜 업그레이드
            update_query = text("""
                UPDATE company_info 
                SET plan_info_id = :plan_info_id, 
                    status = 1, 
                    credit_available = :new_credit
                WHERE company_key = :company_key
                RETURNING credit_available
            """)
            result = await db.execute(update_query, {
                "company_key": company_key,
                "plan_info_id": plan_info_id,
                "new_credit": init_credit - current_credit
            })
            row = result.fetchone()
            await db.commit()
            return row[0]

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.company_info.CompanyInfoQuery.upgrade_plan] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def decrease_credit_available(db:AsyncSession, company_key):
        """Do not use on API because decrease credit after LLM. It should activate on Module"""
        try:
            query = text("""
                UPDATE company_info 
                SET credit_available = credit_available - 1
                WHERE company_key = :company_key
            """)
            params = {"company_key": company_key}
            await db.execute(query, params)
            await db.commit()

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.company_info.CompanyInfoQuery.decrease_credit_available] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_greetings(db:AsyncSession, domain_data:updateGreetingsDomain):
        try:
            query = text("""
                UPDATE company_info 
                SET greetings = :greetings
                WHERE company_key = :company_key
            """)
            params = {
                "company_key": domain_data.company_key,
                "greetings": domain_data.greetings
            }

            await db.execute(query, params)
            await db.commit()
            return True

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.company_info.CompanyInfoQuery.update_greetings] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def increase_parser_credit_available(db:AsyncSession, domain_data:updateParserCreditAvailableDomain):
        try:
            query = text("""
                UPDATE company_info 
                SET parser_credit_available = parser_credit_available + :increase_parser_credit
                WHERE company_key = :company_key
            """)
            params = {
                "company_key": domain_data.company_key,
                "increase_parser_credit": domain_data.parser_credit_available
            }
            await db.execute(query, params)
            await db.commit()

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.company_info.CompanyInfoQuery.increase_parser_credit_available] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def decrease_parser_credit_available(db:AsyncSession, company_key, use_parser_credit):
        try:
            query = text("""
                UPDATE company_info 
                SET parser_credit_available = parser_credit_available - :use_parser_credit
                WHERE company_key = :company_key
                    AND parser_credit_available >= :use_parser_credit
            """)
            params = {
                "company_key": company_key,
                "use_parser_credit": use_parser_credit
            }
            await db.execute(query, params)
            await db.commit()

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.company_info.CompanyInfoQuery.decrease_parser_credit_available] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_store_name(db:AsyncSession, domain_data: registerDomain | EnrollFileSearchStoreDomain):
        try:
            query = text("""
                UPDATE company_info
                SET store_name = :store_name
                WHERE company_key = :company_key
            """)
            params = {
                "store_name": domain_data.store_name,
                "company_key": domain_data.company_key
            }
            await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.company_info.CompanyInfoQuery.update_store_name] DBError: {e}")
            raise DBError(e)
