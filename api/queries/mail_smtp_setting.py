import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.error import DBError

WRITABLE_COLUMNS = [
    "company_key", "is_active", "smtp_host", "smtp_port", "smtp_use_ssl", "smtp_use_tls",
    "smtp_username", "smtp_password_enc", "from_address", "from_name", "reg_date", "update_date",
]


class MailSmtpSettingQuery:

    @staticmethod
    async def get_by_company(db: AsyncSession, company_key: str) -> dict | None:
        try:
            query = text("SELECT * FROM mail_smtp_setting WHERE company_key = :company_key LIMIT 1")
            row = (await db.execute(query, {"company_key": company_key})).mappings().fetchone()
            return dict(row) if row else None
        except Exception as e:
            logging.error(f"[queries.mail_smtp_setting.MailSmtpSettingQuery.get_by_company] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def insert(db: AsyncSession, values: dict) -> int:
        try:
            columns = [c for c in WRITABLE_COLUMNS if c in values]
            query = text(f"INSERT INTO mail_smtp_setting ({', '.join(columns)}) VALUES ({', '.join(':' + c for c in columns)})")
            result = await db.execute(query, {c: values[c] for c in columns})
            await db.commit()
            return result.lastrowid
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.mail_smtp_setting.MailSmtpSettingQuery.insert] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update(db: AsyncSession, setting_id: int, values: dict) -> None:
        try:
            columns = [c for c in WRITABLE_COLUMNS if c in values and c not in ("company_key", "reg_date")]
            query = text(f"UPDATE mail_smtp_setting SET {', '.join(f'{c} = :{c}' for c in columns)}, last_error = NULL WHERE id = :id")
            await db.execute(query, {**{c: values[c] for c in columns}, "id": setting_id})
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.mail_smtp_setting.MailSmtpSettingQuery.update] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def delete(db: AsyncSession, company_key: str) -> None:
        try:
            await db.execute(text("DELETE FROM mail_smtp_setting WHERE company_key = :company_key"), {"company_key": company_key})
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.mail_smtp_setting.MailSmtpSettingQuery.delete] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def mark_result(db: AsyncSession, company_key: str, error: str | None, now: datetime) -> None:
        try:
            query = text("UPDATE mail_smtp_setting SET last_test_at = :now, last_error = :error WHERE company_key = :company_key")
            await db.execute(query, {"company_key": company_key, "error": (error or "")[:2000] or None, "now": now})
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.mail_smtp_setting.MailSmtpSettingQuery.mark_result] DBError: {e}")
            raise DBError(e)
