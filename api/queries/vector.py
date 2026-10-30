import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from utils.error import DBError
from domain.reference import *
from domain.drive import *
from domain.email import *



class VectorQuery:
    
    @staticmethod
    async def insert_vector(db:AsyncSession, domain_data:updateFileContentDomain):
        try:
            if not domain_data.vector_metadatas:
                logging.error(f"[queries.vector.VectorQuery.insert_vector] Empty vector_metadatas. {domain_data}")
                return []
            
            data = domain_data.vector_metadatas[0]
            query = text(
                """
				INSERT INTO
					vector
				(
					company_key,
					upload_file_id,
					page,
					data_type,
					is_on,
					is_show
				)
				VALUES
				(
					:company_key,
					:upload_file_id,
					:page,
					:data_type,
					:is_on,
					:is_show
				)
				RETURNING id
				"""
            )
            params = {
                "company_key": data.get("company_key"),
                "upload_file_id": data.get("upload_file_id"),
                "page": data.get("page"),
                "data_type": data.get("data_type"),
                "is_on": data.get("is_on"),
                "is_show": data.get("is_show"),
            }
            result = await db.execute(query, params)
            inserted_id = result.scalar_one()
            data['id'] = inserted_id
            await db.commit()
            return [inserted_id]
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.vector.VectorQuery.insert_vector] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def bulk_insert_vector(db:AsyncSession, domain_data:updateFileContentDomain):
        try:
            if not domain_data.vector_metadatas:
                return []
            
            batch_size = 1000  # 한 번에 처리할 항목 수
            inserted_ids = []
            
            # 데이터를 배치로 나누어 처리
            for i in range(0, len(domain_data.vector_metadatas), batch_size):
                batch = domain_data.vector_metadatas[i:i+batch_size]
                
                # 컬럼 이름 추출
                columns = list(batch[0].keys())
                columns_str = ", ".join(columns)
                
                # 값 플레이스홀더 및 파라미터 구성
                values_placeholders = []
                params = {}
                
                for j, item in enumerate(batch):
                    item_placeholders = []
                    for col in columns:
                        param_name = f"{col}_{j}"
                        item_placeholders.append(f":{param_name}")
                        params[param_name] = item[col]
                    
                    values_placeholders.append(f"({', '.join(item_placeholders)})")
                
                values_clause = ", ".join(values_placeholders)
                
                # INSERT 쿼리 실행
                insert_query = text(f"""
                    INSERT INTO vector ({columns_str})
                    VALUES {values_clause}
                    RETURNING id
                """)
                
                result = await db.execute(insert_query, params)
                batch_ids = [row[0] for row in result]
                inserted_ids.extend(batch_ids)
            
            await db.commit()
            return inserted_ids
        
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.vector.VectorQuery.bulk_insert_vector] DBError: {e}")
            raise DBError(e)
    
    
    @staticmethod
    async def bulk_insert_vector_from_post(db:AsyncSession, domain_data:insertPostDomain | updatePostDomain):
        try:
            if not domain_data.vector_table_datas:
                return []
            
            # 배치 처리를 위한 크기 설정
            batch_size = 1000
            
            # 데이터를 배치로 나누어 처리
            for i in range(0, len(domain_data.vector_table_datas), batch_size):
                batch = domain_data.vector_table_datas[i:i+batch_size]
                
                # 컬럼 이름 추출
                columns = list(batch[0].keys())
                columns_str = ", ".join(columns)
                
                # 값 플레이스홀더 및 파라미터 구성
                values_placeholders = []
                params = {}
                
                for j, item in enumerate(batch):
                    item_placeholders = []
                    for col in columns:
                        param_name = f"{col}"
                        item_placeholders.append(f":{param_name}")
                        params[param_name] = item[col]
                    
                    values_placeholders.append(f"({', '.join(item_placeholders)})")
                
                values_clause = ", ".join(values_placeholders)
                
                # INSERT 쿼리 실행
                insert_query = text(f"""
                    INSERT INTO vector ({columns_str})
                    VALUES {values_clause}
                """)
                await db.execute(insert_query, params)
            
            await db.commit()
            
            # 삽입된 vector 확인을 위한 post_id 수집
            post_ids = list(set([d['post_id'] for d in domain_data.vector_table_datas]))
            
            # post_id로 삽입된 vector 조회
            query = text("""
                SELECT id
                FROM vector
                WHERE post_id IN :ids
            """)
            
            result = await db.execute(query, {"ids": tuple(post_ids)})
            rows = result.fetchall()
            vector_ids = [row.id for row in rows]
            
            return vector_ids
        
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.vector.VectorQuery.bulk_insert_vector_from_post] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def bulk_insert_vector_from_email(db:AsyncSession, domain_data:SendEmailDomain):
        try:
            if not domain_data.vector_table_datas:
                return []

            # 배치 처리를 위한 크기 설정
            batch_size = 1000

            # 데이터를 배치로 나누어 처리
            for i in range(0, len(domain_data.vector_table_datas), batch_size):
                batch = domain_data.vector_table_datas[i:i+batch_size]

                # 컬럼 이름 추출
                columns = list(batch[0].keys())
                columns_str = ", ".join(columns)

                # 값 플레이스홀더 및 파라미터 구성
                values_placeholders = []
                params = {}

                for j, item in enumerate(batch):
                    item_placeholders = []
                    for col in columns:
                        param_name = f"{col}"
                        item_placeholders.append(f":{param_name}")
                        params[param_name] = item[col]

                    values_placeholders.append(f"({', '.join(item_placeholders)})")

                values_clause = ", ".join(values_placeholders)

                # INSERT 쿼리 실행
                insert_query = text(f"""
                    INSERT INTO vector ({columns_str})
                    VALUES {values_clause}
                """)
                await db.execute(insert_query, params)

            await db.commit()

            # 삽입된 vector 확인을 위한 post_id 수집
            email_ids = list(set([d['email_id'] for d in domain_data.vector_table_datas]))

            # post_id로 삽입된 vector 조회
            query = text("""
                SELECT id
                FROM vector
                WHERE email_id IN :ids
            """)

            result = await db.execute(query, {"ids": tuple(email_ids)})
            rows = result.fetchall()
            vector_ids = [row.id for row in rows]

            return vector_ids

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.vector.VectorQuery.bulk_insert_vector_from_post] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_vector_ids_and_metadatas(db:AsyncSession, domain_data:deleteDomain):
        try:
            query = text(
                """
                    SELECT
                        id,
                        company_key,
                        upload_file_id,
                        page,
                        data_type,
                        is_on,
                        is_show,
                        chunk
                    FROM vector
                    WHERE upload_file_id = (SELECT upload_file_id FROM drive WHERE id = :file_id)
                """
            )
            params = {"file_id": domain_data.file_id}
            results = await db.execute(query, params)
            rows = results.fetchall()
            return [
                {
                    "id": row.id,
                    "company_key": row.company_key,
                    "upload_file_id": row.upload_file_id,
                    "page": row.page,
                    "data_type": row.data_type,
                    "is_on": bool(row.is_on),
                    "is_show": bool(row.is_show),
                    "chunk": row.chunk
                } for row in rows] if rows else False
        except Exception as e:
            logging.error(f"[queries.vector.VectorQuery.get_vector_ids_and_metadataßs_by_upload_file_id] DBError: {e}")
            raise DBError(e)



    @staticmethod
    async def get_vector_ids_by_post_id(db:AsyncSession, domain_data:deletePostDomain):
        try:
            if isinstance(domain_data.id, (list, tuple)):
                query = text("""SELECT id FROM vector WHERE post_id IN :post_id""")
            else:
                query = text("""SELECT id FROM vector WHERE post_id = :post_id""")
            params = {"post_id": domain_data.id}
            results = await db.execute(query, params)
            rows = results.fetchall()
            return [row.id for row in rows] if rows else False
        except Exception as e:
            logging.error(f"[queries.vector.VectorQuery.get_vector_ids_by_post_id] DBError: {e}")


    @staticmethod
    async def get_vector_ids_by_upload_file_id(db:AsyncSession, domain_data:deleteFileDomain):
        try:
            if isinstance(domain_data.upload_file_id, (list, tuple)):
                query = text("""SELECT id FROM vector WHERE upload_file_id IN :upload_file_id""")
            else:
                query = text("""SELECT id FROM vector WHERE upload_file_id = :upload_file_id""")
            params = {"upload_file_id": domain_data.upload_file_id}
            results = await db.execute(query, params)
            rows = results.fetchall()
            return [row.id for row in rows] if rows else False
        except Exception as e:
            logging.error(f"[queries.vector.VectorQuery.get_vector_ids_by_upload_file_id] DBError: {e}")


    @staticmethod
    async def get_vector_by_upload_file_id(db:AsyncSession, upload_file_id:int):
        try:
            query = text(
                """
                    SELECT id
                    FROM vector
                    WHERE upload_file_id = :upload_file_id
                """
            )
            params = {"upload_file_id": upload_file_id}
            results = await db.execute(query, params)
            rows = results.fetchall()
            return [row.id for row in rows] if rows else False
        except Exception as e:
            logging.error(f"[queries.vector.VectorQuery.get_vector_by_upload_file_id] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_ids_by_email_send_history_id(db:AsyncSession, domain_data:DeleteSentEmailDomain):
        try:
            if isinstance(domain_data.email_send_history_id, int):
                query = text(
                    """
                        SELECT id
                        FROM llm_platform.vector
                        WHERE email_id = :email_send_history_id
                    """
                )
            else:
                query = text(
                    """
                        SELECT id
                        FROM llm_platform.vector
                        WHERE email_id IN :email_send_history_id
                    """
                )
            params = {"email_send_history_id": domain_data.email_send_history_id}
            results = await db.execute(query, params)
            rows = results.fetchall()
            return [row.id for row in rows] if rows else []
        except Exception as e:
            logging.error(f"[queries.vector.VectorQuery.get_vector_by_upload_file_id] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_vector_ids_and_metadatas_by_email_id(db:AsyncSession, domain_data:DeleteSentEmailDomain):
        try:
            if isinstance(domain_data.email_send_history_id, int):
                query = text(
                    """
                        SELECT
                            id,
                            company_key,
                            page,
                            chunk,
                            data_type,
                            is_on,
                            is_show,
                            email_id
                        FROM llm_platform.vector
                        WHERE email_id = :email_send_history_id
                    """
                )
            else:
                query = text(
                    """
                        SELECT
                            id,
                            company_key,
                            page,
                            chunk,
                            data_type,
                            is_on,
                            is_show,
                            email_id
                        FROM llm_platform.vector
                        WHERE email_id IN :email_send_history_id
                    """
                )
            params = {"email_send_history_id": domain_data.email_send_history_id}
            results = await db.execute(query, params)
            rows = results.fetchall()

            _id = list()
            metadata = list()
            if rows:
                for row in rows:
                    _id.append(row.id)
                    metadata.append(
                        {
                            "id": row.email_id,
                            "is_on": bool(row.is_on),
                            "is_show": bool(row.is_show),
                            "page": row.page,
                            "chunk": row.chunk,
                            "company_key": row.company_key,
                            "data_type": row.company_key
                        }
                    )

            return _id, metadata

        except Exception as e:
            logging.error(f"[queries.vector.VectorQuery.get_vector_by_upload_file_id] DBError: {e}")
            raise DBError(e)


    
    @staticmethod
    async def get_vector_row_count(db:AsyncSession, domain_data:updatePostDomain):
        try:
            query = text(
                """
                    SELECT id, post_id, page, chunk, data_type, is_on, is_show
                    FROM vector
                    WHERE company_key = :company_key
                        AND post_id = :post_id
                """
            )
            params = {"company_key": domain_data.company_key, "post_id": domain_data.id}
            results = await db.execute(query, params)
            return [
                {
                    "id": result.id,
                    "post_id": result.post_id,
                    "page": result.page,
                    "chunk": result.chunk,
                    "data_type": result.data_type,
                    "is_on": result.is_on,
                    "is_show": result.is_show
                } for result in results.fetchall()] if results else []
        except Exception as e:
            logging.error(f"[queries.vector.VectorQuery.get_vector_row_count] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_all_page(db:AsyncSession, domain_data:fileViewDomain):
        try: # upload_file_id:int
            query = text(
                """
                    SELECT page FROM vector WHERE upload_file_id = :upload_file_id;
                """
            )
            params = {"upload_file_id": domain_data.row["upload_file_id"]}
            result = await db.execute(query, params)
            rows = result.fetchall()
            return [row[0] for row in rows] if rows else []
        except Exception as e:
            logging.error(f"[queries.vector.VectorQuery.get_all_page] DBError: {e}")
            raise DBError(e)
        
    
    @staticmethod
    async def update_is_on_of_vector_table(db:AsyncSession, domain_data:deleteDomain):
        try:
            query = text(
                """
                    UPDATE vector
                    SET is_on = :is_on, is_show = :is_show
                    WHERE upload_file_id = (SELECT upload_file_id FROM drive WHERE id = :file_id)
                """
            )
            params = {"is_on": False, "is_show": False, "file_id": domain_data.file_id}
            await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.vector.VectorQuery.update_is_on_of_vector_table] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def update_is_on_of_vector_table_by_email_id(db:AsyncSession, domain_data:DeleteSentEmailDomain):
        try:
            if isinstance(domain_data.email_send_history_id, int):
                query = text(
                    """
                        UPDATE vector
                        SET is_on = :is_on, is_show = :is_show
                        WHERE email_id = :email_send_history_id
                    """
                )
            else:
                query = text(
                    """
                        UPDATE vector
                        SET is_on = :is_on, is_show = :is_show
                        WHERE email_id IN :email_send_history_id
                    """
                )
            params = {"is_on": False, "is_show": False, "email_send_history_id": domain_data.email_send_history_id}
            await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.vector.VectorQuery.update_is_on_of_vector_table] DBError: {e}")
            raise DBError(e)

    
    @staticmethod
    async def delete_vector_by_ids(db:AsyncSession, ids:list[int]):
        try:
            # 빈 리스트 체크
            if not ids:
                logging.warning("[queries.vector.VectorQuery.delete_vector_by_ids] Empty ids list provided")
                return
                
            query = text("""DELETE FROM vector WHERE id IN :ids""")
            params = {"ids": tuple(ids)}
            await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.vector.VectorQuery.delete_vector_by_ids] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def delete_vector_by_upload_file_id(db:AsyncSession, company_key:str, upload_file_id:int):
        try:
            query = text(
                """
                    DELETE FROM vector
                    WHERE company_key = :company_key
                        AND upload_file_id = :upload_file_id
                """
            )
            params = {"company_key": company_key, "upload_file_id": upload_file_id}
            await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.vector.VectorQuery.delete_vector_by_upload_file_id] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def delete_vector_by_post_id(db:AsyncSession, domain_data:updatePostDomain | deletePostDomain):
        try:
            if isinstance(domain_data.id, int):
                query = text(
                    """
                        DELETE FROM vector
                        WHERE company_key = :company_key
                            AND post_id = :post_id
                    """
                )
            else: 
                query = text(
                    """
                        DELETE FROM vector
                        WHERE company_key = :company_key
                            AND post_id IN :post_id
                    """
                )
            params = {"company_key": domain_data.company_key, "post_id": domain_data.id}
            await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.vector.VectorQuery.delete_vector_by_post_id] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def delete_vector_by_email_send_history_id(db:AsyncSession, domain_data:DeleteSentEmailDomain):
        try:
            if isinstance(domain_data.email_send_history_id, int):
                query = text(
                    """
                        DELETE FROM vector
                        WHERE company_key = :company_key
                            AND email_id = :email_send_history_id
                    """
                )
            else:
                query = text(
                    """
                        DELETE FROM vector
                        WHERE company_key = :company_key
                            AND email_id IN :email_send_history_id
                    """
                )
            params = {"company_key": domain_data.company_key, "email_send_history_id": domain_data.email_send_history_id}
            await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.vector.VectorQuery.delete_vector_by_email_send_history_id] DBError: {e}")
            raise DBError(e)

