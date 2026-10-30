import ast
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from domain.email import *
from utils.date import cal_offset_hours, datetime_to_string
from utils.error import DBError
from utils.constants import *




class CXEmailQuery:
    @staticmethod
    async def get_inbox_list(db:AsyncSession, domain_data:InboxListDomain) -> tuple[list, int]:
        try:
            where_conditions = [
                "company_key = :company_key"
            ]
            params = {
                "status": ["received"],
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
            if domain_data.status:
                where_conditions.append("status = :status")
                params["status"] = domain_data.status
            if domain_data.from_:
                where_conditions.append("(from_mail LIKE :from or from_name LIKE :from)")
                params["from"] = f"%{domain_data.from_}%"
            if domain_data.start_date:
                where_conditions.append("received_at >= :start_date")
                params["start_date"] = domain_data.start_date
            if domain_data.end_date:
                where_conditions.append("received_at <= :end_date")
                params["end_date"] = domain_data.end_date

            # WHERE 절 구성
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # 카운트 쿼리 실행
            count_query = text(f"SELECT COUNT(*) FROM cx_email WHERE {where_clause}")
            count_result = await db.execute(count_query, params)
            count = count_result.scalar()


            query_text ="""
                SELECT id, subject, status, received_at, from_name, from_mail, manager
                FROM cx_email
            """
            if where_conditions:
                query_text += " WHERE " + where_clause
            query_text += " ORDER BY received_at DESC LIMIT :limit OFFSET :offset"

            query = text(query_text)

            result = await db.execute(query, params)
            rows = result.fetchall()

            return ([
                {
                    "id": row.id,
                    "subject": row.subject,
                    "status": row.status,
                    "received_at": row.received_at,
                    "from_name": row.from_name,
                    "from_mail": row.from_mail,
                    "manager": row.manager,
                    # "company": row.company,
                } for row in rows
            ] if rows else [], count)
            # (rows:list, count:int)

        except Exception as e:
            logging.error(f"[queries.post.PostQuery.get_title] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_inbox_detail(db:AsyncSession, domain_data:GetInboxDomain | InitAnswerDomain | ChangeStatusDomain) -> dict:
        try:
            # 추후 추가해야할 칼럼: templates, kind
            query = text(
                """
                    SELECT
                        id, message_id, subject, to_name, to_mail, to_name_list, to_mail_list, from_name, from_mail, cc_name, cc_mail,
                        received_at, `references`, status, content, company, keyword, last_content, comment, manager,
                        answering_content, html_s3_key, attachments, cid_images, has_temp
                    FROM cx_email
                    WHERE id = :id
                        AND company_key = :company_key
                """
            )
            params = {
                "id": domain_data.id,
                "company_key": domain_data.company_key
            }
            result = await db.execute(query, params)
            row = result.fetchone()
            return {
                "id": row.id,
                "message_id": row.message_id,
                "subject": row.subject,
                "to_name": ast.literal_eval(row.to_name_list) if row.to_name_list else [row.to_name],
                "to_mail": ast.literal_eval(row.to_mail_list) if row.to_mail_list else [row.to_mail],
                "from_name": row.from_name,
                "from_mail": row.from_mail,
                "cc_name": row.cc_name,
                "cc_mail": row.cc_mail,
                "received_at": row.received_at,
                "references": row.references,
                "status": row.status,
                "content": row.content,
                "company": row.company,
                "keyword": row.keyword,
                "last_content": row.last_content,
                "comment": row.comment,
                "manager": row.manager,
                "answering_content": row.answering_content,
                "html_s3_key": row.html_s3_key,
                "attachments": row.attachments,
                "cid_images": row.cid_images,
                "has_temp": row.has_temp
            } if row else {}

        except Exception as e:
            logging.error(f"[queries.post.PostQuery.get_title] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_send_data(db:AsyncSession, domain_data:SendEmailDomain):
        try:
            query = text(
                """
                    SELECT
                        cx_email.message_id as message_id,
                        cx_email.subject as received_subject,
                        cx_email_temp.subject as reply_subject,
                        cx_email_temp.to_mail as reply_to,
                        cx_email_temp.to_name as reply_to_name,
                        cx_email_temp.from_mail as reply_from,
                        cx_email_temp.from_name as reply_from_name,
                        cx_email_temp.cc_mail as reply_cc,
                        cx_email_temp.cc_name as reply_cc_name,
                        cx_email_temp.bcc_mail as reply_bcc,
                        cx_email_temp.bcc_name as reply_bcc_name,
                        cx_email.keyword as keyword,
                        cx_email.references as `references`,
                        cx_email.manager as manager_id,
                        cx_email_temp.comment as comment,
                        cx_email.received_at as received_at,
                        cx_email_temp.attachments as attachments,
                        cx_email.last_content as question_content,
                        cx_email_temp.answering_content as answer_content
                    FROM cx_email
                    INNER JOIN cx_email_temp ON cx_email.id = cx_email_temp.cx_email_id
                    WHERE cx_email.id = :cx_email_id
                        AND cx_email.company_key = :company_key
                """
            )
            params = {
                "cx_email_id": domain_data.id,
                "company_key": domain_data.company_key
            }
            result = await db.execute(query, params)
            row = result.fetchone()

            return {
                "message_id": row.message_id,
                "received_subject": row.received_subject,
                "reply_subject": row.reply_subject,
                "reply_to": row.reply_to,
                "reply_to_name": row.reply_to_name,
                "reply_from": row.reply_from,
                "reply_from_name": row.reply_from_name,
                "reply_cc": row.reply_cc,
                "reply_cc_name": row.reply_cc_name,
                "reply_bcc": row.reply_bcc,
                "reply_bcc_name": row.reply_bcc_name,
                "keyword": row.keyword,
                "references": row.references,
                "manager_id": row.manager_id,
                "comment": row.comment,
                "received_at": row.received_at,
                "attachments": row.attachments,
                "question_content": row.question_content,
                "answer_content": row.answer_content
            } if row else False

        except Exception as e:
            logging.error(f"[queries.cx_email.CXEmailQuery.get_send_data] Exception: {e}")
            raise DBError(e)

    @staticmethod
    async def get_cid_images_by_message_id(db:AsyncSession, domain_data: SendEmailDomain):
        try:
            query = text(
                """
                    SELECT cid_images
                    FROM cx_email
                    WHERE message_id = :message_id
                """
            )
            params = {"message_id": domain_data.from_message_id}

            result = await db.execute(query, params)
            row = result.fetchone()

            return row.cid_images if row else None

        except Exception as e:
            logging.error(f"[queries.cx_email.CXEmailQuery.get_cid_images_by_message_id] Exception: {e}")
            raise DBError


    @staticmethod
    async def get_all_thread_data_by_id(db:AsyncSession, domain_data: CheckHasThreadDomain):
        try:
            query = text(
                """
                    SELECT
                        ce.`references` as ref,
                        ce.received_at as compare_time,
                        target.message_id as target_message_id,
                        target.`references` as target_ref,
                        target.received_at as target_time
                    FROM cx_email ce
                    INNER JOIN cx_email_references cer ON ce.message_id = cer.message_id
                    INNER JOIN cx_email target ON target.id = :id
                    INNER JOIN cx_email_references target_ref ON target.message_id = target_ref.message_id
                    WHERE cer.first_message_id = target_ref.first_message_id
                """
            )
            params = {"id": domain_data.id}
            result = await db.execute(query, params)
            rows = result.fetchall()

            return [{
                "references": row.ref,
                "target_message_id": row.target_message_id,
                "target_references": row.target_ref,
                "compare_time": row.compare_time,
                "target_time": row.target_time
            } for row in rows] if rows else {}

        except Exception as e:
            logging.error(f"[queries.cx_email.CXEmailQuery.get_all_thread_data_by_id] Exception: {e}")
            raise DBError


    @staticmethod
    async def get_sent_rows(db:AsyncSession, domain_data:CheckHasThreadDomain):
        try:
            query = text(
                """
                    SELECT
                        esh.id
                    FROM cx_email ce
                        INNER JOIN email_send_history esh ON ce.message_id = esh.in_reply_to COLLATE utf8mb4_unicode_ci
                    WHERE ce.id = :id
                """
            )
            params = {"id": domain_data.id}
            result = await db.execute(query, params)
            rows = result.fetchall()

            return [{
                "id": row.id
            } for row in rows] if rows else {}

        except Exception as e:
            logging.error(f"[queries.cx_email.CXEmailQuery.get_all_thread_data_by_id] Exception: {e}")
            raise DBError


    @staticmethod
    async def get_dashboard_chart(db: AsyncSession, domain_data:GetDashboardChartDomain):
        try:
            params = {"answering": EMAIL_ANSWERING, "parsed": EMAIL_RECIEVED, "company_key": domain_data.company_key}
            where_conditions = ["company_key = :company_key"]

            # params
            if domain_data.client_timezone:
                offset_hours = cal_offset_hours(domain_data.client_timezone, "mysql")
                params["offset_hours"] = offset_hours
                params["timezone"] = domain_data.client_timezone
                date_diff_expr = "DATEDIFF(DATE_ADD(UTC_TIMESTAMP(), INTERVAL :offset_hours HOUR), DATE_ADD(received_at, INTERVAL :offset_hours HOUR)) as days"
            else:
                date_diff_expr = "DATEDIFF(UTC_TIMESTAMP(), received_at) as days"

            if domain_data.diff_date:
                params["chart_days"] = domain_data.diff_date

            # 날짜 필터
            if domain_data.start_date and domain_data.end_date:
                where_conditions.append("received_at >= :start_date AND received_at <= :end_date")
                params["start_date"] = domain_data.start_date
                params["end_date"] = domain_data.end_date
            elif domain_data.start_date:
                where_conditions.append("received_at >= :start_date")
                params["start_date"] = domain_data.start_date
            elif domain_data.end_date:
                where_conditions.append("received_at <= :end_date")
                params["end_date"] = domain_data.end_date

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            logging.info(f"params: {params}")

            query_str = f"""
                SELECT
                    COUNT(*) as count_all,
                    COUNT(CASE WHEN status = '{EMAIL_RECIEVED}' THEN 1 END) as count_parsed,
                    COUNT(CASE WHEN status = '{EMAIL_PENDING}' THEN 1 END) as count_pending,
                    COUNT(CASE WHEN status = '{EMAIL_ANSWERING}' THEN 1 END) as count_answering,
                    COUNT(CASE WHEN status = '{EMAIL_SENT}' THEN 1 END) as count_sent,
                    COUNT(CASE WHEN status = '{EMAIL_CLOSED}' THEN 1 END) as count_closed,
                    COUNT(CASE WHEN status = '{EMAIL_SPAM}' THEN 1 END) as count_spam,
                    (
                        SELECT GROUP_CONCAT(
                            CONCAT(days, ':', count) 
                            ORDER BY days
                            SEPARATOR ','
                        )
                        FROM (
                            SELECT
                                {date_diff_expr},
                                COUNT(*) as count
                            FROM cx_email
                            WHERE {where_clause}
                                AND status = :parsed
                            GROUP BY days
                        ) parsed_rows
                    ) as parsed_days_data,
                    (
                        SELECT GROUP_CONCAT(
                            CONCAT(days, ':', count) 
                            ORDER BY days
                            SEPARATOR ','
                        )
                        FROM (
                            SELECT
                                {date_diff_expr},
                                COUNT(*) as count
                            FROM cx_email
                            WHERE {where_clause}
                                AND status = :answering
                            GROUP BY days
                        ) answering_rows
                    ) as answering_days_data
                FROM cx_email
                WHERE {where_clause}
            """

            query = text(query_str)
            result = await db.execute(query, params)
            row = result.fetchone()
            domain_data.row = {
                "all": {
                    "countAll": row.count_all,
                    "countParsed": row.count_parsed,
                    "countPending": row.count_pending,
                    "countAnswering": row.count_answering,
                    "countSent": row.count_sent,
                    "countClosed": row.count_closed,
                    "countSpam": row.count_spam
                },
                "parsed_days_data": row.parsed_days_data,
                "answering_days_data": row.answering_days_data
            }
        except Exception as e:
            logging.error(f"[queries.cx_email.CXEmailQuery.get_dashboard_chart] Exception: {e}")
            raise DBError(e)


    @staticmethod
    async def get_in_count_per_days(db, domain_data:GetDashboardLineDomain):
        try:
            offset_hours = cal_offset_hours(domain_data.client_timezone, "mysql")

            params = {"spam": EMAIL_SPAM, "offset_hours": offset_hours}
            where_conditions = ["status != :spam"]

            # 동적 필터
            where_conditions.append("company_key = :company_key")
            params["company_key"] = domain_data.company_key

            # 날짜 필터
            if domain_data.start_date and domain_data.end_date:
                where_conditions.append("received_at >= :start_date AND received_at <= :end_date")
                params["start_date"] = domain_data.start_date
                params["end_date"] = domain_data.end_date
            elif domain_data.start_date:
                where_conditions.append("received_at >= :start_date")
                params["start_date"] = domain_data.start_date
            elif domain_data.end_date:
                where_conditions.append("received_at <= :end_date")
                params["end_date"] = domain_data.end_date

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            query = text(f"""
                SELECT
                    DATE(DATE_ADD(received_at, INTERVAL :offset_hours HOUR)) as days,
                    COUNT(*) as count
                FROM cx_email
                WHERE {where_clause}
                GROUP BY days
                ORDER BY days
            """)
            result = await db.execute(query, params)
            rows = result.fetchall()

            if not rows:
                domain_data.cx_email_row = []
            else:
                domain_data.cx_email_row = {
                    datetime_to_string(row.days): row.count
                for row in rows}
        except Exception as e:
            logging.error(f"[queries.cx_email.CXEmailQuery.get_in_count_per_days] Exception: {e}")
            raise DBError


    @staticmethod
    async def get_dashboard_manager_cnt(db:AsyncSession, domain_data:GetDashboardManagerCntDomain):
        try:
            params = {"company_key": domain_data.company_key}
            where_conditions = []

            # 동적 필터
            where_conditions.append("company_key = :company_key")
            params["company_key"] = domain_data.company_key

            # 날짜 필터
            if domain_data.start_date and domain_data.end_date:
                where_conditions.append("received_at >= :start_date AND received_at <= :end_date")
                params["start_date"] = domain_data.start_date
                params["end_date"] = domain_data.end_date
            elif domain_data.start_date:
                where_conditions.append("received_at >= :start_date")
                params["start_date"] = domain_data.start_date
            elif domain_data.end_date:
                where_conditions.append("received_at <= :end_date")
                params["end_date"] = domain_data.end_date

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            query = text(f"""
                SELECT 
                    manager,
                    COUNT(*) AS count
                FROM llm_platform.cx_email ce
                WHERE {where_clause}
                GROUP BY manager;
            """)
            result = await db.execute(query, params)
            rows = result.fetchall()
            if rows:
                for row in rows:
                    domain_data.row[row.manager] = row.count

        except Exception as e:
            logging.error(f"[queries.cx_email.CXEmailQuery.get_dashboard_manager_cnt] Exception: {e}")
            raise DBError(e)


    @staticmethod
    async def update_status(db:AsyncSession, domain_data:SendEmailDomain):
        try:
            query = text(
                """
                    UPDATE cx_email
                    SET
                        status = :status
                    WHERE message_id = :message_id
                """
            )
            params = {
                "status": "sent",
                "message_id": domain_data.from_message_id
            }
            await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.cx_email.CXEmailQuery.update_comment_and_status] Exception: {e}")
            raise DBError(e)


    @staticmethod
    async def set_manager(db:AsyncSession, domain_data: SetManagerDomain | ChangeStatusDomain):
        try:
            query = text(
                """
                    UPDATE cx_email
                    SET
                        manager = :manager
                    WHERE id = :id
                """
            )
            params = {
                "id": domain_data.id,
                "manager": domain_data.manager_id
            }
            await db.execute(query, params)
            await db.commit()

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.cx_email.CXEmailQuery.set_manager] Exception: {e}")
            raise DBError(e)


    @staticmethod
    async def change_status(db:AsyncSession, domain_data: ChangeStatusDomain):
        try:
            query = text(
                """
                    UPDATE cx_email
                    SET
                        status = :status
                    WHERE id = :id
                """
            )
            params = {
                "id": domain_data.id,
                "status": domain_data.status
            }
            await db.execute(query, params)
            await db. commit()

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.cx_email.CXEmailQuery.change_status] Exception: {e}")
            raise DBError(e)


    @staticmethod
    async def update_comment(db:AsyncSession, domain_data: UpdateReceiveCommentDomain):
        try:
            query = text(
                """
                    UPDATE cx_email
                    SET
                        comment = :comment
                    WHERE id = :id
                """
            )
            params = {
                "id": domain_data.id,
                "comment": domain_data.comment
            }
            await db.execute(query, params)
            await db. commit()

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.cx_email.CXEmailQuery.change_status] Exception: {e}")
            raise DBError(e)


    @staticmethod
    async def update_has_temp_to_true(db:AsyncSession, domain_data: InitAnswerDomain):
        try:
            query = text(
                """
                    UPDATE cx_email
                    SET
                        has_temp = True
                    WHERE id = :id
                """
            )
            params = {
                "id": domain_data.id
            }
            await db.execute(query, params)
            await db. commit()

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.cx_email.CXEmailQuery.change_status] Exception: {e}")
            raise DBError(e)


    @staticmethod
    async def update_company(db: AsyncSession, domain_data: UpdateCompanyDomain):
        try:
            query = text(
                """
                    UPDATE cx_email
                    SET
                        company = :company
                    WHERE id = :id
                        AND company_key = :company_key
                """
            )
            params = {
                "company": domain_data.company,
                "id": domain_data.id,
                "company_key": domain_data.company_key
            }
            await db.execute(query, params)
            await db.commit()

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.cx_email.CXEmailQuery.change_status] Exception: {e}")
            raise DBError(e)


    @staticmethod
    async def exists_message_id(db:AsyncSession, company_key:str, message_id:str) -> bool:
        try:
            query = text("SELECT id FROM cx_email WHERE company_key = :company_key AND message_id = :message_id LIMIT 1")
            row = (await db.execute(query, {"company_key": company_key, "message_id": message_id})).fetchone()
            return row is not None
        except Exception as e:
            logging.error(f"[queries.cx_email.CXEmailQuery.exists_message_id] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def insert_received(db:AsyncSession, values:dict) -> int:
        """수집기가 파싱한 수신 메일 1건 적재. 컬럼은 코드에 고정."""
        try:
            query = text("""
                INSERT INTO cx_email (
                    company_key, message_id, subject, from_mail, from_name, to_mail, to_name, to_mail_list, to_name_list,
                    cc_mail, cc_name, received_at, content, last_content, html_s3_key, attachments, `references`, status, issue_status, has_temp
                ) VALUES (
                    :company_key, :message_id, :subject, :from_mail, :from_name, :to_mail, :to_name, :to_mail_list, :to_name_list,
                    :cc_mail, :cc_name, :received_at, :content, :last_content, :html_s3_key, :attachments, :references, :status, 0, 0
                )
            """)
            result = await db.execute(query, values)
            await db.commit()
            return result.lastrowid
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.cx_email.CXEmailQuery.insert_received] DBError: {e}")
            raise DBError(e)
