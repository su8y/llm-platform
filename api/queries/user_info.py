import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from domain.admin import *
from domain.monitoring import *
from domain.user import *
from domain.email import GetManagerListDomain
from utils.date import adapt_timezone_datetime_to_datetime
from utils.error import DBError


class UserInfoQuery:

    @staticmethod
    async def register(
        db:AsyncSession,
        domain_data: registerDomain
    ):
        try:
            query = text("""
                INSERT INTO user_info (
                    company_key, user_id, user_password, email_address, department, 
                    reg_date, user_auth, lang, phone, invite_history_id, certifi, is_admin
                ) VALUES (
                    :company_key, :user_id, :user_password, :email_address, :department, 
                    :reg_date, :user_auth, :lang, :phone, :invite_history_id, :certifi, :is_admin
                )
            """)

            params = {
                "company_key": domain_data.company_key,
                "user_id": domain_data.user_id,
                "user_password": domain_data.hashed_password,
                "email_address": domain_data.email_address,
                "department": domain_data.department,
                "reg_date": domain_data.reg_date,
                "user_auth": domain_data.user_auth,
                "lang": domain_data.lang,
                "phone": domain_data.phone,
                "invite_history_id": domain_data.invite_history_id,
                "certifi": domain_data.certifi,
                "is_admin": domain_data.is_admin
            }

            await db.execute(query, params)
            await db.commit()

            # 회사 정보 조회하여 응답에 포함
            company_query = text("""
                SELECT company_name, plan_info_id, credit_available, vector_db_index, vector_db_namespace, master_id 
                FROM company_info 
                WHERE company_key = :company_key
            """)
            company_result = await db.execute(company_query, {"company_key": domain_data.company_key})
            company_row = company_result.fetchone()

            # 삽입된 사용자 정보 조회
            user_query = text("""
                SELECT * FROM user_info 
                WHERE company_key = :company_key AND user_id = :user_id
            """)
            user_result = await db.execute(user_query, {"company_key": domain_data.company_key, "user_id": domain_data.user_id})
            user_row = user_result.fetchone()

            return {
                "user_id": user_row.user_id,
                "user_password": user_row.user_password,
                "user_auth": user_row.user_auth,
                "email_address": user_row.email_address,
                "reg_date": user_row.reg_date,
                "last_login_date": None,
                "find_key": None,
                "find_key_exp_date": None,
                "department": user_row.department,
                "invite_history_id": user_row.invite_history_id,
                "certifi": user_row.certifi,
                "phone": user_row.phone,
                "lang": user_row.lang,
                "company_key": user_row.company_key,
                "company_name": company_row[0] if company_row else None,
                "plan_info_id": company_row[1] if company_row else None,
                "credit_available": company_row[2] if company_row else None,
                "vector_db_index": company_row[3] if company_row else None,
                "vector_db_namespace": company_row[4] if company_row else None,
                "master_id": company_row[5] if company_row else None
            } if user_row and company_row else None
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.user_info.UserInfoQuery.register] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_user(db:AsyncSession, domain_data:loginDomain | certificateDomain): # for login
        """
        :param filters: user_id or email_address
        :return: dict
        """
        try:
            base_query = """
                SELECT ui.*, ci.company_name, ci.plan_info_id, ci.credit_available, ci.vector_db_index, ci.vector_db_namespace, ci.master_id
                FROM user_info ui
                JOIN company_info ci ON ui.company_key = ci.company_key
                WHERE 
            """

            params = {}

            if domain_data.user_id:
                query = base_query + "ui.user_id = :user_id LIMIT 1"
                params['user_id'] = domain_data.user_id

            result = await db.execute(text(query), params)
            row = result.fetchone()

            if not row:
                return None

            return {
                "user_id": row.user_id,
                "user_password": row.user_password,
                "user_auth": row.user_auth,
                "email_address": row.email_address,
                "reg_date": adapt_timezone_datetime_to_datetime(row.reg_date, "UTC"),
                "last_login_date": adapt_timezone_datetime_to_datetime(row.last_login_date, "UTC") if row.last_login_date else None,
                "find_key": row.find_key,
                "find_key_exp_date": adapt_timezone_datetime_to_datetime(row.find_key_exp_date, "UTC") if row.find_key_exp_date else None,
                "department": row.department,
                "invite_history_id": row.invite_history_id,
                "certifi": row.certifi,
                "phone": row.phone,
                "lang": row.lang,
                "company_key": row.company_key,
                "company_name": row.company_name,
                "plan_info_id": row.plan_info_id,
                "credit_available": row.credit_available,
                "vector_db_index": row.vector_db_index,
                "vector_db_namespace": row.vector_db_namespace,
                "master_id": row.master_id
            }
        except Exception as e:
            logging.error(f"[queries.user_info.UserInfoQuery.get_user] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_user_info_by_user_id(db:AsyncSession, domain_data:loginDomain | registerDomain):
        """
        :param filters: user_id or email_address
        :return: dict
        """
        try:
            query = """
                SELECT user_id
                FROM user_info
                WHERE user_id = :user_id
            """

            result = await db.execute(text(query), {"user_id": domain_data.user_id})
            row = result.fetchone()

            if not row:
                return None
            else:
                return {"user_id": row.user_id}
        except Exception as e:
            logging.error(f"[queries.user_info.UserInfoQuery.get_user] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_user_info_for_find_password(db:AsyncSession, domain_data:findPasswordDomain):
        try:
            query = text("""
                SELECT ui.user_id, ci.company_name, ui.email_address
                FROM user_info ui
                JOIN company_info ci ON ui.company_key = ci.company_key
                WHERE ui.user_id = :user_id
            """)
            params = {"user_id": domain_data.user_id}
            result = await db.execute(query, params)
            row = result.fetchone()
            return {"user_id": row.user_id, "company_name": row.company_name, "email_address": row.email_address} if row else None

        except Exception as e:
            logging.error(f"[queries.user_info.UserInfoQuery.get_user_info_for_find_password] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_find_password_data_by_user_id(db:AsyncSession, domain_data:checkValidationFindPasswordDomain):
        try:
            query = text(
                """
                SELECT user_id, find_key, find_key_exp_date
                FROM user_info
                WHERE user_id = :user_id
                """
            )
            params = {"user_id": domain_data.user_id}
            result = await db.execute(query, params)
            row = result.fetchone()

            if not row:
                return None
            else:
                return {
                    "user_id": row.user_id,
                    "find_key": row.find_key,
                    "find_key_exp_date": row.find_key_exp_date}
        except Exception as e:
            logging.error(f"[queries.user_info.UserInfoQuery.get_user] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_user_email_by_email(db:AsyncSession, domain_data:registerDomain):
        try:
            query = text("""
                SELECT email_address FROM user_info WHERE email_address = :email_address LIMIT 1
            """)
            result = await db.execute(query, {"email_address": domain_data.email_address})
            row = result.fetchone()
            if not row:
                return None
            return {"email_address": row.email_address}
        except Exception as e:
            logging.error(f"[queries.user_info.UserInfoQuery.get_user_by_email] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_user_info(db:AsyncSession, domain_data:getInfoDomain):
        try:
            query = text("""
                 SELECT
                     ui.user_id,
                     ui.email_address,
                     ui.department,
                     ci.company_name,
                     ci.credit_available,
                     ua.auth_name,
                     ua.auth_account_manage,
                     ua.auth_plan_manage,
                     ua.auth_reference_view,
                     ua.auth_reference_write,
                     ua.auth_reference_category_manage,
                     ua.auth_prompt_manage,
                     ua.auth_playground_use,
                     ua.auth_reference_language_all,
                     ui.lang,
                     ci.plan_info_id,
                     COALESCE(fch.remain_credit, 0) AS parser_credit_available,
                     ci.email_available
                 FROM user_info ui
                 JOIN user_auth ua
                 ON ui.user_auth = ua.id
                 JOIN company_info ci
                 ON ui.company_key = ci.company_key
                 LEFT JOIN (
                     SELECT f1.company_key, f1.remain_credit
                     FROM file_credit_history f1
                     WHERE f1.reg_date = (
                         SELECT MAX(f2.reg_date)
                         FROM file_credit_history f2
                         WHERE f1.company_key = f2.company_key
                     )
                 ) fch
                 ON ui.company_key = fch.company_key
                 WHERE ui.user_id = :user_id
            """)

            result = await db.execute(query, {"user_id": domain_data.user_id})
            row = result.fetchone()

            if not row:
                return None

            return {
                "userId": row[0],
                "emailAddress": row[1],
                "department": row[2],
                "companyName": row[3],
                "creditAvailable": row[4],
                "lang": row[14],
                "isExpiredPlan": True if row[15] == 8 else False,  # EXPIRED_PLAN_INFO_ID = 8
                "parserCreditAvailable": row[16],
                "emailAvailable": row[17],
                "userAuth": {
                    "authName": row[5],
                    "authAccountManage": row[6],
                    "authPlanManage": row[7],
                    "authReferenceView": row[8],
                    "authReferenceWrite": row[9],
                    "authReferenceCategoryManage": row[10],
                    "authPromptManage": row[11],
                    "authPlaygroundUse": row[12],
                    "authReferenceLanguageAll": row[13]
                }
            }
        except Exception as e:
            logging.error(f"[queries.user_info.UserInfoQuery.get_user_info] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_user_info_from_token_raw(db:AsyncSession, user_id:str):
        try:
            query = text("""
                SELECT
                    user_info.user_id AS user_id,
                    user_info.user_auth AS user_auth,
                    user_info.company_key AS company_key,
                    user_info.certifi AS certifi,
                    user_info.lang AS lang,
                    user_info.is_admin AS is_admin,
                    company_info.company_name AS company_name,
                    company_info.credit_available AS credit_available,
                    company_info.status AS company_status,
                    company_info.plan_info_id AS plan_info_id,
                    company_info.vector_db_index AS vector_db_index,
                    company_info.vector_db_namespace AS vector_db_namespace,
                    company_info.store_name as store_name,
                    company_info.on_llm_platform_system AS on_llm_platform_system,
                    COALESCE(fch.remain_credit, 0) AS parser_credit_available
                FROM user_info
                LEFT JOIN (
                    SELECT f1.company_key, f1.remain_credit
                    FROM file_credit_history f1
                    WHERE f1.reg_date = (
                        SELECT MAX(f2.reg_date)
                        FROM file_credit_history f2
                        WHERE f1.company_key = f2.company_key
                    )
                ) fch
                ON user_info.company_key = fch.company_key
                INNER JOIN company_info
                ON company_info.company_key = user_info.company_key
                INNER JOIN user_auth
                ON user_auth.id = user_info.user_auth 
                WHERE user_info.user_id = :user_id
                LIMIT 1
            """)

            result = await db.execute(query, {"user_id": user_id})
            row = result.fetchone()

            if not row:
                return None

            return {
                "user_id": row.user_id,
                "user_auth": row.user_auth,
                "company_key": row.company_key,
                "company_name": row.company_name,
                "credit_available": row.credit_available,
                "status": row.company_status,
                "plan_info_id": row.plan_info_id,
                "vector_db_index": row.vector_db_index,
                "vector_db_namespace": row.vector_db_namespace,
                "certifi": row.certifi,
                "lang": row.lang,
                "parser_credit_available": row.parser_credit_available,
                "is_admin": row.is_admin,
                "store_name": row.store_name,
                "on_llm_platform_system": row.on_llm_platform_system
            }
        except Exception as e:
            logging.error(f"[queries.user_info.UserInfoQuery.get_user_info_from_token_raw] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_user_info_from_token(db:AsyncSession, user_id:str):
        try:
            query = text("""
                SELECT
                    ui.user_id,
                    ui.user_auth,
                    ui.company_key,
                    ci.credit_available,
                    ci.status,
                    ci.vector_db_index,
                    ci.vector_db_namespace,
                    ui.certifi,
                    ui.lang
                FROM user_info ui
                JOIN company_info ci ON ui.company_key = ci.company_key
                WHERE ui.user_id = :user_id
            """)

            result = await db.execute(query, {"user_id": user_id})
            row = result.fetchone()

            if not row:
                return None

            return {
                "user_id": row[0],
                "user_auth": row[1],
                "company_key": row[2],
                "credit_available": row[3],
                "status": row[4],
                "vector_db_index": row[5],
                "vector_db_namespace": row[6],
                "certifi": row[7],
                "lang": row[8]
            }
        except Exception as e:
            logging.error(f"[queries.user_info.UserInfoQuery.get_user_info_from_token] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_user_list(db:AsyncSession, domain_data:GetManagerListDomain):
        try:
            query_text = "SELECT * FROM user_info WHERE company_key = :company_key"
            params = {"company_key": domain_data.company_key}
            query = text(query_text)
            result = await db.execute(query, params)
            rows = result.fetchall()
            if rows:
                user_id_list = list()
                email_address_list = list()
                for row in rows:
                    user_id_list.append(row.user_id)
                    email_address_list.append(row.email_address)
                return {
                    "userId": user_id_list,
                    "emailAddress": email_address_list
                }
            else:
                return None
        except Exception as e:
            logging.error(f"[queries.user_info.UserInfoQuery.get_user_list] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_user_ids(db:AsyncSession, domain_data:getChatHistoryDetailHeadDomain):
        try:
            query_text = "SELECT user_id FROM user_info"
            params = {}

            if domain_data.company_key:
                query_text += " WHERE company_key = :company_key"
                params['company_key'] = domain_data.company_key

            query = text(query_text)
            result = await db.execute(query, params)
            rows = result.fetchall()

            return [row[0] for row in rows] if rows else None
        except Exception as e:
            logging.error(f"[queries.user_info.UserInfoQuery.get_user_ids] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_user_by_find_key(db:AsyncSession, find_key:str):
        try:
            query = text("""
                SELECT * 
                FROM user_info 
                WHERE find_key = :find_key
            """)

            result = await db.execute(query, {"find_key": find_key})
            return result.fetchone()
        except Exception as e:
            logging.error(f"[queries.user_info.UserInfoQuery.get_user_by_find_key] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def certificate(db:AsyncSession, user_id:str):
        try:
            query = text("""
                UPDATE user_info
                SET certifi = TRUE
                WHERE user_id = :user_id
            """)

            await db.execute(query, {"user_id": user_id})
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.user_info.UserInfoQuery.certificate] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_login_date(db:AsyncSession, user_id:str, time:datetime):
        try:
            query = text("""
                UPDATE user_info
                SET last_login_date = :time
                WHERE user_id = :user_id
            """)

            await db.execute(query, {"user_id": user_id, "time": time})
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.user_info.UserInfoQuery.update_login_date] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_find_key(db:AsyncSession, user_id:str, find_key:str, find_key_exp_date:datetime):
        try:
            query = text("""
                UPDATE user_info
                SET find_key = :find_key, find_key_exp_date = :find_key_exp_date
                WHERE user_id = :user_id
            """)

            await db.execute(query, {
                "user_id": user_id,
                "find_key": find_key,
                "find_key_exp_date": find_key_exp_date
            })
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.user_info.UserInfoQuery.update_find_key] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_newest_session_key(db:AsyncSession, user_id:str, session_key:str):
        try:
            query = text("""
                UPDATE user_info
                SET newest_session_key = :session_key
                WHERE user_id = :user_id
            """)

            await db.execute(query, {"user_id": user_id, "session_key": session_key})
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.user_info.UserInfoQuery.update_newest_session_key] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_password(db:AsyncSession, domain_data:changePasswordDomain):
        try:
            query = text("""
                UPDATE user_info
                SET user_password = :user_password
                WHERE user_id = :user_id
            """)
            params = {
                "user_password": domain_data.hashed_password,
                "user_id": domain_data.user_id
            }

            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.user_info.UserInfoQuery.update_password] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_auth(db:AsyncSession, domain_data:changeAuthDomain):
        try:
            # 동적으로 SET 구문 생성
            set_clauses = []
            params = {"user_id": domain_data.user_id}

            if domain_data.user_auth:
                set_clauses.append("user_auth = :user_auth")
                params["user_auth"] = domain_data.user_auth

            set_clause = ", ".join(set_clauses)

            if not set_clauses:
                return False

            query = text(f"""
                UPDATE user_info
                SET {set_clause}
                WHERE user_id = :user_id
            """)

            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.user_info.UserInfoQuery.update_auth] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_lang(db:AsyncSession, domain_data:changeLangDomain):
        try:
            query = text("""
                UPDATE user_info
                SET lang = :lang
                WHERE user_id = :user_id
            """)

            await db.execute(query, {"user_id": domain_data.user_id, "lang": domain_data.lang})
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.user_info.UserInfoQuery.update_lang] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def update_find_key_and_expire_date_by_find_key(db:AsyncSession, domain_data:checkValidationFindPasswordDomain):
        try:
            query = text(
                """
                UPDATE user_info
                SET find_key_exp_date = :find_key_exp_date
                WHERE user_id = :user_id
                    AND find_key = :find_key
                """
            )
            params = {
                "find_key_exp_date": domain_data.current_date,
                "user_id": domain_data.user_id,
                "find_key": domain_data.find_key
            }
            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.user_info.UserInfoQuery.update_find_key_and_expire_date_by_find_key] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def delete(db:AsyncSession, domain_data:deleteUserDomain):
        try:
            # 먼저 invite_history_id 가져오기
            select_query = text("""
                SELECT invite_history_id
                FROM user_info
                WHERE company_key = :company_key AND user_id = :user_id
            """)

            result = await db.execute(select_query, {"company_key": domain_data.company_key, "user_id": domain_data.user_id})
            row = result.fetchone()

            if not row:
                return False

            invite_history_id = row[0]

            # 사용자 삭제
            delete_query = text("""
                DELETE FROM user_info
                WHERE company_key = :company_key AND user_id = :user_id
            """)

            await db.execute(delete_query, {"company_key": domain_data.company_key, "user_id": domain_data.user_id})
            await db.commit()

            return invite_history_id
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.user_info.UserInfoQuery.delete] DBError: {e}")
            raise DBError(e)
