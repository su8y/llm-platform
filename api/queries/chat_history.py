import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from domain.playground import *
from domain.monitoring import *
from utils.error import DBError
from utils.date import adapt_timezone_datetime_to_datetime


class ChatHistoryQuery:

    @staticmethod
    async def record_chat(db:AsyncSession, data: dict):

        """
        Record Chat History In Database
        """

        try:
            query = text("""
                INSERT INTO chat_history (
                    session_key, message, role, reg_date, company_key, 
                    asker_id, asker_name, rating, memo, issue_status, 
                    manager_id, assessor_id, question_id, refer_id, parser_id
                ) VALUES (
                    :session_key, :message, :role, :reg_date, :company_key,
                    :asker_id, :asker_name, :rating, :memo, :issue_status,
                    :manager_id, :assessor_id, :question_id, :refer_id, :parser_id
                ) RETURNING id, session_key, message, role, reg_date
            """)
            result = await db.execute(query, data)
            row = result.fetchone()
            await db.commit()
            return {
                "id": row[0],
                "session_key": row[1],
                "message": row[2],
                "role": row[3],
                "reg_date": row[4]
            } if row else None
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.chat_history.ChatHistoryQuery.record_chat] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_all_manager_id(db: AsyncSession, company_key: str):
        try:
            query = text("""
                SELECT DISTINCT manager_id 
                FROM chat_history 
                WHERE company_key = :company_key
            """)
            result = await db.execute(query, {"company_key": company_key})
            rows = result.fetchall()
            return [row[0] for row in rows] if rows else None
        except Exception as e:
            logging.error(f"[queries.chat_history.ChatHistoryQuery.get_all_manager_id] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_chat_rating(db: AsyncSession, domain_data:getChatRatingDomain):
        try:
            where_conditions = []
            params = {}

            # filter
            if domain_data.company_key is not None:
                where_conditions.append(f"company_key = :company_key")
                params["company_key"] = domain_data.company_key
            if domain_data.start_date_local and domain_data.end_date_local:
                where_conditions.append("reg_date >= :start_date_local AND reg_date <= :end_date_local")
                params["start_date_local"] = domain_data.start_date_local
                params["end_date_local"] = domain_data.end_date_local
            elif domain_data.start_date_local:
                where_conditions.append("reg_date >= :start_date_local")
                params["start_date_local"] = domain_data.start_date_local
            elif domain_data.end_date_local:
                where_conditions.append("reg_date <= :end_date_local")
                params["end_date_local"] = domain_data.end_date_local

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            query = text(f"""
                SELECT id, session_key, company_key, rating, reg_date 
                FROM chat_history
                WHERE {where_clause}
                ORDER BY reg_date DESC
            """)

            result = await db.execute(query, params)
            rows = result.fetchall()

            return [
                {
                    "id": row[0],
                    "session_key": row[1],
                    "company_key": row[2],
                    "rating": row[3],
                    "reg_date": row[4]
                } for row in rows
            ] if rows else None
        except Exception as e:
            logging.error(f"[queries.chat_history.ChatHistoryQuery.get_chat_rating] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_refer_id(db: AsyncSession, id: str):
        try:
            query = text("""
                SELECT
                    refer_id,
                    parser_id,
                    email_id,
                    sitemap_id,
                    question_id,
                    mcp_tools
                FROM chat_history
                WHERE id = :id
            """)
            result = await db.execute(query, {"id": id})
            row = result.fetchone()
            return (
                row.refer_id,
                row.parser_id,
                row.email_id,
                row.sitemap_id,
                row.question_id,
                row.mcp_tools
            ) if row else (None, None, None, None, None, None)
        except Exception as e:
            logging.error(f"[queries.chat_history.ChatHistoryQuery.get_refer_id] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_question(db: AsyncSession, domain_data: retrievalDomain):
        try:
            query = text("""
                SELECT
                    message
                FROM chat_history
                WHERE id = :id
            """)
            result = await db.execute(query, {"id": domain_data.question_id_str})
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            logging.error(f"[queries.chat_history.ChatHistoryQuery.get_question] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_rating(db: AsyncSession, id):
        try:
            if isinstance(id, str):
                query = text("""
                    SELECT
                        rating, memo
                    FROM chat_history
                    WHERE id = :id
                """)
                result = await db.execute(query, {"id": id})
                row = result.fetchone()
                return {"id": id, "rating": row[0], "comment": row[1]} if row else None
            elif isinstance(id, list):
                placeholders = ", ".join([f":id_{i}" for i in range(len(id))])
                params = {f"id_{i}": id_val for i, id_val in enumerate(id)}

                query = text(f"""
                    SELECT id, rating, memo
                    FROM chat_history
                    WHERE id IN ({placeholders})
                """)
                result = await db.execute(query, params)
                rows = result.fetchall()
                return [{"id": row[0], "rating": row[1], "comment": row[2]} for row in rows] if rows else None
        except Exception as e:
            logging.error(f"[queries.chat_history.ChatHistoryQuery.get_rating] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_conversation_data(db: AsyncSession, id: str | list[str]):
        try:
            if isinstance(id, str):
                query = text("""
                    SELECT
                        rating, memo
                    FROM chat_history
                    WHERE id = :id
                """)
                result = await db.execute(query, {"id": id})
                row = result.fetchone()
                return [{"id": id, "rating": row[0], "comment": row[1]}] if row else None
            elif isinstance(id, list):
                query = text("""
                    SELECT
                        id, rating, memo
                    FROM chat_history
                    WHERE id = :id
                """)
                result = await db.execute(query, {"id": id})
                rows = result.fetchall()
                return [{"id": row[0], "rating": row[1], "comment": row[2]} for row in rows] if rows else None
        except Exception as e:
            logging.error(f"[queries.chat_history.ChatHistoryQuery.get_conversation_data] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_chat_count(
    db: AsyncSession,
    domain_data:getChatCountDomain
    ) -> list:
        try:
            params = {}
            where_conditions = []

            # 동적 필터
            if domain_data.company_key:
                where_conditions.append("company_key = :company_key")
                params["company_key"] = domain_data.company_key

            # 날짜 필터
            if domain_data.start_date and domain_data.end_date:
                where_conditions.append("reg_date >= :start_date AND reg_date <= :end_date")
                params["start_date"] = domain_data.start_date
                params["end_date"] = domain_data.end_date
            elif domain_data.start_date:
                where_conditions.append("reg_date >= :start_date")
                params["start_date"] = domain_data.start_date
            elif domain_data.end_date:
                where_conditions.append("reg_date <= :end_date")
                params["end_date"] = domain_data.end_date

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            query = text(f"""
                SELECT session_key, role, reg_date
                FROM chat_history
                WHERE {where_clause}
            """)

            result = await db.execute(query, params)
            rows = result.fetchall()

            return [
                {
                    "session_key": row[0],
                    "role": row[1],
                    "reg_date": adapt_timezone_datetime_to_datetime(row[2], "UTC")
                }
                for row in rows
            ] if rows else []

        except Exception as e:
            logging.error(f"[queries.chat_history.ChatHistoryQuery.get_chat_count] Exception: {e}")
            raise e

    @staticmethod
    async def get_chat_history_by_session_list(db: AsyncSession, domain_data:getConversationHistoryDomain | getChatHistoryDomain | getConversationHistoryTitleDomain):
        try:
            if not domain_data.session_list:
                return []

            # WHERE 절 조건 생성
            where_conditions = list()
            params = dict()

            where_conditions.append("ch.session_key IN :session_list")
            params["session_list"] = domain_data.session_list

            # 날짜 필터 조건 추가
            if domain_data.start_date and domain_data.end_date:
                where_conditions.append("ch.reg_date BETWEEN :start_date AND :end_date")
                params.update({"start_date": domain_data.start_date, "end_date": domain_data.end_date})
            elif domain_data.start_date:
                where_conditions.append("ch.reg_date >= :start_date")
                params.update({"start_date": domain_data.start_date})
            elif domain_data.end_date:
                where_conditions.append("ch.reg_date <= :end_date")
                params.update({"end_date": domain_data.end_date})

            where_clause = " AND ".join(where_conditions)

            query = text("""
                SELECT 
                    ch.*,
                    ct.title as chat_title
                FROM 
                    chat_history ch
                LEFT OUTER JOIN 
                    chat_title ct ON ch.session_key = ct.session_key
                WHERE 
                    """ + where_clause + """
                ORDER BY 
                    ch.reg_date DESC
            """)

            result = await db.execute(query, params)
            rows = result.fetchall()

            # 결과를 딕셔너리 리스트로 변환
            return [{
                'id': row.id,
                'session_key': row.session_key,
                'message': row.message,
                'role': row.role,
                'reg_date': row.init_date if row.init_date and row.role == "human" else row.reg_date,
                'chat_title': row.chat_title,
                'issue_status': row.issue_status,
                'asker_name': row.asker_name,
                'asker_id': row.asker_id,
                'manager_id': row.manager_id,
                'assessor_id': row.assessor_id,
                'rating': row.rating,
                'memo': row.memo,
                'is_mcp': row.is_mcp
            } for row in rows] if rows else None

        except Exception as e:
            logging.error(f"[queries.chat_history.ChatHistoryQuery.get_chat_history_by_session_list] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_chat_history_by_session_key(db: AsyncSession, domain_data:getConversationHistoryDomain|getChatTitleDomain):
        try:
            query = text("""
                SELECT 
                    id, session_key, message, role, reg_date, company_key,
                    asker_id, asker_name, rating, memo, issue_status,
                    manager_id, assessor_id, question_id, refer_id, parser_id, is_mcp, mcp_tools
                FROM chat_history
                WHERE session_key = :session_key
                ORDER BY reg_date ASC
            """)

            result = await db.execute(query, {"session_key": domain_data.session_key})
            rows = result.fetchall()

            return [
                {
                    "id": row[0],
                    "session_key": row[1],
                    "message": row[2],
                    "role": row[3],
                    "reg_date": row[4],
                    "company_key": row[5],
                    "asker_id": row[6],
                    "asker_name": row[7],
                    "rating": row[8],
                    "memo": row[9],
                    "issue_status": row[10],
                    "manager_id": row[11],
                    "assessor_id": row[12],
                    "question_id": row[13],
                    "refer_id": row[14],
                    "parser_id": row[15],
                    "is_mcp": row[16],
                    "mcp_tools": row[17]
                } for row in rows
            ] if rows else None

        except Exception as e:
            logging.error(f"[queries.chat_history.ChatHistoryQuery.get_chat_history_by_session_key] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_session_list(db: AsyncSession, domain_data:getConversationHistoryTitleDomain | getChatHistoryDomain):
        try:
            is_pagination = True if domain_data.page and domain_data.per_page else False

            # 기본 WHERE 절 조건 생성
            where_conditions = []
            params = {}

            # 동적 필터 조건 추가
            if domain_data.company_key:
                where_conditions.append("company_key = :company_key")
                params["company_key"] = domain_data.company_key
            if domain_data.asker_id:
                where_conditions.append("asker_id = :asker_id")
                params["asker_id"] = domain_data.asker_id
            if domain_data.manager_id:
                where_conditions.append("manager_id = :manager_id")
                params["manager_id"] = domain_data.manager_id
            if domain_data.issue_status:
                where_conditions.append("issue_status = :issue_status")
                params["issue_status"] = domain_data.issue_status
            if isinstance(domain_data.is_mcp, bool):
                condition = "is_mcp is true" if domain_data.is_mcp else "is_mcp is not true"
                where_conditions.append(condition)

            # 날짜 필터 조건 추가
            if domain_data.start_date and domain_data.end_date:
                where_conditions.append("reg_date BETWEEN :start_date AND :end_date")
                params.update({"start_date": domain_data.start_date, "end_date": domain_data.end_date})
            elif domain_data.start_date:
                where_conditions.append("reg_date >= :start_date")
                params.update({"start_date": domain_data.start_date})
            elif domain_data.end_date:
                where_conditions.append("reg_date <= :end_date")
                params.update({"end_date": domain_data.end_date})

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # 전체 세션 수를 가져오는 쿼리
            count_query = text(f"""
                SELECT COUNT(DISTINCT session_key) 
                FROM chat_history 
                WHERE {where_clause}
            """)

            # 세션 목록을 가져오는 메인 쿼리
            main_query = text(f"""
                WITH RankedSessions AS (
                    SELECT 
                        session_key,
                        reg_date,
                        ROW_NUMBER() OVER (PARTITION BY session_key ORDER BY reg_date DESC) as rn
                    FROM chat_history
                    WHERE {where_clause}
                )
                SELECT 
                    session_key,
                    reg_date
                FROM RankedSessions
                WHERE rn = 1
                ORDER BY reg_date DESC
                {f'LIMIT :per_page OFFSET :offset' if is_pagination else ''}
            """)

            # 전체 카운트 실행
            result = await db.execute(count_query, params)
            count = result.scalar()

            if count == 0:
                return (None, 0)

            # 페이지네이션 파라미터 추가
            if is_pagination:
                params.update({
                    "per_page": domain_data.per_page,
                    "offset": (domain_data.page - 1) * domain_data.per_page
                })

            # 메인 쿼리 실행
            result = await db.execute(main_query, params)
            sessions = result.fetchall()

            session_list = tuple(session.session_key for session in sessions) if sessions else None

            return (session_list, count)

        except Exception as e:
            logging.error(f"[queries.chat_history.ChatHistoryQuery.get_session_list] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_chat_history_head(db: AsyncSession, domain_data:getChatHistoryDetailHeadDomain):
        try:
            # Apply dynamic filters
            where_conditions = ["role = 'human'"]
            params = {}

            if domain_data.company_key is not None:
                where_conditions.append(f"company_key = :company_key")
                params["company_key"] = domain_data.company_key
            if domain_data.session_key is not None:
                where_conditions.append(f"session_key = :session_key")
                params["session_key"] = domain_data.session_key

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            query = text(f"""
                SELECT
                    session_key,
                    issue_status,
                    reg_date,
                    asker_id,
                    asker_name,
                    rating,
                    manager_id,
                    assessor_id,
                    init_date
                FROM chat_history
                WHERE {where_clause}
                ORDER BY reg_date DESC
            """)

            # Apply pagination
            results = await db.execute(query, params)
            rows = results.fetchall()
            return [
                {
                    "session_key": row[0],
                    "issue_status": row[1],
                    "reg_date": row[8] if row[8] else row[2],
                    "asker_id": row[3],
                    "asker_name": row[4],
                    "rating": row[5],
                    "manager_id": row[6],
                    "assessor_id": row[7]
                 } for row in rows
            ] if rows else None
        except Exception as e:
            logging.error(f"[queries.chat_history.ChatHistoryQuery.get_chat_history_head] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_chat_history_tail(
        db: AsyncSession,
        domain_data:getChatHistoryDetailTailDomain
    ):
        try:
            params = {}
            where_conditions = []

            if domain_data.company_key is not None:
                where_conditions.append(f"company_key = :company_key")
                params["company_key"] = domain_data.company_key
            if domain_data.session_key is not None:
                where_conditions.append(f"session_key = :session_key")
                params["session_key"] = domain_data.session_key

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # 페이지네이션이 있는 경우, human role의 id를 먼저 구함
            if domain_data.page:
                subquery_sql = f"""
                    SELECT id
                    FROM chat_history
                    WHERE role = 'human' AND {where_clause}
                    ORDER BY reg_date ASC
                    LIMIT :per_page OFFSET :offset
                """
                params["per_page"] = domain_data.per_page
                params["offset"] = (domain_data.page - 1) * domain_data.per_page
                subquery_result = await db.execute(text(subquery_sql), params)
                question_ids = tuple(row[0] for row in subquery_result.fetchall())
                if not question_ids:
                    return []

                # 메인 쿼리: id 또는 question_id가 위 id에 포함된 것
                main_where = f"(id IN :question_ids OR question_id IN :question_ids)"
                params["question_ids"] = question_ids
                if where_conditions:
                    main_where += f" AND {where_clause}"
                main_sql = f"""
                    SELECT id, message, role, reg_date, init_date, memo, rating
                    FROM chat_history
                    WHERE {main_where}
                    ORDER BY reg_date DESC
                """
                result = await db.execute(text(main_sql), params)
            else:
                # 페이지네이션 없이 전체
                main_sql = f"""
                    SELECT id, message, role, reg_date, init_date, memo, rating
                    FROM chat_history
                    WHERE {where_clause}
                    ORDER BY reg_date DESC
                """
                result = await db.execute(text(main_sql), params)

            rows = result.fetchall()
            return [
                {
                    "id": row.id,
                    "message": row.message,
                    "role": row.role,
                    "reg_date": row.init_date if row.role == "human" and row.init_date else row.reg_date,
                    "memo": row.memo,
                    "rating": row.rating
                } for row in rows
            ] if rows else None
        except Exception as e:
            logging.error(f"[queries.chat_history.ChatHistoryQuery.get_chat_history_tail] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_chat_history_tail_count(
        db: AsyncSession,
        domain_data:getChatHistoryDetailTailDomain
    ):
        try:
            params = {}
            where_conditions = []
            if domain_data.company_key is not None:
                where_conditions.append(f"company_key = :company_key")
                params["company_key"] = domain_data.company_key
            if domain_data.session_key is not None:
                where_conditions.append(f"session_key = :session_key")
                params["session_key"] = domain_data.session_key
            if domain_data.page:
                where_conditions.append("role = 'human'")
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            sql = f"SELECT COUNT(*) FROM chat_history WHERE {where_clause}"
            result = await db.execute(text(sql), params)
            count = result.scalar()
            return count
        except Exception as e:
            logging.error(f"[queries.chat_history.ChatHistoryQuery.get_chat_history_tail_count] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def update_conversation_history(db: AsyncSession, domain_data:updateConversationHistoryDomain):
        try:
            if not domain_data.rating and not domain_data.memo:
                return None

            set_clauses = []
            params = {"id": domain_data.id}

            if domain_data.rating is not None:
                set_clauses.append("rating = :rating")
                params["rating"] = domain_data.rating

            if domain_data.memo is not None:
                set_clauses.append("memo = :memo")
                params["memo"] = domain_data.memo

            set_clause = ", ".join(set_clauses)

            query = text(f"""
                UPDATE chat_history
                SET {set_clause}
                WHERE id = :id
            """)
            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.chat_history.ChatHistoryQuery.update_conversation_history] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def update_chat_history(db: AsyncSession, domain_data:updateChatHistoryDomain):
        try:
            set_conditions = []
            params = {
                "company_key": domain_data.company_key,
                "session_key": domain_data.session_key
            }

            if domain_data.manager_id:
                set_conditions.append("manager_id = :manager_id")
                params["manager_id"] = domain_data.manager_id
            if domain_data.issue_status:
                set_conditions.append("issue_status = :issue_status")
                params["issue_status"] = domain_data.issue_status
            if domain_data.rating:
                set_conditions.append("rating = :rating")
                params["rating"] = domain_data.rating
            if domain_data.assessor_id:
                set_conditions.append("assessor_id = :assessor_id")
                params["assessor_id"] = domain_data.assessor_id

            set_clause = ", ".join(set_conditions)

            query = text(f"""
                UPDATE chat_history
                SET {set_clause}
                WHERE company_key = :company_key AND session_key = :session_key
                RETURNING id, session_key, message, role, reg_date, company_key,
                          asker_id, asker_name, rating, memo, issue_status,
                          manager_id, assessor_id, question_id, refer_id, parser_id
            """)

            result = await db.execute(query, params)
            rows = result.fetchall()

            await db.commit()

            return [
                {
                    "id": row[0],
                    "session_key": row[1],
                    "message": row[2],
                    "role": row[3],
                    "reg_date": row[4],
                    "company_key": row[5],
                    "asker_id": row[6],
                    "asker_name": row[7],
                    "rating": row[8],
                    "memo": row[9],
                    "issue_status": row[10],
                    "manager_id": row[11],
                    "assessor_id": row[12],
                    "question_id": row[13],
                    "refer_id": row[14],
                    "parser_id": row[15]
                } for row in rows
            ] if rows else None

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.chat_history.ChatHistoryQuery.update_chat_history] DBError: {e}")
            raise DBError(e)
