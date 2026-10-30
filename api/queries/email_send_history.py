import ast
import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from domain.email import *
from domain.emailrag import *
from utils.date import cal_offset_hours, datetime_to_string
from utils.error import DBError
from utils.constants import *




class EmailSendHistoryQuery:
	@staticmethod
	async def insert_outbox(db:AsyncSession, domain_data:SendEmailDomain):
		try:
			query_text ="""
				INSERT INTO email_send_history (
					company_key, subject,
					from_mail, from_name, to_mail, to_name, cc_mail, cc_name, bcc_mail, bcc_name,
					received_at, sent_at, keyword, comment, manager,
					attachments, company, in_reply_to, `references`, cid_images, last_content_for_llm
				) VALUES (
					:company_key, :subject,
					:from_mail, :from_name, :to_mail, :to_name, :cc_mail, :cc_name, :bcc_mail, :bcc_name,
					:received_at, :sent_at, :keyword, :comment, :manager,
					:attachments, :company, :in_reply_to, :references, :cid_images, :last_content_for_llm
				) RETURNING id
			"""
			params = {
				"company_key": domain_data.company_key,
				# "message_id": domain_data.to_message_id,
				"subject": domain_data.reply_subject,
				"from_mail": str(domain_data.reply_from) if isinstance(domain_data.reply_from, (str, list)) else None,
				"from_name": str(domain_data.reply_from_name) if isinstance(domain_data.reply_from_name, (str, list)) else None,
				"to_mail": str(domain_data.reply_to) if isinstance(domain_data.reply_to, (str, list)) else None,
				"to_name": str(domain_data.reply_to_name) if isinstance(domain_data.reply_to_name, (str, list)) else None,
				"cc_mail": str(domain_data.reply_cc) if isinstance(domain_data.reply_cc, (str, list)) else None,
				"cc_name": str(domain_data.reply_cc_name) if isinstance(domain_data.reply_cc_name, (str, list)) else None,
				"bcc_mail": str(domain_data.reply_bcc) if isinstance(domain_data.reply_bcc, (str, list)) else None,
				"bcc_name": str(domain_data.reply_bcc_name) if isinstance(domain_data.reply_bcc_name, (str, list)) else None,
				"received_at": domain_data.received_at,
				"sent_at": domain_data.current_time,
				"keyword": domain_data.keyword,
				"comment": domain_data.comments,
				"manager": domain_data.manager_id,
				# "html_s3_key": f"{domain_data.s3_bucket}:{domain_data.s3_key}",
				"attachments": domain_data.attachments,
				"company": domain_data.company,
				"in_reply_to": domain_data.from_message_id,
				"references": str(domain_data.references + [domain_data.from_message_id]) if domain_data.references else str([domain_data.from_message_id]),
				"cid_images": domain_data.cid_images,
				"last_content_for_llm": domain_data.llm_content
			}
			query = text(query_text)
			result = await db.execute(query, params)
			row = result.fetchone()
			await db.commit()
			return row[0]

		except Exception as e:
			await db.rollback()
			logging.error(f"[queries.email_send_history.EmailSendHistoryQuery.insert_outbox] DBError: {e}")
			raise DBError(e)


	@staticmethod
	async def outbox_list(db:AsyncSession, domain_data:EmailRAGListDomain):
		try:
			where_conditions = ["company_key = :company_key"]
			params = {
				"company_key": domain_data.company_key,
				"limit": domain_data.per_page,
				"offset": (domain_data.page - 1) * domain_data.per_page
			}
			if domain_data.subject:
				where_conditions.append("subject LIKE :subject")
				params["subject"] = f"%{domain_data.subject}%"
			if domain_data.manager:
				where_conditions.append("manager = :manager")
				params["manager"] = domain_data.manager
			if domain_data.to:
				where_conditions.append("(to_mail LIKE :to or to_name LIKE :to)")
				params["to"] = f"%{domain_data.to}%"
			if domain_data.start_date:
				where_conditions.append("sent_at >= :start_date")
				params["start_date"] = domain_data.start_date
			if domain_data.end_date:
				where_conditions.append("sent_at <= :end_date")
				params["end_date"] = domain_data.end_date

			count_base_query = """
				SELECT COUNT(*) as total
				FROM email_send_history
				WHERE 
			"""
			base_query = """
				SELECT
					id, subject, company, manager, sent_at, from_mail, from_name, to_mail, to_name, received_at
				FROM email_send_history
				WHERE 
			"""
			where_query = " AND ".join(where_conditions) if where_conditions else "1=1"
			order_query = " ORDER BY sent_at DESC"
			page_query = " LIMIT :limit OFFSET :offset"
			count_query_text = count_base_query + where_query
			query_text = base_query + where_query + order_query + page_query

			count_query = text(count_query_text)
			count_result = await db.execute(count_query, params)
			total_count = count_result.scalar()
			query = text(query_text)
			result = await db.execute(query, params)
			rows = result.fetchall()
			return ([
				{
					"id": row.id,
					"subject": row.subject,
					"company": row.company,
					"manager": row.manager,
					"sentAt": row.sent_at,
					"receivedAt": row.received_at,
					"fromMail": row.from_mail,
					"fromName": row.from_name,
					"toMail": ast.literal_eval(row.to_mail) if isinstance(row.to_mail, str) and row.to_mail[0] == "[" and row.to_mail[-1] == "]" else [],
					"toName": ast.literal_eval(row.to_name) if isinstance(row.to_mail, str) and row.to_name[0] == "[" and row.to_name[-1] == "]" else [],
				} for row in rows
			], total_count)

		except Exception as e:
			logging.error(f"[queries.email_send_history.EmailSendHistoryQuery.outbox_list] Exception: {e}")
			raise DBError


	@staticmethod
	async def get_outbox_detail(db:AsyncSession, domain_data:EmailRAGDetailDomain) -> dict:
		try:
			# 추후 추가해야할 칼럼: templates, kind
			query = text(
				"""
					SELECT
						message_id, subject,
						from_mail, from_name, to_mail, to_name, cc_mail, cc_name, bcc_mail, bcc_name,
						sent_at, received_at, keyword, comment, manager,
						html_s3_key, attachments, company, cid_images
					FROM email_send_history
					WHERE id = :id
						AND company_key = :company_key
				"""
			)
			params = {
				"id": domain_data.row_id,
				"company_key": domain_data.company_key
			}
			result = await db.execute(query, params)
			row = result.fetchone()
			return {
				"messageId": row.message_id,
				"subject": row.subject,
				"toName": row.to_name,
				"toMail": row.to_mail,
				"fromName": row.from_name,
				"fromMail": row.from_mail,
				"ccName": row.cc_name,
				"ccMail": row.cc_mail,
				"bccName": row.bcc_name,
				"bccMail": row.bcc_mail,
				"sentAt": row.sent_at,
				"receivedAt": row.received_at,
				"keyword": row.keyword,
				"comment": row.comment,
				"manager": row.manager,
				"thread": row.html_s3_key,
				"attachments": row.attachments,
				"company": row.company,
				"cid_images": row.cid_images
			} if row else {}

		except Exception as e:
			logging.error(f"[queries.email_send_history.EmailSendHistoryQuery.get_title] DBError: {e}")
			raise DBError(e)


	@staticmethod
	async def get_out_count_per_days(db:AsyncSession, domain_data:GetDashboardLineDomain):
		try:
			offset_hours = cal_offset_hours(domain_data.client_timezone, "mysql")

			params = {"offset_hours": offset_hours}
			where_conditions = []

			# 동적 필터
			if domain_data.company_key:
				where_conditions.append("company_key = :company_key")
				params["company_key"] = domain_data.company_key

			# 날짜 필터
			if domain_data.start_date and domain_data.end_date:
				where_conditions.append("sent_at >= :start_date AND sent_at <= :end_date")
				params["start_date"] = domain_data.start_date
				params["end_date"] = domain_data.end_date
			elif domain_data.start_date:
				where_conditions.append("sent_at >= :start_date")
				params["start_date"] = domain_data.start_date
			elif domain_data.end_date:
				where_conditions.append("sent_at <= :end_date")
				params["end_date"] = domain_data.end_date

			where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

			query = text(f"""
				SELECT
					DATE(DATE_ADD(sent_at, INTERVAL :offset_hours HOUR)) as days,
					COUNT(*) as count
				FROM email_send_history
				WHERE {where_clause}
				GROUP BY days
				ORDER BY days
			""")
			result = await db.execute(query, params)
			rows = result.fetchall()

			if not rows:
				domain_data.email_send_history_row = []
			else:
				domain_data.email_send_history_row = {
					datetime_to_string(row.days): row.count
				for row in rows}
		except Exception as e:
			logging.error(f"[queries.email_send_history.EmailSendHistoryQuery.get_out_count_per_days] Exception: {e}")
			raise DBError


	@staticmethod
	async def update_row_after_send_mail(db:AsyncSession, domain_data:SendEmailDomain):
		try:
			query = text("""
				UPDATE email_send_history
				SET
					is_error = :is_error,
					message_id = :message_id,
					html_s3_key = :html_s3_key
				WHERE id = :row_id
			""")
			params = {
				"is_error": False,
				"message_id": domain_data.to_message_id,
				"html_s3_key": f"{domain_data.s3_bucket}:{domain_data.s3_key}",
				"row_id": domain_data.row_id
			}
			await db.execute(query, params)
			await db.commit()
		except Exception as e:
			logging.error(f"[queries.email_send_history.EmailSendHistoryQuery.update_bounce_message] Exception: {e}")
			raise DBError(e)


	@staticmethod
	async def update_bounce_message(db:AsyncSession, domain_data:GetSESBounceDomain):
		try:
			query = text("""
				UPDATE email_send_history
				SET
					is_bounce = :is_bounce,
					bounce_type = :bounce_type,
					bounce_sub_type = :bounce_sub_type,
					bounced_recipients =:bounced_recipients
				WHERE message_id = :message_id
			""")
			params = {
				"is_bounce": domain_data.is_bounce,
				"bounce_type": domain_data.bounce_type,
				"bounce_sub_type": domain_data.bounce_sub_type,
				"bounced_recipients": domain_data.bounced_recipients,
				"message_id": domain_data.message_id
			}
			await db.execute(query, params)
			await db.commit()
		except Exception as e:
			logging.error(f"[queries.email_send_history.EmailSendHistoryQuery.update_bounce_message] Exception: {e}")
			raise DBError(e)


	@staticmethod
	async def update_soft_deletion(db:AsyncSession, domain_data:DeleteSentEmailDomain):
		try:
			if isinstance(domain_data.email_send_history_id, int):
				query = text(
					"""
						UPDATE email_send_history
						SET
							is_on = :is_on,
							is_show = :is_show
						WHERE company_key = :company_key
								AND id = :email_send_history_id
					"""
				)
			else:
				query = text(
					"""
						UPDATE email_send_history
						SET
							is_on = :is_on,
							is_show = :is_show
						WHERE company_key = :company_key
								AND id IN :email_send_history_id
					"""
				)
			params = {
				"is_on": False,
				"is_show": False,
				"company_key": domain_data.company_key,
				"email_send_history_id": domain_data.email_send_history_id
			}
			await db.execute(query, params)
			await db.commit()

		except Exception as e:
			logging.error(f"[queries.email_send_history.EmailSendHistoryQuery.update_soft_deletion] Exception: {e}")
			raise DBError(e)


	@staticmethod
	async def delete_by_id(db:AsyncSession, domain_data: DeleteSentEmailDomain):
		try:
			if isinstance(domain_data.email_send_history_id, int):
				query = text(
					"""
						DELETE FROM email_send_history
						WHERE company_key = :company_key
								AND id = :email_send_history_id
					"""
				)
			else:
				query = text(
					"""
						DELETE FROM email_send_history
						WHERE company_key = :company_key
								AND id IN :email_send_history_id
					"""
				)
			params = {"company_key": domain_data.company_key, "email_send_history_id": domain_data.email_send_history_id}
			await db.execute(query, params)
			await db.commit()

		except Exception as e:
			logging.error(f"[queries.email_send_history.EmailSendHistoryQuery.delete_by_id] Exception: {e}")
			raise DBError(e)