"""mail_receive_setting 테이블 추가 (IMAP / SES 수신 설정)

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-29

신규 설치는 0001 의 create_all 이 이미 만들므로 checkfirst 로 멱등 생성한다.
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    import models

    models.import_all_models()
    models.Base.metadata.tables["mail_receive_setting"].create(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    op.drop_table("mail_receive_setting")
