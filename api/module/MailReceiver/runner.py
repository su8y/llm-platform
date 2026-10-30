"""lifespan 에서 띄우는 수집 루프. 활성 설정마다 poll_interval_sec 간격으로 폴링한다."""
import asyncio
import logging
from datetime import timedelta

from module.MailReceiver.service import MailReceiveService
from queries.mail_receive_setting import MailReceiveSettingQuery
from utils.date import get_utc_now


class MailReceiverRunner:
    _task: asyncio.Task | None = None
    _stop: asyncio.Event | None = None
    tick_sec: int = 5

    @classmethod
    async def start(cls) -> None:
        if cls._task is not None:
            return
        cls._stop = asyncio.Event()
        cls._task = asyncio.create_task(cls._loop(), name="mail-receiver")
        logging.info("[module.MailReceiver.runner.MailReceiverRunner.start] ✅ mail receiver started")

    @classmethod
    async def stop(cls) -> None:
        if cls._task is None:
            return
        cls._stop.set()
        cls._task.cancel()
        try:
            await cls._task
        except asyncio.CancelledError:
            pass
        cls._task = None
        logging.info("[module.MailReceiver.runner.MailReceiverRunner.stop] 🔴 mail receiver stopped")

    @classmethod
    async def run_once(cls, company_key: str | None = None) -> int:
        """지금 즉시 한 번 폴링(관리 화면의 '지금 수집'). company_key 가 있으면 그 회사만."""
        from models import SessionLocal

        service = MailReceiveService()
        received = 0
        async with SessionLocal() as db:
            settings = await MailReceiveSettingQuery.list_active(db)
            for setting in settings:
                if company_key and setting["company_key"] != company_key:
                    continue
                received += await service.poll_setting(db, setting)
        return received

    @classmethod
    async def _loop(cls) -> None:
        from models import SessionLocal

        service = MailReceiveService()
        while not cls._stop.is_set():
            try:
                async with SessionLocal() as db:
                    settings = await MailReceiveSettingQuery.list_active(db)
                    now = get_utc_now()
                    for setting in settings:
                        due = setting["last_polled_at"] is None or now - setting["last_polled_at"] >= timedelta(seconds=setting["poll_interval_sec"] or 60)
                        if due:
                            await service.poll_setting(db, setting)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logging.error(f"[module.MailReceiver.runner.MailReceiverRunner._loop] 🔴 Exception: {e}")
            try:
                await asyncio.wait_for(cls._stop.wait(), timeout=cls.tick_sec)
            except asyncio.TimeoutError:
                pass
