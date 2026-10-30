"""baseline: 2026-10-29 모델 기준으로 스키마를 수렴시킨다

Revision ID: 0001
Revises:
Create Date: 2026-10-29

신규 설치: create_all 로 전체 테이블 생성.
기존 설치: create_all(checkfirst) 로 빠진 테이블만 만들고, 모델에는 있는데 DB 에 없는 컬럼을 ADD COLUMN 한다.
(create_all 은 기존 테이블의 컬럼을 추가하지 않으므로 설치형 드리프트를 여기서 흡수한다.)
이 리비전 이후의 스키마 변경은 `alembic revision --autogenerate` 로 별도 리비전을 만든다.
"""
import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.schema import CreateColumn

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    import models

    models.import_all_models()
    bind = op.get_bind()
    metadata = models.Base.metadata

    metadata.create_all(bind=bind, checkfirst=True)

    inspector = sa.inspect(bind)
    added = 0
    for table in metadata.sorted_tables:
        existing = {column["name"] for column in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing:
                continue
            ddl = str(CreateColumn(column).compile(dialect=bind.dialect))
            if column.default is not None and isinstance(column.default.arg, bool):
                ddl += " DEFAULT " + ("1" if column.default.arg else "0")
            op.execute(sa.text(f"ALTER TABLE `{table.name}` ADD COLUMN {ddl}"))
            logging.info(f"[migrations.0001_baseline.upgrade] ✅ add column {table.name}.{column.name}")
            added += 1
    logging.info(f"[migrations.0001_baseline.upgrade] ✅ baseline synced, columns added: {added}")


def downgrade() -> None:
    # 베이스라인은 되돌리지 않는다 (기존 설치 데이터 보호)
    pass
