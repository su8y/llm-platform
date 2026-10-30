import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.error import DBError

# 코드에 고정된 컬럼 화이트리스트. payload 값은 절대 컬럼명으로 쓰지 않는다
WRITABLE_COLUMNS = [
    "company_key", "source_type", "is_active", "poll_interval_sec",
    "imap_host", "imap_port", "imap_use_ssl", "imap_username", "imap_password_enc", "imap_folder",
    "ses_region", "ses_bucket", "ses_prefix", "ses_access_key", "ses_secret_key_enc",
    "reg_date", "update_date",
]


class MailReceiveSettingQuery:

    @staticmethod
    async def get_by_company(db: AsyncSession, company_key: str, source_type: str) -> dict | None:
        try:
            query = text("SELECT * FROM mail_receive_setting WHERE company_key = :company_key AND source_type = :source_type LIMIT 1")
            row = (await db.execute(query, {"company_key": company_key, "source_type": source_type})).mappings().fetchone()
            return dict(row) if row else None
        except Exception as e:
            logging.error(f"[queries.mail_receive_setting.MailReceiveSettingQuery.get_by_company] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def list_by_company(db: AsyncSession, company_key: str) -> list[dict]:
        try:
            query = text("SELECT * FROM mail_receive_setting WHERE company_key = :company_key ORDER BY source_type")
            rows = (await db.execute(query, {"company_key": company_key})).mappings().fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logging.error(f"[queries.mail_receive_setting.MailReceiveSettingQuery.list_by_company] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def list_active(db: AsyncSession) -> list[dict]:
        try:
            query = text("SELECT * FROM mail_receive_setting WHERE is_active = 1 ORDER BY id")
            rows = (await db.execute(query)).mappings().fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logging.error(f"[queries.mail_receive_setting.MailReceiveSettingQuery.list_active] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def insert(db: AsyncSession, values: dict) -> int:
        try:
            columns = [c for c in WRITABLE_COLUMNS if c in values]
            query = text(f"INSERT INTO mail_receive_setting ({', '.join(columns)}) VALUES ({', '.join(':' + c for c in columns)})")
            result = await db.execute(query, {c: values[c] for c in columns})
            await db.commit()
            return result.lastrowid
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.mail_receive_setting.MailReceiveSettingQuery.insert] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update(db: AsyncSession, setting_id: int, values: dict, reset_checkpoint: bool = False) -> None:
        try:
            columns = [c for c in WRITABLE_COLUMNS if c in values and c not in ("company_key", "source_type", "reg_date")]
            set_clause = ", ".join(f"{c} = :{c}" for c in columns)
            if reset_checkpoint:
                set_clause += ", imap_last_uid = 0, imap_uidvalidity = NULL, last_error = NULL"
            query = text(f"UPDATE mail_receive_setting SET {set_clause} WHERE id = :id")
            await db.execute(query, {**{c: values[c] for c in columns}, "id": setting_id})
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.mail_receive_setting.MailReceiveSettingQuery.update] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def delete(db: AsyncSession, company_key: str, source_type: str) -> None:
        try:
            query = text("DELETE FROM mail_receive_setting WHERE company_key = :company_key AND source_type = :source_type")
            await db.execute(query, {"company_key": company_key, "source_type": source_type})
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.mail_receive_setting.MailReceiveSettingQuery.delete] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_imap_checkpoint(db: AsyncSession, setting_id: int, uidvalidity: int, last_uid: int, received: int, now: datetime) -> None:
        try:
            query = text("""
                UPDATE mail_receive_setting
                SET imap_uidvalidity = :uidvalidity, imap_last_uid = :last_uid, received_count = received_count + :received,
                    last_polled_at = :now, last_success_at = :now, last_error = NULL
                WHERE id = :id
            """)
            await db.execute(query, {"id": setting_id, "uidvalidity": uidvalidity, "last_uid": last_uid, "received": received, "now": now})
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.mail_receive_setting.MailReceiveSettingQuery.update_imap_checkpoint] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def update_ses_checkpoint(db: AsyncSession, setting_id: int, last_modified: datetime | None, received: int, now: datetime) -> None:
        try:
            query = text("""
                UPDATE mail_receive_setting
                SET ses_last_modified = :last_modified, received_count = received_count + :received,
                    last_polled_at = :now, last_success_at = :now, last_error = NULL
                WHERE id = :id
            """)
            await db.execute(query, {"id": setting_id, "last_modified": last_modified, "received": received, "now": now})
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.mail_receive_setting.MailReceiveSettingQuery.update_ses_checkpoint] DBError: {e}")
            raise DBError(e)

    @staticmethod
    async def mark_error(db: AsyncSession, setting_id: int, error: str, now: datetime) -> None:
        try:
            query = text("UPDATE mail_receive_setting SET last_polled_at = :now, last_error = :error WHERE id = :id")
            await db.execute(query, {"id": setting_id, "error": error[:2000], "now": now})
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.error(f"[queries.mail_receive_setting.MailReceiveSettingQuery.mark_error] DBError: {e}")
            raise DBError(e)
