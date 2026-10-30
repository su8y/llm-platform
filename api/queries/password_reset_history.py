import logging

import logging
from datetime import timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from domain.user import *
from utils.error import DBError
from utils.constants import *



class PasswordResetHistoryQuery:
	"""
	id: int,
	user_id: str,
	find_key: str,
	find_key_exp_date: datetime,
	reg_date: datetime,
	is_newest: bool,
	is_success: bool
	"""

	@staticmethod
	async def insert_row(db:AsyncSession, domain_data:findPasswordDomain):
		try:
			query = text(
				"""
					INSERT INTO
						password_reset_history (user_id, find_key, find_key_exp_date, reg_date)
					VALUES
						(:user_id, :find_key, :find_key_exp_date, :reg_date)
				"""
			)
			params = {
				"user_id": domain_data.user_id,
				"find_key": domain_data.find_key,
				"find_key_exp_date": domain_data.current_date + timedelta(days=1),
				"reg_date": domain_data.current_date
			}

			await db.execute(query, params)
			await db.commit()
			
			return True
			
		except Exception as e:
			await db.rollback()
			logging.error(f"[queries.password_reset_history.PasswordResetHistoryQuery.insert_row] DBError: {e}")
			raise DBError(f"PasswordResetHistoryQuery.insert_password_reset_history_row error: {e}")
	

	@staticmethod
	async def get_find_key_by_user_id(db:AsyncSession, domain_data:checkValidationFindPasswordDomain):
		try:
			query = text(
				"""
					SELECT
						id, user_id, find_key, find_key_exp_date
					FROM password_reset_history
					WHERE user_id = :user_id
						AND is_newest = 1
				"""
			)
			params = {
				"user_id": domain_data.user_id
			}

			result = await db.execute(query, params)
			row = result.fetchone()

			if not row:
				return None
			else:
				return {
					"id": row.id,
					"user_id": row.user_id,
					"find_key": row.find_key,
					"find_key_exp_date": row.find_key_exp_date
				}

		except Exception as e:
			logging.error(f"[queries.password_reset_history.PasswordResetHistoryQuery.get_find_key_by_user_id] DBError: {e}")
			raise DBError(f"PasswordResetHistoryQuery.get_find_key_by_user_id error: {e}")
	
	
	@staticmethod
	async def update_is_newest_false(db:AsyncSession, domain_data:findPasswordDomain):
		try:
			query = text(
				"""
					UPDATE
						password_reset_history
					SET
						is_newest = 0
					WHERE
						user_id = :user_id
				"""
			)
			params = {
				"user_id": domain_data.user_id
			}

			await db.execute(query, params)
			await db.commit()
			
			return True
		
		except Exception as e:
			await db.rollback()
			logging.error(f"[queries.password_reset_history.PasswordResetHistoryQuery.update_is_newest] DBError: {e}")
			raise DBError(f"PasswordResetHistoryQuery.update_is_newest error: {e}")
	

	@staticmethod
	async def update_expire_date_by_id(db:AsyncSession, domain_data:changePasswordDomain):
		try:
			query = text(
				"""
					UPDATE password_reset_history
					SET
						find_key_exp_date = :find_key_exp_date
					WHERE find_key = :find_key
						AND is_newest = 1
				"""
			)
			params = {
				"find_key": domain_data.find_key,
				"find_key_exp_date": domain_data.current_date
			}

			await db.execute(query, params)
			await db.commit()
			
			return True
		
		except Exception as e:
			await db.rollback()
			logging.error(f"[queries.password_reset_history.PasswordResetHistoryQuery.update_is_newest] DBError: {e}")
			raise DBError(f"PasswordResetHistoryQuery.update_is_newest error: {e}")