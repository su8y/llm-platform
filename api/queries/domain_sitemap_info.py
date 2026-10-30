import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from domain.reference import deletePostDomain
from utils.error import DBError



class DomainSitemapInfoQuery:

    @staticmethod
    async def delete_row_by_sitemap_id(db:AsyncSession, domain_data:deletePostDomain):
        try:
            query = text("""DELETE FROM domain_sitemap_info WHERE id IN :id""")
            params = {"id": domain_data.sitemap_ids}

            await db.execute(query, params)
            await db.commit()

        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.domain_sitemap_info.delete_row_by_sitemap_id] Exception: {e}")
            raise DBError(e)

