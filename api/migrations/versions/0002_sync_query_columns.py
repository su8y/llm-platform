"""raw SQL 이 쓰는데 모델에 없던 컬럼 보정

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-29

cx_email.to_name_list / to_mail_list / cid_images, email_send_history.last_content_for_llm,
user_info.newest_session_key, inquire_history.purpose_5 를 모델에 추가했다.
신규 설치는 0001 의 create_all 이 이미 만들므로, 여기서는 없는 컬럼만 추가한다.
"""
import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.schema import CreateColumn

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

TARGET_COLUMNS = {
    "cx_email": ["to_name_list", "to_mail_list", "cid_images"],
    "email_send_history": ["last_content_for_llm"],
    "user_info": ["newest_session_key"],
    "inquire_history": ["purpose_5"],
}


def upgrade() -> None:
    import models

    models.import_all_models()
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table_name, column_names in TARGET_COLUMNS.items():
        table = models.Base.metadata.tables[table_name]
        existing = {column["name"] for column in inspector.get_columns(table_name)}
        for column_name in column_names:
            if column_name in existing:
                continue
            ddl = str(CreateColumn(table.columns[column_name]).compile(dialect=bind.dialect))
            op.execute(sa.text(f"ALTER TABLE `{table_name}` ADD COLUMN {ddl}"))
            logging.info(f"[migrations.0002_sync_query_columns.upgrade] ✅ add column {table_name}.{column_name}")


def downgrade() -> None:
    for table_name, column_names in TARGET_COLUMNS.items():
        for column_name in column_names:
            op.drop_column(table_name, column_name)
