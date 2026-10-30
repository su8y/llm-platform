import asyncio
import importlib
import logging
import os
import pkgutil
from datetime import datetime, timezone
from pydantic import BaseModel
from uuid import uuid4

from domain.user import registerDomain
from utils.constants import REAL_INDEX

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from werkzeug.security import generate_password_hash



# SQLAlchemy Config
SQLALCHEMY_DATABASE_URL = os.getenv("DB_URI")
ENGINE_OPTION_CONFIG = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,
    "pool_recycle": 9
}
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, **ENGINE_OPTION_CONFIG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()



async def get_db():
    """Generating DB Session for Injecting to Router Function"""
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            try:
                await session.close()
            except:
                logging.warning("[models.__init__.get_db] Fail to close session. Session could go to Python GC or Already closed Connection by RDS")


async def close_db(db:AsyncSession):
    """For closing session before endpoint of API router"""
    try:
        logging.info("[models.__init__.close_db] Try to close session when Doing Long Time Task in Router")
        await db.close()
        logging.info("[models.__init__.close_db] Success to close session")
    except:
        logging.warning(f"[api.drive.delete] fail to close db session")


# building table when application start
def import_all_models() -> None:
    """models/ 패키지의 모든 모듈을 import 해 Base.metadata에 테이블을 등록한다. 신규 모델 파일을 추가하면 자동 포함."""
    package_dir = os.path.dirname(__file__)
    for module_info in pkgutil.iter_modules([package_dir]):
        importlib.import_module(f"{__name__}.{module_info.name}")


def sync_database_url(async_url: str) -> str:
    """alembic은 동기 드라이버로 실행한다. mysql+aiomysql → mysql+pymysql.
    alembic Config 는 ConfigParser 보간을 쓰므로 URL 인코딩된 비밀번호의 '%' 는 '%%' 로 이스케이프한다."""
    return async_url.replace("+aiomysql", "+pymysql").replace("%", "%%")


def run_migrations() -> None:
    """alembic upgrade head. 베이스라인 리비전이 create_all + 누락 컬럼 보정을 멱등으로 수행하므로 신규·기존 설치 모두 수렴한다."""
    from alembic import command
    from alembic.config import Config

    api_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config = Config(os.path.join(api_root, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(api_root, "migrations"))
    config.set_main_option("sqlalchemy.url", sync_database_url(SQLALCHEMY_DATABASE_URL))
    command.upgrade(config, "head")
    logging.info("[models.__init__.run_migrations] ✅ alembic upgrade head done")


async def init_db() -> None:
    import_all_models()
    await asyncio.to_thread(run_migrations)


async def init_admin(db: AsyncSession) -> None:
    from queries.company_info import CompanyInfoQuery
    from queries.user_info import UserInfoQuery

    class getUserDomainData(BaseModel):
        user_id: str

    user_id = os.getenv("ADMIN_USER_ID", "admin")
    admin_row = await UserInfoQuery.get_user(db=db, domain_data=getUserDomainData(user_id=user_id))
    if admin_row:
        await _apply_admin_email_setting(db=db, company_key=admin_row["company_key"])
        await _ensure_admin_drive_home(db=db, company_key=admin_row["company_key"], company_name=admin_row.get("company_name") or os.getenv("ADMIN_COMPANY_NAME", "admin"))
        return

    domain_data = registerDomain(
        company_key=uuid4().hex,
        company_name=os.getenv("ADMIN_COMPANY_NAME", "admin"),
        user_id=user_id,
        hashed_password=generate_password_hash(
            os.getenv("ADMIN_USER_PASSWORD", "admin123!@#"), method="pbkdf2:sha256",
        ),
        email_address=os.getenv("ADMIN_EMAIL_ADDRESS", "admin@admin.com"),
        department=os.getenv("ADMIN_DEPARTMENT", "admin"),
        reg_date=datetime.now(timezone.utc),
        lang=os.getenv("ADMIN_LANG", "ko"),
        expired_date=datetime(9999, 12, 31, tzinfo=timezone.utc),
        plan_info_id=1,
        credit_available=-1,
        parser_credit_available=-1,
        vector_db_index=REAL_INDEX,
        vector_db_namespace=uuid4().hex,
        user_auth=1,
        certifi=True,
        is_admin=True,
    )
    await create_db_metadata(db=db)
    await CompanyInfoQuery.register(db=db, domain_data=domain_data)
    await create_invite_history(
        db=db, company_key=domain_data.company_key, email_address=domain_data.email_address,
    )
    await UserInfoQuery.register(db=db, domain_data=domain_data)
    await _apply_admin_email_setting(db=db, company_key=domain_data.company_key)
    await _ensure_admin_drive_home(db=db, company_key=domain_data.company_key, company_name=domain_data.company_name)


async def _ensure_admin_drive_home(db: AsyncSession, company_key: str, company_name: str) -> None:
    """파일 저장소 루트 폴더. 회원가입(register)은 만들지만 init_admin 경로에는 없어서 설치형 admin 은 폴더를 만들 수 없었다."""
    from queries.drive_path import DrivePathQuery

    if await DrivePathQuery.has_home_directory(db=db, company_key=company_key):
        return
    now = datetime.now(timezone.utc)
    await DrivePathQuery.create_drive_path(db=db, domain_data=registerDomain.model_construct(company_key=company_key, company_name=company_name, reg_date=now))
    logging.info(f"[models.__init__._ensure_admin_drive_home] ✅ drive home created for admin company")


async def _apply_admin_email_setting(db: AsyncSession, company_key: str) -> None:
    """설치형 AI 메일 메뉴 노출 스위치. ADMIN_EMAIL_AVAILABLE(기본 true) 로 company_info.email_available 을 맞추고,
    발신 주소/이름이 비어 있으면 ADMIN_EMAIL_ADDRESS / ADMIN_COMPANY_NAME 으로 채운다. 매 부팅마다 멱등 적용."""
    from queries.company_info import CompanyInfoQuery

    email_available = os.getenv("ADMIN_EMAIL_AVAILABLE", "true").strip().lower() in ("1", "true", "yes", "on")
    await CompanyInfoQuery.update_email_setting(
        db=db,
        company_key=company_key,
        email_available=email_available,
        from_address=os.getenv("ADMIN_EMAIL_ADDRESS", "admin@admin.com"),
        from_name=os.getenv("ADMIN_COMPANY_NAME", "admin"),
    )
    logging.info(f"[models.__init__._apply_admin_email_setting] ✅ email_available={email_available}")


async def create_db_metadata(db:AsyncSession):
    from queries.user_auth import UserAuthQuery
    from queries.plan_info import PlanInfoQuery
    
    user_auth_metadatas = [
        {
            "id": 1,
            "common": True,
            "auth_name": "Master",
            "auth_account_manage": True,
            "auth_plan_manage": True,
            "auth_reference_view": True,
            "auth_reference_write": True,
            "auth_reference_category_manage": True,
            "auth_prompt_manage": True,
            "auth_playground_use": True,
            "auth_reference_language_all": True,
            "auth_prompt_manage": True,
        },
        {
            "id": 2,
            "common": True,
            "auth_name": "Manager",
            "auth_account_manage": False,
            "auth_plan_manage": False,
            "auth_reference_view": True,
            "auth_reference_write": True,
            "auth_reference_category_manage": True,
            "auth_prompt_manage": True,
            "auth_playground_use": True,
            "auth_reference_language_all": True,
            "auth_prompt_manage": True,
        },
        {
            "id": 3,
            "common": True,
            "auth_name": "Viewer",
            "auth_account_manage": False,
            "auth_plan_manage": False,
            "auth_reference_view": False,
            "auth_reference_write": False,
            "auth_reference_category_manage": False,
            "auth_prompt_manage": False,
            "auth_playground_use": True,
            "auth_reference_language_all": False,
            "auth_prompt_manage": False,
        }
    ]
    
    for user_auth_metadata in user_auth_metadatas:
        await UserAuthQuery.insert_metadata(db=db, **user_auth_metadata)
    
    plan_info_metadatas = {
        "id": 1,
        "plan_name": "admin",
        "plan_price": 0,
        "init_credit": -1,
        "model": "llm-platform",
    }
    
    await PlanInfoQuery.insert_metadata(db=db, **plan_info_metadatas)
        
    
async def create_invite_history(db:AsyncSession, company_key:str, email_address:str):
    from queries.invite_history import InviteHistoryQuery
    
    invite_history_metadatas = {
        "id": 1,
        "email_address_invite": email_address,
        "company_key": company_key,
        "success": True,
        "accept": True
    }
    
    await InviteHistoryQuery.insert_metadata(db=db, **invite_history_metadatas)