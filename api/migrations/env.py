import os
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

API_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if API_ROOT not in sys.path:
    sys.path.insert(0, API_ROOT)

import models  # noqa: E402  (engine 생성을 위해 DB_URI 환경변수 필요)

models.import_all_models()
config = context.config
target_metadata = models.Base.metadata

# CLI 로 직접 실행할 때는 DB_URI 환경변수를 우선한다
if os.getenv("DB_URI"):
    config.set_main_option("sqlalchemy.url", models.sync_database_url(os.environ["DB_URI"]))


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
