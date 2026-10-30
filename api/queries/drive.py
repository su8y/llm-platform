import logging
import unicodedata
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from domain.drive import *
from utils.error import DBError, DataError
from utils.constants import *



class DriveQuery:

    @staticmethod
    async def insert_drive_row(db:AsyncSession, domain_data:uploadFileDomain):
        try:
            query = text(
                """
                    INSERT INTO
                        drive (company_key, filename, filetype, filesize, drive_path_id, upload_user_id, is_on, is_show, status, reg_date, update_date, unit_count)
                    VALUES
                        (:company_key, :filename, :filetype, :filesize, :drive_path_id, :upload_user_id, :is_on, :is_show, :status, :reg_date, :update_date, :unit_count)
                    RETURNING
                        id
                """
            )
            params_data = domain_data.file_data[0]
            params = {
                "company_key": params_data["company_key"],
                "filename": params_data["filename"],
                "filetype": params_data["filetype"],
                "filesize": params_data["filesize"],
                "drive_path_id": params_data["drive_path_id"],
                "upload_user_id": params_data["upload_user_id"],
                "is_on": params_data["is_on"],
                "is_show": params_data["is_show"],
                "status": params_data["status"],
                "reg_date": params_data["reg_date"],
                "update_date": params_data["update_date"],
                "unit_count": params_data["unit_count"]
            }
            result = await db.execute(query, params)
            insert_id = result.scalar_one()
            await db.commit()
            return [insert_id]
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.insert_drive_row] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def bulk_insert_drive_row(db:AsyncSession, domain_data:uploadFileDomain):
        try: # insert_datas:tuple
            query = text(
                """INSERT INTO
                        drive (company_key, filename, filetype, filesize, reg_date, update_date, upload_user_id, drive_path_id, is_on, is_show, status, unit_count)
                    VALUES
                        (:company_key, :filename, :filetype, :filesize, :reg_date, :update_date, :upload_user_id, :drive_path_id, :is_on, :is_show, :status, :unit_count);
                    SELECT LAST_INSERT_ID() as id;
                """
            )
            inserted_ids = []
            async with db.begin_nested():
                for insert_data in domain_data.file_data:
                    params = {
                        "company_key": insert_data["company_key"],
                        "filename": insert_data["filename"],
                        "filetype": insert_data["filetype"],
                        "filesize": insert_data["filesize"],
                        "upload_user_id": insert_data["upload_user_id"],
                        "drive_path_id": insert_data["drive_path_id"],
                        "reg_date": insert_data["reg_date"],
                        "update_date": insert_data["update_date"],
                        "is_on": insert_data["is_on"],
                        "is_show": insert_data["is_show"],
                        "status": insert_data["status"],
                        "unit_count": insert_data["unit_count"]
                    }
                    result = await db.execute(query, params)
                    inserted_id = result.scalar_one()
                    inserted_ids.append(inserted_id)
            await db.commit()
            return inserted_ids
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.bulk_insert_drive_row] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_files_in_directory(db:AsyncSession, company_key:str, drive_path_id:int): # directory는 drive_path에서 parent_id가 drive_path_id인 것들을 가져오면 된다. 여긴 only File
        try:
            query = text(
                """
                    SELECT
                        id, filename, filetype, status
                    FROM drive
                    WHERE company_key = :company_key
                        AND drive_path_id = :drive_path_id
                        AND status != :status
                        status != :status
                    ORDER BY update_date DESC
                """
            )
            params = {"company_key": company_key, "drive_path_id": drive_path_id, "status": 0}
            result = await db.execute(query, params)
            rows = result.fetchall()
            return [{
                "fileId": row[0],
                "fileName": row[1],
                "fileType": row[2],
                "status": row[3]
            } for row in rows] if rows else []
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.get_files_in_directory] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_files_in_directory_with_pagination(db:AsyncSession, domain_data:getPageDomain):
        try: #company_key:str, drive_path_id:int, page:int, per_page:int, name:str, start_date:str, end_date:str)
            filters = {
                "company_key": domain_data.company_key,
                "drive_path_id": domain_data.current_dir_id,
                "is_deleted": domain_data.is_deleted,
                "is_show": domain_data.is_show
            }
            params = {
                "company_key": domain_data.company_key,
                "drive_path_id": domain_data.current_dir_id,
                "is_deleted": domain_data.is_deleted,
                "is_show": domain_data.is_show,
                "limit": domain_data.per_page,
                "offset": (domain_data.page - 1) * domain_data.per_page
            }
            if domain_data.name:
                search_value = domain_data.name.strip()
                filters["name"] = f"%{search_value}%" if search_value else "%"
            if domain_data.start_date:
                filters["start_date"] = domain_data.start_date
            if domain_data.end_date:
                filters["end_date"] = domain_data.end_date

            where_conditions = []
            for filter_key in filters:
                if filter_key == "start_date":
                    where_conditions.append("update_date >= :start_date")
                    params["start_date"] = filters[filter_key]
                elif filter_key == "end_date":
                    where_conditions.append("update_date <= :end_date")
                    params["end_date"] = filters[filter_key]
                elif filter_key == "name":
                    where_conditions.append("(filename LIKE :filename_nfc or filename LIKE :filename_nfd)")
                    filename_nfc = unicodedata.normalize('NFC', filters[filter_key])
                    filename_nfd = unicodedata.normalize('NFD', filters[filter_key])
                    params["filename_nfc"] = filename_nfc
                    params["filename_nfd"] = filename_nfd
                else:
                    where_conditions.append(f"{filter_key} = :{filter_key}")
                    params[filter_key] = filters[filter_key]

            # 전체 개수를 가져오는 쿼리
            count_query = text("""
                SELECT 
                    COUNT(*) as total
                FROM drive
                WHERE
            """ + " AND ".join(where_conditions)
            )

            # 페이지네이션된 데이터를 가져오는 쿼리
            data_query = text("""
                SELECT
                    id, filename, filetype, filesize, update_date, status, reg_date
                FROM drive
                WHERE
            """ + " AND ".join(where_conditions) + " ORDER BY reg_date DESC LIMIT :limit OFFSET :offset"
            )

            # 전체 개수 조회
            total_count_result = await db.execute(count_query, params)
            total_count = total_count_result.scalar()

            # 데이터 조회
            result = await db.execute(data_query, params)
            rows = result.fetchall()

            # 결과 포맷팅: TODO: status 조건문을 reform에 달면 굳이 for loop를 한번 더 돌려야함. 가독성과 유지보수 생각하면 reform이 맞으나, 성능 생각하면 여기서 돌리는게 맞음. 고민해볼 것!
            files = [{
                "fileId": row[0],
                "fileName": row[1],
                "fileType": row[2],
                "fileSize": row[3],
                "updateDate": row[4],
                "status": row[5] if row[5] in [1, 2, 3] else 0 if row[5] == 0 else 5 if row[5] in [FAIL_TO_DB, FAIL_TO_SEND_MESSAGE, PARSER_FAILED, PARSER_FAILED_NOT_SAME_COUNT, PARSER_FAILED_UPDATE_TO_VECTOR_DB, PARSER_PARTIAL_ERROR] else 4,
                "regDate": row[6]
            } for row in rows]

            return {"count": total_count, "file": files}

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.get_files_in_directory_with_pagination] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def search(db:AsyncSession, domain_data:searchDomain):
        try:
            where_conditions = []
            params = {}
            if domain_data.company_key:
                where_conditions.append("company_key = :company_key")
                params["company_key"] = domain_data.company_key

            if domain_data.start_date:
                where_conditions.append("update_date >= :start_date")
                params["start_date"] = domain_data.start_date
            if domain_data.end_date:
                where_conditions.append("update_date <= :end_date")
                params["end_date"] = domain_data.end_date

            if domain_data.name:
                where_conditions.append("(filename LIKE :filename or filename_nfc LIKE :filename_nfd)")
                search_value = domain_data.name.strip()
                filename_nfc = unicodedata.normalize('NFC', search_value)
                filename_nfd = unicodedata.normalize('NFD', search_value)
                params["filename_nfc"] = f"%{filename_nfc}%"
                params["filename_nfd"] = f"%{filename_nfd}%"
            if domain_data.filetype:
                where_conditions.append("filetype LIKE :filetype")
                params["filetype"] = f"%{domain_data.filetype}%"
            if domain_data.is_on:
                where_conditions.append("is_on = :is_on")
                params["is_on"] = domain_data.is_on
            if domain_data.is_show:
                where_conditions.append("is_show = :is_show")
                params["is_show"] = domain_data.is_show

            if domain_data.page and domain_data.per_page:
                params["offset"] = (domain_data.page - 1) * domain_data.per_page
                params["per_page"] = domain_data.per_page

            where_conditions.append("status != :status")
            params["status"] = 0  # 삭제된 파일 제외 (get_files_in_directory 와 동일)
            where_clause = " AND ".join(where_conditions)

            count_query = text(
                """
                    SELECT COUNT(*)
                    FROM drive
                    WHERE
                """ + where_clause
            )
            total_count_result = await db.execute(count_query, params)
            total_count = total_count_result.scalar()

            query = text(
                """
                    SELECT
                        id, filename, filetype, filesize, update_date, status
                    FROM drive
                    WHERE
                """ + where_clause + " ORDER BY update_date DESC LIMIT :per_page OFFSET :offset"
            )
            result = await db.execute(query, params)
            rows = result.fetchall()
            return {
                "count": total_count,
                "files": [
                    {
                        "fileId": row[0],
                        "fileName": row[1],
                        "fileType": row[2],
                        "fileSize": row[3],
                        "updateDate": row[4],
                        "status": row[5]
                    } for row in rows
                ] if rows else []
            }
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.search] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_file_by_id(db:AsyncSession, domain_data:fileViewDomain|GetStatusDomain|getFileInfoDomain):
        try:
            query = text(
                """
                    SELECT
                        d.id,
                        d.filename,
                        d.filetype,
                        d.filesize,
                        d.thumnail_s3_path,
                        d.unit_count,
                        d.reg_date,
                        d.update_date,
                        d.upload_user_id,
                        d.status,
                        COALESCE(uf.s3_path, NULL) as s3_path,
                        COALESCE(uf.id, NULL) as upload_file_id
                    FROM drive d
                    LEFT JOIN upload_file uf
                        ON d.upload_file_id = uf.id
                    WHERE company_key = :company_key
                        AND d.id = :file_id
                """
            )
            params = {"company_key": domain_data.company_key, "file_id": domain_data.file_id}
            result = await db.execute(query, params)
            row = result.fetchone()
            if row is None:
                raise DataError(f"File not found: {domain_data.file_id}")
            return {
                "id": row[0],
                "filename": row[1],
                "filetype": row[2],
                "filesize": row[3],
                "thumnail_s3_path": row[4],
                "unit_count": row[5],
                "reg_date": row[6],
                "update_date": row[7],
                "upload_user_id": row[8],
                "status": row[9],
                "s3_path": row[10],
                "upload_file_id": row[11]
            }
        except DataError:
            raise
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.get_file_by_id] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_filename_and_id(db:AsyncSession, domain_data:GetFilenamesDomain):
        try:
            params = {"company_key": domain_data.company_key}
            if domain_data.page and domain_data.per_page:
                params["offset"] = (domain_data.page - 1) * domain_data.per_page
                params["per_page"] = domain_data.per_page

            query = text(
                """
                    SELECT
                        filename,
                        upload_file_id
                    FROM drive
                    WHERE company_key = :company_key
                        AND upload_file_id is not null
                    ORDER BY update_date DESC
                    LIMIT :per_page OFFSET :offset
                """
            )
            result = await db.execute(query, params)
            rows = result.fetchall()
            return [
                {
                    "filename": row[0],
                    "file_id": row[1]
                } for row in rows
            ]

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.get_filename_and_id] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_file_by_ids(db:AsyncSession, domain_data:retryDomain):
        try:
            query = text(
                """
                    SELECT
                        d.id,
                        d.filename,
                        d.filetype,
                        d.filesize,
                        d.thumnail_s3_path,
                        d.reg_date,
                        d.update_date,
                        d.upload_user_id,
                        d.status,
                        COALESCE(uf.s3_path, NULL) as s3_path,
                        COALESCE(uf.id, NULL) as upload_file_id
                    FROM drive d
                    LEFT JOIN upload_file uf
                        ON d.upload_file_id = uf.id
                    WHERE company_key = :company_key
                        AND d.id IN :file_ids
                """
            )
            params = {"company_key": domain_data.company_key, "file_ids": domain_data.file_ids}
            result = await db.execute(query, params)
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "filename": row[1],
                    "filetype": row[2],
                    "filesize": row[3],
                    "thumnail_s3_path": row[4],
                    "reg_date": row[5],
                    "update_date": row[6],
                    "upload_user_id": row[7],
                    "status": row[8],
                    "s3_path": row[9],
                    "upload_file_id": row[10]
                } for row in rows
            ]
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.get_file_by_ids] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_file_data_for_view(db:AsyncSession, company_key:str, file_id:int):
        try:
            query = text(
                """
                    WITH file_vectors AS (
                        SELECT upload_file_id, MAX(page) as page
                        FROM vector
                        GROUP BY upload_file_id
                    )
                    SELECT
                        uf.s3_path as s3_path,
                        COALESCE(fv.page, 0) as page
                    FROM drive d
                    LEFT JOIN upload_file uf
                        ON d.upload_file_id = uf.id
                    LEFT JOIN file_vectors fv
                        ON uf.id = fv.upload_file_id
                    WHERE d.company_key = :company_key
                        AND d.id = :file_id
                """
            )
            params = {"company_key": company_key, "file_id": file_id}
            result = await db.execute(query, params)
            row = result.fetchone()
            return {
                "s3_path": row[0],
                "page": row[1]
            } if row else None
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.get_file_data_for_view] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_vector_by_drive_id_and_page(db:AsyncSession, drive_id:int, page:int):
        try:
            query = text(
                """
                    SELECT
                        v.id as vector_id,
                        v.upload_file_id as upload_file_id,
                        uf.s3_path as s3_path
                    FROM drive d
                    INNER JOIN upload_file uf
                        ON d.upload_file_id = uf.id
                    INNER JOIN vector v
                        ON uf.id = v.upload_file_id
                    WHERE d.id = :drive_id
                        AND v.page = :page
                    ORDER BY v.chunk ASC
                """
            )
            params = {"drive_id": drive_id, "page": page}
            result = await db.execute(query, params)
            rows = result.fetchall()
            return [
                {
                    "vector_id": row[0],
                    "upload_file_id": row[1],
                    "s3_path": row[2]
                } for row in rows
            ] if rows else []
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.get_vector_by_drive_id_and_page] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_drive_id_by_drive_id_upload_file_id(db:AsyncSession, upload_id:int):
        try:
            query = text("""SELECT id FROM drive WHERE upload_file_id = :upload_file_id""")
            params = {"upload_file_id": upload_id}
            result = await db.execute(query, params)
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.get_drive_id_by_drive_id_upload_file_id] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_upload_file_id_by_drive_id(db:AsyncSession, domain_data:deleteFileDomain):
        try:
            query = text("""SELECT upload_file_id FROM drive WHERE id = :id""")
            params = {"id": domain_data.file_id}
            result = await db.execute(query, params)
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.get_upload_file_id_by_drive_id] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_error_page(db:AsyncSession, domain_data):
        try:
            query = text("SELECT error_page FROM drive WHERE company_key = :company_key AND upload_file_id = :upload_file_id")
            result = await db.execute(query, {"company_key": domain_data.company_key, "upload_file_id": domain_data.id})
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            logging.error(f"[queries.company_info.CompanyInfoQuery.get_error_page] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_error_page_by_drive_id(db:AsyncSession, domain_data):
        try:
            query = text("SELECT error_page FROM drive WHERE company_key = :company_key AND id = :drive_id")
            result = await db.execute(query, {"company_key": domain_data.company_key, "drive_id": domain_data.drive_ids[0]})
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            logging.error(f"[queries.company_info.CompanyInfoQuery.get_error_page_by_drive_id] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_all_page(db:AsyncSession, domain_data):
        try:
            query = text("SELECT unit_count FROM drive WHERE company_key = :company_key AND id = :drive_id")
            result = await db.execute(query, {"company_key": domain_data.company_key, "drive_id": domain_data.drive_ids[0]})
            row = result.fetchone()
            return int(row[0]) if row else None
        except Exception as e:
            logging.error(f"[queries.company_info.CompanyInfoQuery.get_all_page] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_upload_file_id_by_drive_id(db:AsyncSession, domain_data:deleteFileDomain):
        try:
            query = text("SELECT upload_file_id FROM drive WHERE id = :id")
            result = await db.execute(query, {"id": domain_data.file_id})
            row = result.fetchone()
            return {"upload_file_id": row[0]} if row else None
        except Exception as e:
            logging.error(f"[queries.drive.DriveQuery.get_upload_file_id_by_drive_id] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_is_show(db:AsyncSession, domain_data:uploadFileDomain):
        try:
            query = text("""UPDATE drive SET is_show = :is_show WHERE id IN :ids""")
            params = {"is_show": domain_data.is_show, "ids": domain_data.drive_ids}
            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.update_is_show] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def update_status_to_analysis(db:AsyncSession, domain_data:retryDomain):
        try:
            query = text("""UPDATE drive SET status = :status WHERE id IN :ids""")
            params = {"status": 3, "ids": domain_data.file_ids}
            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.update_is_show] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def update_drive_row_after_upload(db:AsyncSession, id:int, status:int, upload_file_id:int):
        try:
            query = text("""UPDATE drive SET status = :status, upload_file_id = :upload_file_id WHERE id = :id""")
            params = {"id": id, "status": status, "upload_file_id": upload_file_id}
            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.update_drive_row_after_upload] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def update_drive_row_status_by_upload_file_id(db:AsyncSession, upload_file_id:int, status:int):
        try:
            query = text("""UPDATE drive SET status = :status, error_page = :error_page WHERE upload_file_id = :upload_file_id""")
            params = {
                "upload_file_id": upload_file_id,
                "error_page": None,
                "status": status,
            }
            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.update_drive_row_status_by_upload_file_id] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def update_drive_row_status_and_err_page_by_upload_file_id(db:AsyncSession, upload_file_id:int, status:int, error_page:list):
        try:
            query = text("""UPDATE drive SET status = :status, error_page = :error_page WHERE upload_file_id = :upload_file_id""")
            params = {"upload_file_id": upload_file_id, "status": status, "error_page": str(error_page)}
            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.update_drive_row_status_by_upload_file_id] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def bulk_update_drive_row_after_upload(db:AsyncSession, upload_file_results: list, status: int):
        try:
            ids = []
            case_statements = []
            for upload_file_result in upload_file_results:
                ids.append(upload_file_result.get('drive_id'))
                case_statements.append(f"WHEN {upload_file_result.get('drive_id')} THEN {upload_file_result.get('id')}")

            query = text(f"""
                UPDATE drive 
                SET 
                    status = :status,
                    upload_file_id = CASE id 
                        {' '.join(case_statements)}
                    END
                WHERE id IN :ids
            """)

            params = {
                "status": status,
                "ids": tuple(ids)
            }

            await db.execute(query, params)
            await db.commit()
            return True

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.bulk_update_drive_row_after_upload] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def update_drive_row_status(db:AsyncSession, id:int, status:int):
        try:
            query = text("""UPDATE drive SET status = :status WHERE id = :id""")
            params = {"id": id, "status": status}
            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.update_drive_row_status] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def update_drive_row_status_and_upload_file_id(db:AsyncSession,
                                                         ids: list,
                                                         upload_file_ids: list,
                                                         status:int
                                                        ):
        try:
            for drive_id, upload_file_id in zip(ids, upload_file_ids):
                query = text("""UPDATE drive SET status = :status, upload_file_id = :upload_file_id WHERE id = :id""")
                params = {"id": drive_id, "status": status, "upload_file_id": upload_file_id}
                await db.execute(query, params)
            await db.commit()
        except Exception:
            await db.rollback()
            message = "[queries.drive.DriveQuery.update_drive_row_status_and_upload_file_id] DBError"
            logging.error(message)
            raise DBError(message)


    @staticmethod
    async def update_is_delete_and_is_on(db:AsyncSession, domain_data:deleteDomain):
        try:
            query = text("""UPDATE drive SET is_deleted = :is_deleted, is_on = :is_on, is_show = :is_show WHERE id = :id AND company_key = :company_key""")
            params = {"is_deleted": True, "is_on": False, "is_show": False, "id": domain_data.file_id, "company_key": domain_data.company_key}
            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.update_is_delete_and_is_on] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def get_active_file_ids_in_directories(db:AsyncSession, company_key:str, dir_ids:list[int]) -> list[int]:
        """삭제되지 않은 파일 id 목록 (폴더 삭제 시 파일별 소프트 삭제·벡터 정리에 사용)."""
        if not dir_ids:
            return []
        try:
            placeholders = ", ".join(f":d{i}" for i in range(len(dir_ids)))
            query = text(f"SELECT id FROM drive WHERE company_key = :company_key AND is_deleted = 0 AND drive_path_id IN ({placeholders})")
            params = {"company_key": company_key, **{f"d{i}": d for i, d in enumerate(dir_ids)}}
            return [row[0] for row in (await db.execute(query, params)).fetchall()]
        except Exception as e:
            logging.error(f"[queries.drive.DriveQuery.get_active_file_ids_in_directories] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def detach_files_from_directories(db:AsyncSession, company_key:str, dir_ids:list[int]) -> None:
        """폴더 행을 지우기 전에 (소프트 삭제된) 파일의 폴더 참조를 끊는다(FK)."""
        if not dir_ids:
            return
        try:
            placeholders = ", ".join(f":d{i}" for i in range(len(dir_ids)))
            query = text(f"UPDATE drive SET drive_path_id = NULL WHERE company_key = :company_key AND drive_path_id IN ({placeholders})")
            await db.execute(query, {"company_key": company_key, **{f"d{i}": d for i, d in enumerate(dir_ids)}})
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.detach_files_from_directories] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def rename_file(db:AsyncSession, domain_data:renameDomain):
        try:
            query = text("""UPDATE drive SET filename = :filename WHERE id = :id AND company_key = :company_key""")
            params = {"id": domain_data.drive_id, "filename": domain_data.new_name, "company_key": domain_data.company_key}
            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.rename_file] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def move_file(db:AsyncSession, domain_data:moveToDirectoryDomain):
        try:
            query = text("""UPDATE drive SET drive_path_id = :drive_path_id WHERE id = :id AND company_key = :company_key""")
            params = {"drive_path_id": domain_data.to_dir_id, "id": domain_data.drive_id, "company_key": domain_data.company_key}
            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.move_file] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def update_drive_row_update_time(db: AsyncSession, domain_data: updateFileContentDomain):
        try:
            query = text("""UPDATE drive SET update_date = :update_date WHERE id = :id""")
            params = {"update_date": domain_data.current_time, "id": domain_data.drive_id}
            await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.update_drive_row_update_time] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def delete_file(db:AsyncSession, domain_data:deleteFileDomain):
        try:
            query = text("""DELETE FROM drive WHERE id = :id AND company_key = :company_key""")
            params = {"id": domain_data.file_id, "company_key": domain_data.company_key}
            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.remove_file_by_id] DBError: {e}")
            raise DBError(e)


    @staticmethod
    async def delete_file_by_drive_path_id(db:AsyncSession, drive_path_id:int): # directory를 삭제하면 하위 모든 디렉토리가 삭제되어야 한다. 따라서, 파일 삭제 -> 디렉토리 삭제 -> 하위 파일 삭제 -> 하위 디렉토리 삭제 순서로 진행되어야 한다.
        try:
            query = text("""DELETE FROM drive WHERE drive_path_id = :drive_path_id""")
            params = {"drive_path_id": drive_path_id}
            await db.execute(query, params)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive.DriveQuery.delete_file_by_drive_path_id] DBError: {e}")
            raise DBError(e)
