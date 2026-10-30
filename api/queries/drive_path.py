import logging

import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.error import DBError
from domain.user import registerDomain
from domain.drive import *



class DrivePathQuery:

    @staticmethod
    async def create_drive_path(db:AsyncSession, domain_data:registerDomain):
        try:
            query = text(
                """
                    INSERT INTO drive_path (company_key, name, depth, parent_id, reg_date, update_date)
                    VALUES (:company_key, :name, :depth, :parent_id, :reg_date, :update_date)
                """
            )
            params = {
                "company_key": domain_data.company_key,
                "name": domain_data.company_name,
                "depth": 1,
                "parent_id": None,
                "reg_date": domain_data.reg_date,
                "update_date": domain_data.reg_date
            }
            await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive_path.DrivePathQuery.create_drive_path] DBError: {e}")
            raise DBError(e)
    
    @staticmethod
    async def has_home_directory(db:AsyncSession, company_key:str) -> bool:
        try:
            query = text("SELECT id FROM drive_path WHERE company_key = :company_key AND parent_id IS NULL LIMIT 1")
            return (await db.execute(query, {"company_key": company_key})).fetchone() is not None
        except Exception as e:
            logging.error(f"[queries.drive_path.DrivePathQuery.has_home_directory] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def insert_directory_row_in_drive_path(db:AsyncSession, domain_data:makeDirectoryDomain):
        try:
            query = text(
                """
                    INSERT INTO drive_path (
                        company_key,
                        name,
                        depth,
                        parent_id,
                        reg_date,
                        update_date
                    ) VALUES (
                        :company_key,
                        :name,
                        :depth,
                        :parent_id,
                        :reg_date,
                        :update_date
                    )
                """
            )
            params = {
                "company_key": domain_data.company_key,
                "name": domain_data.dir_name,
                "depth": domain_data.parent_depth + 1,
                "parent_id": domain_data.parent_id,
                "reg_date": domain_data.reg_date,
                "update_date": domain_data.update_date
            }
            await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive_path.DrivePathQuery.insert_directory_row_in_drive_path] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_home_directory(db:AsyncSession, domain_data:getPageDomain):
        try:
            query = text("""
                SELECT id FROM drive_path WHERE company_key = :company_key AND depth = 1
            """)
            params = {"company_key": domain_data.company_key}
            result = await db.execute(query, params)
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            logging.error(f"[queries.drive_path.DrivePathQuery.get_home_directory] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def search(db:AsyncSession, domain_data:searchDomain):
        try:
            where_conditions = []
            params = {}
            if domain_data.company_key:
                where_conditions.append("company_key = :company_key")
                params["company_key"] = domain_data.company_key
            if domain_data.name:
                where_conditions.append("filename LIKE :filename")
                params["filename"] = f"%{domain_data.name}%"
            if domain_data.start_date:
                where_conditions.append("reg_date >= :start_date")
                params["start_date"] = domain_data.start_date
            if domain_data.end_date:
                where_conditions.append("reg_date <= :end_date")
                params["end_date"] = domain_data.end_date
            query_text = """
                SELECT
                    id, name, depth, update_date
                FROM
                    drive_path
                WHERE
            """
            
            if where_conditions:
                query_text += " " + " AND ".join(where_conditions)
            else:
                query_text += " 1=1"  # 항상 참인 조건
                
            query = text(query_text)
                    
            result = await db.execute(query, params)
            rows = result.fetchall()
            return [
                {
                    "dirId": row[0],
                    "dirName": row[1],
                    "depth": row[2],
                    "updateDate": row[3]
                } for row in rows
            ] if rows else []
        except Exception as e:
            logging.error(f"[queries.drive_path.DrivePathQuery.search] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_directory_by_dir_id(db:AsyncSession, dir_id:int):
        try:
            query = text(
                """
                    SELECT
                        id, name, depth
                    FROM drive_path
                    WHERE id = :dir_id
                """
            )
            params = {"dir_id": dir_id}
            result = await db.execute(query, params)
            return result.fetchone()
        except Exception as e:
            logging.error(f"[queries.drive_path.DrivePathQuery.get_directory_by_dir_id] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_directories_by_parent_id(db:AsyncSession, domain_data:getPageDomain):
        try:
            query = text(
                """
                    SELECT
                        id, name, depth
                    FROM drive_path
                    WHERE parent_id = :dir_id
                        AND company_key = :company_key
                    ORDER BY name
                """
            )
            params = {"dir_id": domain_data.current_dir_id, "company_key": domain_data.company_key}
            result = await db.execute(query, params)
            rows = result.fetchall()
            return [
                {
                    "dirId": row[0],
                    "dirName": row[1],
                    "depth": row[2]
                } for row in rows
            ] if rows else []
        except Exception as e:
            logging.error(f"[queries.drive_path.DrivePathQuery.get_directories_by_parent_id] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_parent_dir_depth(db:AsyncSession, domain_data:makeDirectoryDomain):
        try: # company_key:str, parent_id:int
            query = text(
                """
                    SELECT
                        depth
                    FROM drive_path
                    WHERE company_key = :company_key
                        AND id = :parent_id
                """
            )
            params = {"company_key": domain_data.company_key, "parent_id": domain_data.parent_id}
            result = await db.execute(query, params)
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            logging.error(f"[queries.drive_path.DrivePathQuery.get_parent_depth] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def move_directory(db:AsyncSession, domain_data:moveToDirectoryDomain):
        try:
            query = text("""UPDATE drive_path SET parent_id = :parent_id WHERE id = :id AND company_key = :company_key AND parent_id IS NOT NULL""")
            params = {"parent_id": domain_data.to_dir_id, "id": domain_data.drive_path_id, "company_key": domain_data.company_key}
            await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive_path.DrivePathQuery.move_directory] DBError: {e}")
            raise DBError(e)
        
    @staticmethod
    async def rename_directory(db:AsyncSession, domain_data:renameDomain):
        try:
            query = text("""UPDATE drive_path SET name = :dirname WHERE id = :id AND company_key = :company_key""")
            params = {"id": domain_data.drive_path_id, "dirname": domain_data.new_name, "company_key": domain_data.company_key}
            await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive_path.DrivePathQuery.rename_directory] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def get_descendant_dir_ids(db:AsyncSession, company_key:str, dir_id:int) -> list[int]:
        """dir_id 아래 모든 하위 폴더 id (자기 자신 제외), 깊은 것이 뒤에 오도록 BFS 순서."""
        try:
            result, frontier = [], [dir_id]
            query = text("SELECT id FROM drive_path WHERE company_key = :company_key AND parent_id = :parent_id")
            while frontier:
                parent = frontier.pop(0)
                rows = (await db.execute(query, {"company_key": company_key, "parent_id": parent})).fetchall()
                for row in rows:
                    result.append(row[0]); frontier.append(row[0])
            return result
        except Exception as e:
            logging.error(f"[queries.drive_path.DrivePathQuery.get_descendant_dir_ids] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def is_home_directory(db:AsyncSession, company_key:str, dir_id:int) -> bool:
        try:
            query = text("SELECT parent_id FROM drive_path WHERE company_key = :company_key AND id = :id")
            row = (await db.execute(query, {"company_key": company_key, "id": dir_id})).fetchone()
            return row is not None and row[0] is None
        except Exception as e:
            logging.error(f"[queries.drive_path.DrivePathQuery.is_home_directory] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def remove_directory_by_id(db:AsyncSession, id:int, company_key:str):
        try:
            query = text("""DELETE FROM drive_path WHERE id = :id AND company_key = :company_key""")
            params = {"id": id, "company_key": company_key}
            await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.drive_path.DrivePathQuery.remove_directory_by_id] DBError: {e}")
            raise DBError(e)
