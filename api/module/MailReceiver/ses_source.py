"""SES 수신 소스. SES 수신 규칙(S3 action)이 버킷에 저장한 원문 MIME 객체를 LastModified 순으로 폴링한다."""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import aioboto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from utils.error import MailSourceError


@dataclass
class SesConfig:
    region: str
    bucket: str
    prefix: str
    access_key: str | None
    secret_key: str | None


@dataclass
class SesFetchResult:
    messages: list[tuple[str, bytes, datetime]]     # (key, raw, last_modified UTC naive)
    last_modified: datetime | None


def _session(config: SesConfig) -> aioboto3.Session:
    kwargs = {"region_name": config.region}
    if config.access_key and config.secret_key:
        kwargs.update(aws_access_key_id=config.access_key, aws_secret_access_key=config.secret_key)
    return aioboto3.Session(**kwargs)


_BOTO_CONFIG = Config(retries={"max_attempts": 3, "mode": "standard"}, connect_timeout=10, read_timeout=30)


class SesSource:
    @staticmethod
    async def fetch_new(config: SesConfig, since: datetime | None, limit: int = 50) -> SesFetchResult:
        try:
            async with _session(config).client("s3", config=_BOTO_CONFIG) as s3:
                candidates = []
                paginator = s3.get_paginator("list_objects_v2")
                async for page in paginator.paginate(Bucket=config.bucket, Prefix=config.prefix or ""):
                    for obj in page.get("Contents", []):
                        if obj["Key"].endswith("/") or obj.get("Size", 0) == 0:
                            continue
                        modified = obj["LastModified"].astimezone(timezone.utc).replace(tzinfo=None)
                        if since is None or modified > since:
                            candidates.append((modified, obj["Key"]))
                candidates.sort()
                messages = []
                for modified, key in candidates[:limit]:
                    response = await s3.get_object(Bucket=config.bucket, Key=key)
                    raw = await response["Body"].read()
                    messages.append((key, raw, modified))
                return SesFetchResult(messages=messages, last_modified=messages[-1][2] if messages else since)
        except (ClientError, BotoCoreError) as e:
            logging.error(f"[module.MailReceiver.ses_source.SesSource.fetch_new] 🔴 {e}")
            raise MailSourceError(f"SES/S3 error: {e}") from e

    @staticmethod
    async def test_connection(config: SesConfig) -> dict:
        try:
            async with _session(config).client("s3", config=_BOTO_CONFIG) as s3:
                response = await s3.list_objects_v2(Bucket=config.bucket, Prefix=config.prefix or "", MaxKeys=5)
                return {"ok": True, "bucket": config.bucket, "prefix": config.prefix or "", "sampleCount": response.get("KeyCount", 0)}
        except (ClientError, BotoCoreError) as e:
            raise MailSourceError(f"SES/S3 error: {e}") from e
