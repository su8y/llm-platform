import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.error import DBError
from domain.reference import *



class PostQuery:
    @staticmethod
    async def insert_post(db:AsyncSession, domain_data:insertPostDomain | insertPostTemporaryDomain):
        '''
        # params
        data = {
            "company_key":str,
            "title":str,
            "content":str,
            "image_url":str,
            "content_admin":str,
            "is_show":bool,
            "is_on":bool,
            "lang":str,
            "author":str
        }
        '''
        try:
            # 동적으로 컬럼과 값 목록 생성
            columns = ["company_key", "title", "content", "image_url", "reg_date", "update_date", "is_on", "is_show", "author", "lang", "post_category_id", "category_depth_1_id", "category_depth_2_id"]
            values = [":company_key", ":title", ":content", ":image_url", ":reg_date", ":update_date", ":is_on", ":is_show", ":author", ":lang", ":post_category_id", ":category_depth_1_id", ":category_depth_2_id"]
            params = {
                "company_key": domain_data.company_key,
                "title": domain_data.title,
                "content": domain_data.content,
                "image_url": domain_data.image_url,
                "reg_date": domain_data.reg_date,
                "update_date": domain_data.update_date,
                "is_on": domain_data.is_on,
                "is_show": domain_data.is_show,
                "author": domain_data.author,
                "lang": domain_data.lang,
                "post_category_id": domain_data.post_category_id,
                "category_depth_1_id": domain_data.category_depth_1_id,
                "category_depth_2_id": domain_data.category_depth_2_id
            }
            if domain_data.is_temp:
                columns.append("is_temp")
                values.append(":is_temp")
                params["is_temp"] = domain_data.is_temp

            columns_str = ", ".join(columns)
            values_str = ", ".join(values)

            query = text(f"""
                INSERT INTO post ({columns_str})
                VALUES ({values_str})
                -- RETURNING *
            """)

            result = await db.execute(query, params)
            insert_id = result.lastrowid
            select_query = text("""
                SELECT * FROM post WHERE id = :id
            """)
            select_result = await db.execute(select_query, {"id": insert_id})
            row = select_result.fetchone()
            await db.commit()

            # 회사 정보 조회
            company_query = text("""
                SELECT company_name, vector_db_index, vector_db_namespace 
                FROM company_info 
                WHERE company_key = :company_key
            """)
            company_result = await db.execute(company_query, {"company_key": domain_data.company_key})
            company_row = company_result.fetchone()

            # 카테고리 정보 조회
            category_info = {}
            if domain_data.post_category_id:
                category_query = text("""
                    SELECT name, depth, parent_id 
                    FROM post_category 
                    WHERE id = :category_id
                """)
                category_result = await db.execute(category_query, {"category_id": domain_data.post_category_id})
                category_row = category_result.fetchone()
                if category_row:
                    category_info = {
                        "name": category_row[0],
                        "depth": category_row[1],
                        "parent_id": category_row[2]
                    }

            # 카테고리 depth 1 정보
            category_depth1_info = {}
            if domain_data.category_depth_1_id:
                depth1_query = text("""
                    SELECT name 
                    FROM post_category 
                    WHERE id = :category_id
                """)
                depth1_result = await db.execute(depth1_query, {"category_id": domain_data.category_depth_1_id})
                depth1_row = depth1_result.fetchone()
                if depth1_row:
                    category_depth1_info = {"name": depth1_row[0]}

            # 카테고리 depth 2 정보
            category_depth2_info = {}
            if domain_data.category_depth_2_id:
                depth2_query = text("""
                    SELECT name 
                    FROM post_category 
                    WHERE id = :category_id
                """)
                depth2_result = await db.execute(depth2_query, {"category_id": domain_data.category_depth_2_id})
                depth2_row = depth2_result.fetchone()
                if depth2_row:
                    category_depth2_info = {"name": depth2_row[0]}

            # 결과 딕셔너리 구성
            post_data = dict(row._mapping)

            result_data = {
                **post_data,
                "company_name": company_row[0] if company_row else None,
                "vector_db_index": company_row[1] if company_row else None,
                "vector_db_namespace": company_row[2] if company_row else None,
                "post_category_name": category_info.get("name") if category_info else None,
                "post_category_depth": category_info.get("depth") if category_info else None,
                "post_category_parent_id": category_info.get("parent_id") if category_info else None,
                "category_depth_1_name": category_depth1_info.get("name") if category_depth1_info else None,
                "category_depth_2_name": category_depth2_info.get("name") if category_depth2_info else None
            }
            return result_data

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.post.PostQuery.insert_post] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_post(db:AsyncSession, domain_data: getPostDomain):
        try: # page:int, per_page:int, start_date:datetime, end_date:datetime, category_ids:list, **filters:dict
            where_conditions = ["p.company_key = :company_key"]
            params = {
                "company_key": domain_data.company_key,
                "limit": domain_data.per_page,
                "offset": (domain_data.page - 1) * domain_data.per_page
            }

            # 필터 적용
            if domain_data.title:
                # LIKE 검색 적용
                where_conditions.append(f"p.title LIKE :title")
                params["title"] = f"%{domain_data.title}%"  # % 와일드카드 추가
            if domain_data.author:
                where_conditions.append(f"p.author LIKE :author")
                params["author"] = f"%{domain_data.author}%"
            if domain_data.is_on is not None:
                where_conditions.append(f"p.is_on = :is_on")
                params["is_on"] = domain_data.is_on
            if domain_data.is_show is not None:
                where_conditions.append(f"p.is_show = :is_show")
                params["is_show"] = domain_data.is_show
            # 날짜 조건 추가
            if domain_data.start_date:
                where_conditions.append("p.reg_date >= :start_date")
                params["start_date"] = domain_data.start_date
            if domain_data.end_date:
                where_conditions.append("p.reg_date <= :end_date")
                params["end_date"] = domain_data.end_date
            # 카테고리 조건 추가
            if domain_data.category_ids:
                where_conditions.append("p.post_category_id IN :category_ids")
                params["category_ids"] = tuple(domain_data.category_ids)
            where_conditions.append("(p.is_temp IS NULL OR p.is_temp = 0)")

            # WHERE 절 구성
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # 쿼리 실행
            count_query = text(f"SELECT COUNT(*) FROM post p WHERE {where_clause}")
            count_result = await db.execute(count_query, params)
            count = count_result.scalar()

            if count == 0:
                return [], 0

            query = """
                SELECT
                    p.id AS id,
                    p.title AS title,
                    p.reg_date AS reg_date,
                    p.update_date AS update_date,
                    p.is_on AS is_on,
                    p.lang AS lang,
                    p.source AS source,
                    p.use_count AS use_count,
                    p.author AS author,
                    p.post_category_id AS post_category_id,
                    pc.name AS post_category_name,
                    pc.depth AS post_category_depth,
                    pc.parent_id AS post_category_parent_id,
                    pc1.id AS category_depth_1_id,
                    pc1.name AS category_depth_1_name,
                    pc2.id AS category_depth_2_id,
                    pc2.name AS category_depth_2_name
                FROM post p
                LEFT JOIN post_category pc ON p.post_category_id = pc.id
                LEFT JOIN post_category pc1 ON p.category_depth_1_id = pc1.id
                LEFT JOIN post_category pc2 ON p.category_depth_2_id = pc2.id
                WHERE """ + where_clause + " ORDER BY p.update_date DESC LIMIT :limit OFFSET :offset"
            query_text = text(query)
            result = await db.execute(query_text, params)
            rows = result.fetchall()
            posts = [{
                "id": row.id,
                "title": row.title,
                "reg_date": row.reg_date,
                "update_date": row.update_date,
                "is_on": row.is_on,
                "lang": row.lang,
                "source": row.source,
                "use_count": row.use_count,
                "author": row.author,
                "post_category_id": row.post_category_id,
                "post_category_name": row.post_category_name,
                "post_category_depth": row.post_category_depth,
                "category_depth_1_id": row.category_depth_1_id,
                "category_depth_1_name": row.category_depth_1_name,
                "category_depth_2_id": row.category_depth_2_id,
                "category_depth_2_name": row.category_depth_2_name
            } for row in rows]
            return posts, count

        except Exception as e:
            logging.error(f"[queries.post.PostQuery.get_post] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_post_temporary(db:AsyncSession, domain_data:insertPostTemporaryDomain | getPostTemporaryDomain):
        try:
            query_parts = ["""
                SELECT 
                    p.id, p.company_key, p.post_category_id, p.title, p.content, 
                    p.image_url, p.reg_date, p.update_date, p.content_admin, 
                    p.is_show, p.is_on, p.lang, p.source, p.use_count, p.author,
                    p.category_depth_1_id, p.category_depth_2_id, p.is_temp, p.is_update,
                    ci.company_name, ci.vector_db_index, ci.vector_db_namespace,
                    pc.name AS post_category_name, pc.depth AS post_category_depth, pc.parent_id AS post_category_parent_id,
                    pc1.name AS category_depth_1_name,
                    pc2.name AS category_depth_2_name
                FROM post p
                JOIN company_info ci ON p.company_key = ci.company_key
                LEFT JOIN post_category pc ON p.post_category_id = pc.id
                LEFT JOIN post_category pc1 ON p.category_depth_1_id = pc1.id
                LEFT JOIN post_category pc2 ON p.category_depth_2_id = pc2.id
                WHERE 1=1
            """]

            params = {}

            if domain_data.author:
                query_parts.append(" AND p.author = :author")
                params["author"] = domain_data.author

            if domain_data.company_key:
                query_parts.append(" AND p.company_key = :company_key")
                params["company_key"] = domain_data.company_key

            if domain_data.is_temp:
                query_parts.append(" AND p.is_temp = :is_temp")
                params["is_temp"] = domain_data.is_temp

            query_text = "".join(query_parts)
            query_text += " LIMIT 1"

            result = await db.execute(text(query_text), params)
            row = result.fetchone()

            if not row:
                return None

            return {
                "id": row.id,
                "company_key": row.company_key,
                "company_name": row.company_name,
                "vector_db_index": row.vector_db_index,
                "vector_db_namespace": row.vector_db_namespace,
                "post_category_id": row.post_category_id,
                "post_category_name": row.post_category_name,
                "post_category_depth": row.post_category_depth,
                "post_category_parent_id": row.post_category_parent_id,
                "title": row.title,
                "content": row.content,
                "image_url": row.image_url,
                "reg_date": row.reg_date,
                "update_date": row.update_date,
                "content_admin": row.content_admin,
                "is_show": row.is_show,
                "is_on": row.is_on,
                "lang": row.lang,
                "source": row.source,
                "use_count": row.use_count,
                "author": row.author,
                "is_temp": row.is_temp,
                "is_update": row.is_update,
                "category_depth_1_id": row.category_depth_1_id,
                "category_depth_1_name": row.category_depth_1_name,
                "category_depth_2_id": row.category_depth_2_id,
                "category_depth_2_name": row.category_depth_2_name
            }

        except Exception as e:
            logging.error(f"[queries.post.PostQuery.get_post_temporary] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_post_detail(db:AsyncSession, domain_data:getPostDetailDomain):
        try:
            query_parts = ["""
                SELECT 
                    p.id, p.post_category_id, p.title, p.content, 
                    p.image_url, p.reg_date, p.update_date, p.content_admin, 
                    p.is_show, p.is_on, p.lang, p.source, p.use_count, p.author,
                    p.category_depth_1_id, p.category_depth_2_id, p.is_temp, p.is_update,
                    pc.name AS post_category_name, pc.depth AS post_category_depth, pc.parent_id AS post_category_parent_id,
                    pc1.name AS category_depth_1_name,
                    pc2.name AS category_depth_2_name,
                    p.is_markdown,
                    p.sitemap_id
                FROM post p
                JOIN company_info ci ON p.company_key = ci.company_key
                LEFT JOIN post_category pc ON p.post_category_id = pc.id
                LEFT JOIN post_category pc1 ON p.category_depth_1_id = pc1.id
                LEFT JOIN post_category pc2 ON p.category_depth_2_id = pc2.id
                WHERE 1=1
            """]

            params = {}

            if domain_data.id:
                query_parts.append(" AND p.id = :id")
                params["id"] = domain_data.id
            if domain_data.company_key:
                query_parts.append(" AND p.company_key = :company_key")
                params["company_key"] = domain_data.company_key

            # for attr, value in filters.items():
            #     if attr == 'title' or attr == 'author':
            #         query_parts.append(f" AND p.{attr} LIKE :{attr}")
            #         params[attr] = f"%{value}%"
            #     elif attr in ['id', 'company_key', 'post_category_id', 'is_show', 'is_on', 'is_temp', 'is_update', 'lang']:
            #         query_parts.append(f" AND p.{attr} = :{attr}")
            #         params[attr] = value

            query_text = "".join(query_parts)
            query_text += " LIMIT 1"

            result = await db.execute(text(query_text), params)
            row = result.fetchone()

            if not row:
                return None

            return {
                "id": row.id,
                "post_category_id": row.post_category_id,
                "post_category_name": row.post_category_name,
                "post_category_depth": row.post_category_depth,
                "post_category_parent_id": row.post_category_parent_id,
                "title": row.title,
                "content": row.content,
                "image_url": row.image_url,
                "reg_date": row.reg_date,
                "update_date": row.update_date,
                "content_admin": row.content_admin,
                "is_show": row.is_show,
                "is_on": row.is_on,
                "lang": row.lang,
                "source": row.source,
                "use_count": row.use_count,
                "author": row.author,
                "is_temp": row.is_temp,
                "is_update": row.is_update,
                "category_depth_1_id": row.category_depth_1_id,
                "category_depth_1_name": row.category_depth_1_name,
                "category_depth_2_id": row.category_depth_2_id,
                "category_depth_2_name": row.category_depth_2_name,
                "is_markdown": row.is_markdown,
                "sitemap_id": row.sitemap_id
            }

        except Exception as e:
            logging.error(f"[queries.post.PostQuery.get_post_detail] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_post_count(db:AsyncSession, start_date:datetime, end_date:datetime, category_ids:list, **filters):
        try:
            query_parts = ["SELECT COUNT(*) FROM post p WHERE 1=1"]
            params = {}

            for attr, value in filters.items():
                if attr == 'title' or attr == 'author':
                    query_parts.append(f" AND p.{attr} LIKE :{attr}")
                    params[attr] = f"%{value}%"
                elif attr in ['company_key', 'is_show', 'is_on', 'is_temp', 'is_update', 'lang']:
                    query_parts.append(f" AND p.{attr} = :{attr}")
                    params[attr] = value

            if start_date and end_date:
                query_parts.append(" AND p.update_date >= :start_date AND p.update_date <= :end_date")
                params['start_date'] = start_date
                params['end_date'] = end_date
            elif start_date:
                query_parts.append(" AND p.update_date >= :start_date")
                params['start_date'] = start_date
            elif end_date:
                query_parts.append(" AND p.update_date <= :end_date")
                params['end_date'] = end_date

            if category_ids and len(category_ids) > 0:
                query_parts.append(" AND p.post_category_id IN :category_ids")
                params['category_ids'] = tuple(category_ids)

            query_text = "".join(query_parts)
            result = await db.execute(text(query_text), params)
            count = result.scalar()

            return count

        except Exception as e:
            logging.error(f"[queries.post.PostQuery.get_post_count] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_title(db:AsyncSession, data:list):
        try:
            if not data:
                return None

            query = text("""
                SELECT id, title 
                FROM post 
                WHERE id IN :ids
            """)

            result = await db.execute(query, {"ids": tuple(data)})
            rows = result.fetchall()

            return [{"id": row.id, "title": row.title} for row in rows] if rows else None

        except Exception as e:
            logging.error(f"[queries.post.PostQuery.get_title] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_post_by_category_id(db:AsyncSession, domain_data:deleteCategoryDomain):
        try:
            query = text("""
                SELECT 1 
                FROM post 
                WHERE post_category_id = :id OR category_depth_1_id = :id OR category_depth_2_id = :id
                LIMIT 1
            """)

            result = await db.execute(query, {"id": domain_data.id})
            row = result.fetchone()

            return True if row else None

        except Exception as e:
            logging.error(f"[queries.post.PostQuery.get_post_by_category_id] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_sitemap_ids_by_id(db:AsyncSession, domain_data:deletePostDomain):
        try:
            if isinstance(domain_data.id, (tuple, list)):
                query = text("""SELECT sitemap_id FROM post WHERE company_key = :company_key AND id IN :id""")
            else:
                query = text("""SELECT sitemap_id FROM post WHERE company_key = :company_key AND id = :id""")
            params = {"company_key": domain_data.company_key, "id": domain_data.id}
            result = await db.execute(query, params)
            rows = result.fetchall()
            return [row[0] for row in rows] if rows else None

        except Exception as e:
            logging.error(f"[queries.post.PostQuery.get_post_by_category_id] DBError: {e}")
            raise DBError(e)



    @staticmethod
    async def update_post(db:AsyncSession, domain_data: insertPostDomain | insertPostTemporaryDomain | updatePostDomain):
        try:
            id = domain_data.id
            if not id:
                raise ValueError("ID must be provided for update")

            # 업데이트할 컬럼 및 파라미터 구성
            set_conditions = []
            params = {"id": id}

            if domain_data.title:
                set_conditions.append(f"title = :title")
                params["title"] = domain_data.title

            if domain_data.content:
                set_conditions.append(f"content = :content")
                params["content"] = domain_data.content

            if domain_data.image_url:
                set_conditions.append(f"image_url = :image_url")
                params["image_url"] = domain_data.image_url

            if domain_data.post_category_id:
                set_conditions.append(f"post_category_id = :post_category_id")
                params["post_category_id"] = domain_data.post_category_id

            if domain_data.category_depth_1_id:
                set_conditions.append(f"category_depth_1_id = :category_depth_1_id")
                params["category_depth_1_id"] = domain_data.category_depth_1_id

            if domain_data.category_depth_2_id:
                set_conditions.append(f"category_depth_2_id = :category_depth_2_id")
                params["category_depth_2_id"] = domain_data.category_depth_2_id

            if domain_data.reg_date:
                set_conditions.append(f"reg_date = :reg_date")
                params["reg_date"] = domain_data.reg_date

            if domain_data.update_date:
                set_conditions.append(f"update_date = :update_date")
                params["update_date"] = domain_data.update_date

            set_conditions.append(f"is_temp = :is_temp")
            params["is_temp"] = domain_data.is_temp

            set_conditions.append(f"is_on = :is_on")
            params["is_on"] = domain_data.is_on

            if not set_conditions:
                raise ValueError("No update fields provided")

            set_clause = ", ".join(set_conditions)

            # 업데이트 쿼리 실행
            update_query = text(f"""
                UPDATE post
                SET {set_clause}
                WHERE id = :id
            """)

            await db.execute(update_query, params)
            await db.commit()

            # 업데이트된 데이터 조회
            detail_query = text("""
                SELECT 
                    p.id as id,
                    p.company_key as company_key,
                    p.post_category_id as post_category_id,
                    p.title as title,
                    p.content as content, 
                    p.image_url as image_url,
                    p.reg_date as reg_date,
                    p.update_date as update_date,
                    p.content_admin as content_admin, 
                    p.is_show as is_show,
                    p.is_on as is_on,
                    p.lang as lang,
                    p.source as source,
                    p.use_count as use_count,
                    p.author as author,
                    p.category_depth_1_id as category_depth_1_id,
                    p.category_depth_2_id as category_depth_2_id,
                    p.is_temp as is_temp,
                    p.is_update as is_update,
                    ci.company_name as company_name,
                    ci.vector_db_index as vector_db_index,
                    ci.vector_db_namespace as vector_db_namespace,
                    pc.name AS post_category_name, pc.depth AS post_category_depth, pc.parent_id AS post_category_parent_id,
                    pc1.name AS category_depth_1_name,
                    pc2.name AS category_depth_2_name
                FROM post p
                JOIN company_info ci ON p.company_key = ci.company_key
                LEFT JOIN post_category pc ON p.post_category_id = pc.id
                LEFT JOIN post_category pc1 ON p.category_depth_1_id = pc1.id
                LEFT JOIN post_category pc2 ON p.category_depth_2_id = pc2.id
                WHERE p.id = :id
            """)

            result = await db.execute(detail_query, {"id": id})
            row = result.fetchone()

            if not row:
                return None

            return {
                "id": row.id,
                "company_key": row.company_key,
                "company_name": row.company_name,
                "vector_db_index": row.vector_db_index,
                "vector_db_namespace": row.vector_db_namespace,
                "post_category_id": row.post_category_id,
                "post_category_name": row.post_category_name,
                "post_category_depth": row.post_category_depth,
                "post_category_parent_id": row.post_category_parent_id,
                "title": row.title,
                "content": row.content,
                "image_url": row.image_url,
                "reg_date": row.reg_date,
                "update_date": row.update_date,
                "content_admin": row.content_admin,
                "is_show": row.is_show,
                "is_on": row.is_on,
                "lang": row.lang,
                "source": row.source,
                "use_count": row.use_count,
                "author": row.author,
                "is_temp": row.is_temp,
                "is_update": row.is_update,
                "category_depth_1_id": row.category_depth_1_id,
                "category_depth_1_name": row.category_depth_1_name,
                "category_depth_2_id": row.category_depth_2_id,
                "category_depth_2_name": row.category_depth_2_name
            }

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.post.PostQuery.update_post] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_count(db:AsyncSession, id:int):
        try:
            query = text("""
                UPDATE post
                SET use_count = COALESCE(use_count, 0) + 1
                WHERE id = :id
            """)

            await db.execute(query, {"id": id})
            await db.commit()

            return True

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.post.PostQuery.update_count] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def delete_post(db:AsyncSession, domain_data:deletePostDomain):
        try:
            if isinstance(domain_data.id, int):
                query = text("""
                    DELETE FROM post
                    WHERE id = :id AND company_key = :company_key
                """)

                result = await db.execute(query, {"id": domain_data.id, "company_key": domain_data.company_key})
                deleted = result.rowcount > 0

            elif isinstance(domain_data.id, (list, tuple)):
                query = text("""
                    DELETE FROM post
                    WHERE id IN :ids AND company_key = :company_key
                """)

                result = await db.execute(query, {"ids": tuple(domain_data.id), "company_key": domain_data.company_key})
                deleted = result.rowcount > 0

            else:
                return False

            if deleted:
                await db.commit()
                return True

            return False

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.post.PostQuery.delete_post] DBError: {e}")
            raise DBError(e)
