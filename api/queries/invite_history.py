import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.error import DBError
from utils.date import adapt_timezone_datetime_to_datetime
from domain.user import registerDomain, certificateDomain, getRegisterInfoDomain
from domain.admin import inviteMemberDomain, reInviteMemberDomain, getMembersDomain, deleteUserDomain, acceptDomain



class InviteHistoryQuery:

    @staticmethod
    async def insert_metadata(db:AsyncSession, **kwargs):
        try:
            query = text("""
                INSERT INTO invite_history (id, company_key, email_address_invite, success, accept)
                VALUES (:id, :company_key, :email_address_invite, :success, :accept)
            """)
            await db.execute(query, kwargs)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.invite_history.InviteHistoryQuery.insert_metadata] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def insert_invite_history(db:AsyncSession, domain_data:inviteMemberDomain | reInviteMemberDomain):
        """
        data format\n\n
        {
            "id": int
            "email_address_invite": str,
            "auth_key": str,
            "auth_key_exp_date": datetime,
            "invite_date": datetime,
            "invite_url": str,
            "success": boolean,
            "company_key": str
        }
        """

        try:
            query = text("""
                INSERT INTO invite_history 
                (email_address_invite, company_key, auth_key, auth_key_exp_date, invite_date, invite_url, success)
                VALUES 
                (:email_address_invite, :company_key, :auth_key, :auth_key_exp_date, :invite_date, :invite_url, :success)
            """)

            if isinstance(domain_data.insert_data, (list, tuple)):
                async with db.begin_nested():
                    for item in domain_data.insert_data:
                        await db.execute(query, item)
            else:
                await db.execute(query, domain_data.insert_data)

            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.invite_history.InviteHistoryQuery.insert_invite_history] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_members(db:AsyncSession, page:int, per_page:int, start_date:datetime, end_date:datetime, **filters):
        try:
            offset = (page - 1) * per_page

            # 기본 JOIN 및 SELECT 부분
            base_query = """
                SELECT
                    ih.id,
                    ih.email_address_invite,
                    ih.auth_key_exp_date,
                    ih.invite_date,
                    ih.success,
                    ih.accept,
                    ui.user_id,
                    ui.email_address,
                    ui.user_auth,
                    ua.auth_name,
                    ui.department
                FROM invite_history ih
                LEFT JOIN user_info ui ON ih.email_address_invite = ui.email_address
                LEFT JOIN user_auth ua ON ui.user_auth = ua.id
                WHERE ih.company_key = :company_key
                    AND ih.id != 1
            """

            # 필터 조건 구성
            params = {"company_key": filters["company_key"], "offset": offset, "per_page": per_page}

            # 날짜 필터
            if start_date and end_date:
                base_query += " AND ih.invite_date >= :start_date AND ih.invite_date <= :end_date"
                params["start_date"] = start_date
                params["end_date"] = end_date
            elif start_date:
                base_query += " AND ih.invite_date >= :start_date"
                params["start_date"] = start_date
            elif end_date:
                base_query += " AND ih.invite_date <= :end_date"
                params["end_date"] = end_date

            # 추가 필터링
            for attr, value in filters.items():
                if attr == 'email_address_invite':
                    base_query += " AND ih.email_address_invite LIKE :email_pattern"
                    params["email_pattern"] = f"%{value}%"
                elif attr == 'accept' or attr == 'success':
                    base_query += f" AND ih.{attr} = :{attr}"
                    params[attr] = value
                elif attr == 'waiting_now':
                    base_query += " AND ih.auth_key_exp_date > :waiting_date AND ih.accept = FALSE AND ih.success = TRUE"
                    params["waiting_date"] = value
                elif attr == 'expired_now':
                    base_query += " AND ih.auth_key_exp_date < :expired_date AND ih.accept = FALSE AND ih.success = TRUE"
                    params["expired_date"] = value
                elif attr == 'auth_name':
                    base_query += " AND ua.auth_name = :auth_name"
                    params["auth_name"] = value
                elif attr == 'user_id' or attr == 'department':
                    base_query += f" AND ui.{attr} LIKE :{attr}_pattern"
                    params[f"{attr}_pattern"] = f"%{value}%"

            # 정렬 및 페이지네이션
            base_query += " ORDER BY ih.invite_date DESC LIMIT :per_page OFFSET :offset"

            result = await db.execute(text(base_query), params)
            rows = result.fetchall()

            return [
                {
                    "id": row[0],
                    "email_address_invite": row[1],
                    "auth_key_exp_date": adapt_timezone_datetime_to_datetime(row[2], "UTC"),
                    "invite_date": adapt_timezone_datetime_to_datetime(row[3], "UTC"),
                    "success": row[4],
                    "accept": row[5],
                    "user_id": row[6],
                    "email_address": row[7],
                    "user_auth": row[8],
                    "auth_name": row[9],
                    "department": row[10]
                } for row in rows
            ] if rows else None
        except Exception as e:
            logging.error(f"[queries.invite_history.InviteHistoryQuery.get_members] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_members_count(db:AsyncSession, start_date, end_date, **filters):
        try:
            base_query = """
                SELECT COUNT(*)
                FROM invite_history ih
                LEFT JOIN user_info ui
                    ON ih.email_address_invite = ui.email_address
                LEFT JOIN user_auth ua
                    ON ui.user_auth = ua.id
                WHERE ih.company_key = :company_key
                    AND ih.id != 1
            """

            params = {"company_key": filters["company_key"]}

            # 날짜 필터
            if start_date and end_date:
                base_query += " AND ih.invite_date >= :start_date AND ih.invite_date <= :end_date"
                params["start_date"] = start_date
                params["end_date"] = end_date
            elif start_date:
                base_query += " AND ih.invite_date >= :start_date"
                params["start_date"] = start_date
            elif end_date:
                base_query += " AND ih.invite_date <= :end_date"
                params["end_date"] = end_date

            # 추가 필터링
            for attr, value in filters.items():
                if attr == 'email_address_invite':
                    base_query += " AND ih.email_address_invite LIKE :email_pattern"
                    params["email_pattern"] = f"%{value}%"
                elif attr == 'accept' or attr == 'success':
                    base_query += f" AND ih.{attr} = :{attr}"
                    params[attr] = value
                elif attr == 'waiting_now':
                    base_query += " AND ih.auth_key_exp_date > :waiting_date AND ih.accept = FALSE AND ih.success = NULL"
                    params["waiting_date"] = value
                elif attr == 'expired_now':
                    base_query += " AND ih.auth_key_exp_date < :expired_date AND ih.accept = FALSE AND ih.success = NULL"
                    params["expired_date"] = value
                elif attr == 'auth_name':
                    base_query += " AND ua.auth_name = :auth_name"
                    params["auth_name"] = value
                elif attr == 'user_id' or attr == 'department':
                    base_query += f" AND ui.{attr} LIKE :{attr}_pattern"
                    params[f"{attr}_pattern"] = f"%{value}%"

            result = await db.execute(text(base_query), params)
            count = result.scalar()
            return count
        except Exception as e:
            logging.error(f"[queries.invite_history.InviteHistoryQuery.get_members_count] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_slave_info(db:AsyncSession, domain_data:getRegisterInfoDomain):
        try:
            query = text("""
                SELECT ci.company_name, ih.email_address_invite, ci.lang
                FROM invite_history ih
                JOIN company_info ci
                    ON ih.company_key = ci.company_key
                WHERE ih.auth_key = :auth_key
            """)
            result = await db.execute(query, {"auth_key": domain_data.invitation_key})
            row = result.fetchone()
            return {
                "company_name": row[0],
                "email_address_invite": row[1],
                "lang": row[2]
            } if row else None
        except Exception as e:
            logging.error(f"[queries.invite_history.InviteHistoryQuery.get_slave_info] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_id_and_expire_time(db:AsyncSession, domain_data:acceptDomain):
        try:
            query = text("""
                SELECT id, auth_key_exp_date
                FROM invite_history
                WHERE auth_key = :auth_key
            """)
            result = await db.execute(query, {"auth_key": domain_data.auth_key})
            row = result.fetchone()
            return {
                "id": row[0],
                "auth_key_exp_date": adapt_timezone_datetime_to_datetime(row[1], "UTC")
            } if row else None
        except Exception as e:
            logging.error(f"[queries.invite_history.InviteHistoryQuery.get_id_and_expire_time] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_invite_email_set(db:AsyncSession, domain_data:inviteMemberDomain):
        try:
            query = text("""
                SELECT email_address_invite
                FROM invite_history
                WHERE (company_key = :company_key AND auth_key_exp_date > :current AND success = TRUE)
                    OR accept = TRUE
            """)
            result = await db.execute(query, {"company_key": domain_data.company_key, "current": domain_data.invite_date})
            rows = result.fetchall()
            return set([row[0] for row in rows]) if rows else []
        except Exception as e:
            logging.error(f"[queries.invite_history.InviteHistoryQuery.get_invite_email_set] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_register_info_by_auth_key(db:AsyncSession, domain_data:registerDomain):
        try:
            query = text("""
                SELECT id, company_key
                FROM invite_history
                WHERE auth_key = :auth_key
            """)
            result = await db.execute(query, {"auth_key": domain_data.invitation_key})
            row = result.fetchone()
            return {
                "invite_history_id": row[0],
                "company_key": row[1]
            } if row else None
        except Exception as e:
            logging.error(f"[queries.invite_history.InviteHistoryQuery.get_register_info_by_auth_key] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_data_by_id(db:AsyncSession, domain_data:registerDomain | certificateDomain):
        try:
            # 동적으로 SET 절 구성
            set_clauses = []
            params = {"id": domain_data.invite_history_id}

            if domain_data.invite_date:
                set_clauses.append("invite_date = :invite_date")
                params["invite_date"] = domain_data.invite_date
            if domain_data.accept:
                set_clauses.append("accept = :accept")
                params["accept"] = domain_data.accept

            set_clause = ", ".join(set_clauses)

            query = text(f"""
                UPDATE invite_history
                SET {set_clause}
                WHERE id = :id
            """)

            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.invite_history.InviteHistoryQuery.update_data_by_id] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_accept(db:AsyncSession, invite_history_id:int, update_data:dict):
        try:
            # 동적으로 SET 절 구성
            set_clauses = []
            params = {"id": invite_history_id}

            for key, value in update_data.items():
                set_clauses.append(f"{key} = :{key}")
                params[key] = value

            set_clause = ", ".join(set_clauses)

            query = text(f"""
                UPDATE invite_history
                SET {set_clause}
                WHERE id = :id
            """)

            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.invite_history.InviteHistoryQuery.update_accept] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_success(db:AsyncSession, auth_key:str, update_data:dict):
        try:
            # 동적으로 SET 절 구성
            set_clauses = []
            params = {"auth_key": auth_key}

            for key, value in update_data.items():
                set_clauses.append(f"{key} = :{key}")
                params[key] = value

            set_clause = ", ".join(set_clauses)

            query = text(f"""
                UPDATE invite_history
                SET {set_clause}
                WHERE auth_key = :auth_key
            """)

            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.invite_history.InviteHistoryQuery.update_success] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def bulk_update_success_by_auth_key(db:AsyncSession, update_data:list):
        try:
            # 각 항목별로 별도 쿼리 실행
            async with db.begin_nested():
                for data in update_data:
                    # 동적으로 SET 절 구성
                    set_clauses = []
                    params = {"auth_key": data["auth_key"]}

                    # auth_key를 제외한 다른 키-값 처리
                    for key, value in data.items():
                        if key != "auth_key":
                            set_clauses.append(f"{key} = :{key}")
                            params[key] = value

                    set_clause = ", ".join(set_clauses)

                    query = text(f"""
                        UPDATE invite_history
                        SET {set_clause}
                        WHERE auth_key = :auth_key
                    """)

                    await db.execute(query, params)

            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.invite_history.InviteHistoryQuery.bulk_update_success_by_auth_key] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_invite_history_date(db:AsyncSession, invite_history_id:str, update_data:dict):
        try:
            # 동적으로 SET 절 구성
            set_clauses = []
            params = {"id": invite_history_id}

            for key, value in update_data.items():
                set_clauses.append(f"{key} = :{key}")
                params[key] = value

            set_clause = ", ".join(set_clauses)

            query = text(f"""
                UPDATE invite_history
                SET {set_clause}
                WHERE id = :id
            """)

            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.invite_history.InviteHistoryQuery.update_invite_history_date] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_error_message(db:AsyncSession, auth_key:str, update_data:dict):
        try:
            # 동적으로 SET 절 구성
            set_clauses = []
            params = {"auth_key": auth_key}

            for key, value in update_data.items():
                set_clauses.append(f"{key} = :{key}")
                params[key] = value

            set_clause = ", ".join(set_clauses)

            query = text(f"""
                UPDATE invite_history
                SET {set_clause}
                WHERE auth_key = :auth_key
            """)

            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.invite_history.InviteHistoryQuery.update_error_message] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def delete_by_id(db:AsyncSession, domain_data:deleteUserDomain):
        try:
            query = text("""
                DELETE FROM invite_history
                WHERE id = :id
            """)

            await db.execute(query, {"id": domain_data.invite_history_id})
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.invite_history.InviteHistoryQuery.delete_by_id] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_members_with_count(db:AsyncSession, domain_data:getMembersDomain):
        try:
            # 파라미터 추출
            page = domain_data.page
            per_page = domain_data.per_page
            start_date = domain_data.start_date
            end_date = domain_data.end_date
            filters = domain_data.filters
            offset = (page - 1) * per_page

            # 파라미터 초기화
            params = {
                'company_key': filters['company_key'],
                'offset': offset,
                'per_page': per_page
            }

            # 날짜 조건 구성
            date_conditions = []
            if start_date:
                date_conditions.append("ih.invite_date >= :start_date")
                params['start_date'] = start_date
            if end_date:
                date_conditions.append("ih.invite_date <= :end_date")
                params['end_date'] = end_date

            # 필터 조건 구성
            filter_conditions = []
            for attr, value in filters.items():
                if attr == 'email_address_invite':
                    filter_conditions.append("ih.email_address_invite LIKE :email")
                    params['email'] = f"%{value}%"
                elif attr in ['accept', 'success']:
                    filter_conditions.append(f"ih.{attr} = :{attr}")
                    params[attr] = value
                elif attr == 'waiting_now':
                    filter_conditions.append("ih.auth_key_exp_date > :waiting_date AND ih.accept = 0 AND ih.success = 1")
                    params['waiting_date'] = value
                elif attr == 'expired_now':
                    filter_conditions.append("ih.auth_key_exp_date < :expired_date AND ih.accept = 0 AND ih.success = 1")
                    params['expired_date'] = value
                elif attr == 'auth_name':
                    filter_conditions.append("ua.auth_name = :auth_name")
                    params['auth_name'] = value
                elif attr in ['user_id', 'department']:
                    filter_conditions.append(f"ui.{attr} LIKE :{attr}")
                    params[attr] = f"%{value}%"

            # 쿼리 조건 문자열 생성
            condition_list = []
            if date_conditions:
                condition_list.append("(" + " AND ".join(date_conditions) + ")")
            if filter_conditions:
                condition_list.append("(" + " AND ".join(filter_conditions) + ")")

            additional_conditions = " AND ".join(condition_list) if condition_list else ""

            # 카운트 쿼리
            count_query = f"""
                SELECT COUNT(*) 
                FROM invite_history ih
                LEFT JOIN user_info ui ON ih.email_address_invite = ui.email_address
                LEFT JOIN user_auth ua ON ui.user_auth = ua.id
                WHERE ih.company_key = :company_key AND ih.id != 1
                {' AND ' + additional_conditions if additional_conditions else ''}
            """

            # 데이터 쿼리
            data_query = f"""
                SELECT 
                    ih.id,
                    ih.email_address_invite,
                    ih.auth_key_exp_date,
                    ih.invite_date,
                    ih.success,
                    ih.accept,
                    ui.user_id,
                    ui.email_address,
                    ui.user_auth,
                    ua.auth_name,
                    ui.department
                FROM invite_history ih
                LEFT JOIN user_info ui
                    ON ih.email_address_invite = ui.email_address
                LEFT JOIN user_auth ua
                    ON ui.user_auth = ua.id
                WHERE ih.company_key = :company_key
                    AND ih.id != 1
                {' AND ' + additional_conditions if additional_conditions else ''}
                ORDER BY ih.invite_date DESC
                LIMIT :per_page OFFSET :offset
            """

            # 쿼리 실행
            count_result = await db.execute(text(count_query), params)
            total_count = count_result.scalar()

            # 결과 처리
            if total_count == 0:
                return {
                    "count": 0,
                    "rows": []
                }

            else:
                data_result = await db.execute(text(data_query), params)
                rows = data_result.fetchall()

                # 결과 포맷팅
                formatted_results = [
                    {
                        "id": row[0],
                        "email_address_invite": row[1],
                        "auth_key_exp_date": adapt_timezone_datetime_to_datetime(row[2], "UTC"),
                        "invite_date": adapt_timezone_datetime_to_datetime(row[3], "UTC"),
                        "success": row[4],
                        "accept": row[5],
                        "user_id": row[6],
                        "email_address": row[7],
                        "user_auth": row[8],
                        "auth_name": row[9],
                        "department": row[10]
                    } for row in rows
                ]

                return {
                    "count": total_count,
                    "rows": formatted_results
                }
        except Exception as e:
            logging.error(f"[queries.invite_history.InviteHistoryQuery.get_members_with_count] DBError: {e}")
            raise DBError(e)
