"""mail_smtp_setting 테이블 추가 (SMTP 발신 설정)

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-29
"""
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    import models

    models.import_all_models()
    models.Base.metadata.tables["mail_smtp_setting"].create(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    op.drop_table("mail_smtp_setting")
