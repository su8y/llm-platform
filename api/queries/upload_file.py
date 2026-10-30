import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from domain.reference import insertPostDomain, updatePostDomain
from domain.drive import uploadFileDomain, downloadFileDomain
from utils.error import DBError



class UploadFileQuery:

    @staticmethod
    async def record_upload_file_history_for_parser(db:AsyncSession, data:dict):
        try:
            query = text("""
                INSERT INTO upload_file (s3_path, reg_date)
                VALUES (:s3_path, :reg_date)
                RETURNING id
            """)
            params = {
                "s3_path": data.get("s3_path"),
                "reg_date": data.get("reg_date"),
            }
            result = await db.execute(query, params)
            insert_id = result.scalar_one()
            await db.commit()
            return insert_id
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.upload_file.UploadFileQuery.record_upload_file_history_for_parser] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def bulk_record_upload_file_history_for_parser(db:AsyncSession, datas:list):
        try:
            ids = []
            async with db.begin_nested():
                for data in datas:
                    query = text("""
                        INSERT INTO upload_file (s3_path, reg_date)
                        VALUES (:s3_path, :reg_date)
                        RETURNING id
                    """)
                    params = {
                        "s3_path": data["s3_path"],
                        "reg_date": data["reg_date"]
                    }
                    result = await db.execute(query, params)
                    ids.append(result.scalar_one())
            await db.commit()
            return ids
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.upload_file.UploadFileQuery.bulk_record_upload_file_history_for_parser] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def record_upload_file_history_for_filesearch(db:AsyncSession, domain_data:uploadFileDomain | insertPostDomain | updatePostDomain):
        try:
            s3_path = f"{domain_data.filesearch_payload['buckets'][0]}:{domain_data.filesearch_payload['keys'][0]}"
            document_name = domain_data.filesearch_response["documentName"][0]

            query = text("""
                INSERT INTO upload_file (s3_path, reg_date, drive_id, post_id, document_name)
                VALUES (:s3_path, :reg_date, :drive_id, :post_id, :document_name)
                RETURNING id
            """)
            params = {
                "s3_path": s3_path,
                "reg_date": domain_data.reg_date,
                "document_name": document_name
            }
            if isinstance(domain_data, uploadFileDomain):
                params["drive_id"] = domain_data.drive_ids[0]
                params["post_id"] = None
            else:
                params["drive_id"] = None
                params["post_id"] = domain_data.id

            result = await db.execute(query, params)
            insert_id = result.scalar_one()
            await db.commit()

            return insert_id

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.upload_file.UploadFileQuery.record_upload_file_history_for_parser] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def bulk_record_upload_file_history_for_filesearch(db:AsyncSession, domain_data:uploadFileDomain):
        try:
            ids = []

            zip_iter = zip(
                domain_data.drive_ids,
                domain_data.filesearch_payload['buckets'],
                domain_data.filesearch_payload['keys'],
                domain_data.filesearch_response['documentName']
            )

            async with db.begin_nested():
                for drive_id, bucket, key, document_name in zip_iter:
                    s3_path = f"{bucket}:{key}"
                    query = text("""
                        INSERT INTO upload_file (s3_path, reg_date, drive_id, document_name)
                        VALUES (:s3_path, :reg_date, :drive_id, :document_name)
                    """)
                    params = {
                        "s3_path": s3_path,
                        "reg_date": domain_data.reg_date,
                        "drive_id": drive_id,
                        "document_name": document_name
                    }
                    result = await db.execute(query, params)
                    insert_id = result.scalar_one()
                    ids.append(insert_id)

            await db.commit()
            return ids

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.upload_file.UploadFileQuery.bulk_record_upload_file_history_for_parser] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def record_upload_file_history(db:AsyncSession, datas:list):
        try:
            for data in datas:
                columns = list(data.keys())
                columns_str = ", ".join(columns)
                placeholders = ", ".join([f":{col}" for col in columns])

                query = text(f"""
                    INSERT INTO upload_file ({columns_str})
                    VALUES ({placeholders})
                """)
                await db.execute(query, data)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.upload_file.UploadFileQuery.record_upload_file_history] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_s3_filename_by_file_id(db:AsyncSession, id:int):
        try:
            query = text("""
                SELECT filename
                FROM upload_file
                WHERE id = :id
            """)
            params = {"id": id}
            result = await db.execute(query, params)
            row = result.fetchone()

            return row.filename if row else None
        except Exception as e:
            logging.error(f"[queries.upload_file.UploadFileQuery.get_s3_filename_by_file_id] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_s3_filenames_by_post_id(db:AsyncSession, post_id):
        try:
            if isinstance(post_id, (list, tuple)):
                query = text("""
                    SELECT id, filename
                    FROM upload_file
                    WHERE post_id IN :post_id
                """)
                params = {"post_id": tuple(post_id)}
            else:
                query = text("""
                    SELECT id, filename
                    FROM upload_file
                    WHERE post_id = :post_id
                """)
                params = {"post_id": post_id}

            result = await db.execute(query, params)
            rows = result.fetchall()

            return [{"id": row.id, "name": row.filename} for row in rows] if rows else None
        except Exception as e:
            logging.error(f"[queries.upload_file.UploadFileQuery.get_s3_filenames_by_post_id] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_s3_path_by_post_id(db:AsyncSession, post_id:int):
        try:
            query = text("""
                SELECT id, s3_path
                FROM upload_file
                WHERE post_id = :post_id
            """)
            params = {"post_id": post_id}
            result = await db.execute(query, params)
            rows = result.fetchall()

            return [{"id": row.id, "s3_path": row.s3_path} for row in rows] if rows else None
        except Exception as e:
            logging.error(f"[queries.upload_file.UploadFileQuery.get_s3_path_by_post_id] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_s3_path_by_drive_id(db:AsyncSession, domain_data:downloadFileDomain):
        try:
            query = text("""
                SELECT
                    up.s3_path
                FROM
                    upload_file up
                INNER JOIN
                    drive d ON d.upload_file_id = up.id
                WHERE
                    d.id = :drive_id
            """)
            params = {"drive_id": domain_data.drive_id}
            result = await db.execute(query, params)
            row = result.fetchone()

            return {"s3_path": row[0]} if row else None
        except Exception as e:
            logging.error(f"[queries.upload_file.UploadFileQuery.get_s3_path_by_drive_id] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_row_by_drive_id(db:AsyncSession, drive_id:int):
        try:
            query = text("""
                SELECT
                    up.id,
                    up.s3_path,
                    up.reg_date
                FROM
                    upload_file up
                INNER JOIN
                    drive d ON d.upload_file_id = up.id
                WHERE
                    d.id = :drive_id
            """)
            params = {"drive_id": drive_id}
            result = await db.execute(query, params)
            row = result.fetchone()

            return {
                "id": row[0],
                "s3_path": row[1],
                "reg_date": row[2]
            } if row else None
        except Exception as e:
            logging.error(f"[queries.upload_file.UploadFileQuery.get_row_by_drive_id] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_rows_by_drive_ids(db:AsyncSession, drive_ids:list):
        try:
            query = text("""
                SELECT
                    up.id,
                    up.s3_path,
                    up.reg_date
                FROM
                    upload_file up
                INNER JOIN
                    drive d ON d.upload_file_id = up.id
                WHERE
                    d.id IN :drive_ids
            """)
            params = {"drive_ids": tuple(drive_ids)}
            result = await db.execute(query, params)
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "s3_path": row[1],
                    "reg_date": row[2]
                } for row in rows
            ] if rows else None

        except Exception as e:
            logging.error(f"[queries.upload_file.UploadFileQuery.get_rows_by_drive_ids] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def delete_upload_file_histories_by_post_id(db:AsyncSession, post_id):
        try:
            if isinstance(post_id, (list, tuple)):
                query = text("""
                    DELETE FROM upload_file
                    WHERE post_id IN :post_id
                """)
                params = {"post_id": tuple(post_id)}
            else:
                query = text("""
                    DELETE FROM upload_file
                    WHERE post_id = :post_id
                """)
                params = {"post_id": post_id}

            result = await db.execute(query, params)
            deleted = result.rowcount > 0

            if deleted:
                await db.commit()
                return True
            else:
                return None
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.upload_file.UploadFileQuery.delete_upload_file_histories_by_post_id] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_filesearch_document_name_by_post_id(db:AsyncSession, domain_data:updatePostDomain):
        try:
            query = text(
                """
                    SELECT
                        document_name
                    FROM upload_file
                    WHERE post_id = :post_id
                """
            )
            params = {
                "post_id": domain_data.id,
            }
            result = await db.execute(query, params)
            row = result.fetchone()

            return row.document_name if row else None

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.upload_file.UploadFileQuery.get_filesearch_document_name_by_post_id] DBError: {e}")
            raise DBError()

    @staticmethod
    async def delete_upload_file_history(db:AsyncSession, id:int):
        try:
            query = text("""
                DELETE FROM upload_file
                WHERE id = :id
            """)
            params = {"id": id}
            result = await db.execute(query, params)
            deleted = result.rowcount > 0

            if deleted:
                await db.commit()
                return True
            else:
                return None
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.upload_file.UploadFileQuery.delete_upload_file_history] DBError: {e}")
            raise DBError(e)
