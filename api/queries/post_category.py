import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from utils.error import DBError
from domain.reference import *



class PostCategoryQuery:
    @staticmethod
    async def insert_category(db:AsyncSession, domain_data:insertCategoryDomain | updateCategoryDomain):
        """
        data = {
            "company_key":str,
            "name":str,
            "parent_id":str,
            "depth":str,
            "order":str,
            "is_show":bool,
            "is_on":bool,
            "lang":str
        }
        """
        try:
            query = text("""
                INSERT INTO post_category (company_key, name, parent_id, depth, `order`, is_show, is_on, lang)
                VALUES (:company_key, :name, :parent_id, :depth, :order, :is_show, :is_on, :lang)
            """)
            params = {
                "company_key": domain_data.company_key,
                "name": domain_data.name,
                "parent_id": domain_data.parent_id,
                "depth": domain_data.depth,
                "order": domain_data.order,
                "is_show": domain_data.is_show,
                "is_on": domain_data.is_on,
                "lang": domain_data.lang
            }
            result = await db.execute(query, params)
            insert_id = result.lastrowid
            await db.commit()
            # 삽입된 데이터 조회 (필요한 경우)
            select_query = text("""
                SELECT id, company_key, name, parent_id, depth, `order`, is_show, is_on, lang, reg_date, update_date
                FROM post_category 
                WHERE id = :id
            """)
            select_result = await db.execute(select_query, {"id": insert_id})
            insert_row = select_result.fetchone()
            return {
                "id": insert_row[0],
                "company_key": insert_row[1],
                "name": insert_row[2],
                "parent_id": insert_row[3],
                "depth": insert_row[4],
                "order": insert_row[5],
                "is_show": insert_row[6],
                "is_on": insert_row[7],
                "lang": insert_row[8],
                "reg_date": insert_row[9],
                "update_date": insert_row[10]
            }
            
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.post_category.PostCategoryQuery.insert_category] DBError: {e}")
            raise DBError(e)

    
    @staticmethod
    async def insert_categories(db:AsyncSession, domain_data:updateCategoryDomain):
        try:
            async with db.begin_nested():
                for data in domain_data.insert_list:
                    query = text("""
                        INSERT INTO post_category (company_key, name, parent_id, depth, `order`, is_show, is_on, lang)
                        VALUES (:company_key, :name, :parent_id, :depth, :order, :is_show, :is_on, :lang)
                    """)
                    await db.execute(query, data)
            
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.post_category.PostCategoryQuery.insert_categories] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_categories(db:AsyncSession, domain_data:getPostDetailDomain | getPostTemporaryDomain | getAllCategoriesDomain):
        try:
            query_text = """
                SELECT id, company_key, name, parent_id, depth, "order", is_show, is_on, lang, reg_date
                FROM post_category
                WHERE company_key = :company_key
            """
            
            params = {"company_key": domain_data.company_key}
            
            # if domain_data.lang:
            #     query_text += " AND lang = :lang"
            #     params["lang"] = domain_data.lang
                
            query = text(query_text)
            result = await db.execute(query, params)
            rows = result.fetchall()
            
            return [
                {
                    "id": row[0],
                    "company_key": row[1],
                    "name": row[2],
                    "parent_id": row[3],
                    "depth": row[4],
                    "order": row[5],
                    "is_show": row[6],
                    "is_on": row[7],
                    "lang": row[8],
                    "reg_date": row[9]
                } for row in rows
            ] if rows else None
        except Exception as e:
            logging.error(f"[queries.post_category.PostCategoryQuery.get_categories] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_categories_for_search(db:AsyncSession, id:int):
        try:
            # 먼저 대상 카테고리의 정보 조회
            info_query = text("""
                SELECT id, parent_id, depth
                FROM post_category
                WHERE id = :id
            """)
            result = await db.execute(info_query, {"id": id})
            category = result.fetchone()

            if not category:
                return None
                
            if category[2] == 3:  # depth = 3인 경우
                return [id]
            elif category[2] == 2:  # depth = 2인 경우
                children_query = text("""
                    SELECT id
                    FROM post_category
                    WHERE parent_id = :parent_id
                """)
                children_result = await db.execute(children_query, {"parent_id": id})
                children_rows = children_result.fetchall()
                children_ids = [row[0] for row in children_rows]
                return [id] + children_ids
            elif category[2] == 1:  # depth = 1인 경우
                # 자식 카테고리(depth=2) 조회
                children_query = text("""
                    SELECT id
                    FROM post_category
                    WHERE parent_id = :parent_id
                """)
                children_result = await db.execute(children_query, {"parent_id": id})
                children_rows = children_result.fetchall()
                children_ids = [row[0] for row in children_rows]
                
                # 각 자식 카테고리의 자식들(depth=3) 조회
                grand_children_ids = []
                for child_id in children_ids:
                    grand_children_query = text("""
                        SELECT id
                        FROM post_category
                        WHERE parent_id = :parent_id
                    """)
                    grand_children_result = await db.execute(grand_children_query, {"parent_id": child_id})
                    grand_children_rows = grand_children_result.fetchall()
                    grand_children_ids.extend([row[0] for row in grand_children_rows])
                
                return [id] + children_ids + grand_children_ids

        except Exception as e:
            logging.error(f"[queries.post_category.PostCategoryQuery.get_categories_for_search] DBError: {e}")
            raise DBError(e)
        
    
    @staticmethod
    async def get_categories_for_search_by_subquery(db:AsyncSession, id:int):
        try:
            # 먼저 현재 카테고리의 depth 확인
            depth_query = text("""
                SELECT depth
                FROM post_category
                WHERE id = :id
            """)
            depth_result = await db.execute(depth_query, {"id": id})
            current_depth = depth_result.scalar()
            
            if not current_depth:
                return None
                
            if current_depth == 3:
                return [id]
                
            # depth에 따른 재귀 깊이 제한
            max_depth = current_depth + (3 - current_depth)
            
            recursive_query = text("""
                WITH RECURSIVE category_tree AS (
                    -- 초기 쿼리 (시작점)
                    SELECT id, parent_id, depth, 1 as level
                    FROM post_category
                    WHERE id = :id
                    
                    UNION ALL
                    
                    -- 재귀 부분
                    SELECT c.id, c.parent_id, c.depth, ct.level + 1
                    FROM post_category c
                    INNER JOIN category_tree ct ON c.parent_id = ct.id
                    WHERE c.depth <= :max_depth
                )
                SELECT id FROM category_tree
            """)
            
            result = await db.execute(recursive_query, {'id': id, 'max_depth': max_depth})
            rows = result.fetchall()
            category_ids = [row[0] for row in rows]
            
            return category_ids if category_ids else None
            
        except Exception as e:
            logging.error(f"[queries.post_category.PostCategoryQuery.get_categories_for_search_by_subquery] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def update_categories(db:AsyncSession, domain_data:updateCategoryDomain):
        try:
            async with db.begin_nested():
                for update_id, update_data in zip(domain_data.update_id_list, domain_data.update_data_list):
                    # 동적으로 SET 절 구성
                    set_clauses = []
                    params = {"id": update_id, "company_key": domain_data.company_key}
                    
                    for key, value in update_data.items():
                        if key != "order":
                            set_clauses.append(f"{key} = :{key}")
                            params[key] = value
                        else:
                            set_clauses.append(f"`order` = :order")
                            params[key] = value
                        
                    set_clause = ", ".join(set_clauses)
                    
                    query = text(f"""
                        UPDATE post_category
                        SET {set_clause}
                        WHERE id = :id AND company_key = :company_key
                    """)
                    
                    await db.execute(query, params)
            
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.post_category.PostCategoryQuery.update_categories] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def delete_category(db:AsyncSession, domain_data:deleteCategoryDomain):
        try:
            # 먼저 삭제할 카테고리 정보 조회
            info_query = text("""
                SELECT id, company_key, name, parent_id, depth, "order", is_show, is_on, lang
                FROM post_category
                WHERE id = :id AND company_key = :company_key
            """)
            
            result = await db.execute(info_query, {"id": domain_data.id, "company_key": domain_data.company_key})
            category = result.fetchone()
            
            if not category:
                return None
                
            # 카테고리 정보를 딕셔너리로 변환
            serialized_category = {
                "id": category[0],
                "company_key": category[1],
                "name": category[2],
                "parent_id": category[3],
                "depth": category[4],
                "order": category[5],
                "is_show": category[6],
                "is_on": category[7],
                "lang": category[8]
            }
            
            # 카테고리 삭제
            delete_query = text("""
                DELETE FROM post_category
                WHERE id = :id AND company_key = :company_key
            """)
            
            await db.execute(delete_query, {"id": domain_data.id, "company_key": domain_data.company_key})
            await db.commit()
            
            return serialized_category
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.post_category.PostCategoryQuery.delete_category] DBError: {e}")
            raise DBError(e)
