import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from domain.admin import *
from utils.error import DBError

class UserAuthQuery:
    
    @staticmethod
    async def insert_metadata(db:AsyncSession, **kwargs):
        try:
            query = text("""
                INSERT INTO user_auth (id, common, auth_name, auth_account_manage, auth_plan_manage, auth_reference_view, auth_reference_write, auth_reference_category_manage, auth_playground_use, auth_reference_language_all, auth_prompt_manage)
                VALUES (:id, :common, :auth_name, :auth_account_manage, :auth_plan_manage, :auth_reference_view, :auth_reference_write, :auth_reference_category_manage, :auth_playground_use, :auth_reference_language_all, :auth_prompt_manage)
            """)
            await db.execute(query, kwargs)
            await db.commit()
        except Exception as e:
            logging.error(f"[queries.user_auth.UserAuth.insert_metadata] DBError: {e}")
            raise DBError(e)

            
    @staticmethod
    async def get_auth(db:AsyncSession, id:int):
        try:
            query = text("""
                SELECT * FROM user_auth WHERE id = :id
            """)
            params = {
                "id": id
            }
            result = await db.execute(query, params)
            
            if not result:
                return None
            else:
                row = result.fetchone()
                return row
        except Exception as e:
            logging.error(f"[queries.user_auth.UserAuth.get_auth] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_auth_name(db:AsyncSession, domain_data:getAuthNameDomain):
        try:
            query = text("""
                SELECT auth_name FROM user_auth WHERE id != 1 AND (common = TRUE OR company_key = :company_key)
            """)
            params = {
                "company_key": domain_data.company_key
            }
            result = await db.execute(query, params)
            if not result:
                return None
            else:
                rows = result.fetchall()
                return [row.auth_name for row in rows]
        except Exception as e:
            logging.error(f"[queries.user_auth.UserAuth.get_auth_name] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_user_auth_by_auth_name(db:AsyncSession, domain_data:changeAuthDomain):
        try:
            query = text("""
                SELECT id FROM user_auth WHERE auth_name = :auth_name AND (common = TRUE OR company_key = :company_key)
            """)
            params = {
                "auth_name": domain_data.auth_name,
                "company_key": domain_data.company_key
            }
            result = await db.execute(query, params)
            return result.fetchone().id if result else None
        except Exception as e:
            logging.error(f"[queries.user_auth.UserAuth.get_user_auth_by_auth_name] DBError: {e}")
            raise DBError(e)


