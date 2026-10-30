import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.error import DBError
from domain.email import *

from utils.date import *



#id:int(auto), content_id(str), s3_key(str), content_type(str), size(int), filename(str), last_used_at(datetime), created_at(datetime), updated_at(datetime)
class EmailCIDImagesQuery:

    @staticmethod
    async def insert_row(db:AsyncSession, domain_data:UploadBase64Domain):
        try:
            query = text(
                """INSERT INTO
                        email_cid_images (content_id, s3_key, content_type, size, filename, last_used_at, created_at, updated_at)
                    VALUES
                        (:content_id, :s3_key, :content_type, :size, :filename, :last_used_at, :created_at, :updated_at);
                """
            )
            async with db.begin_nested():
                for insert_data in domain_data.insert_rows:
                    params = {
                        "content_id": insert_data["content_id"],
                        "s3_key": insert_data["s3_key"],
                        "content_type": insert_data["content_type"],
                        "size": insert_data["size"],
                        "filename": insert_data["filename"],
                        "last_used_at": insert_data["current_date"],
                        "created_at": insert_data["current_date"],
                        "updated_at": insert_data["current_date"],

                    }
                    await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.email_cid_images.EmailCIDImagesQuery.insert_row] DBError: {e}")
            raise DBError(e)