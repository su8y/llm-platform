import hashlib
import json
from collections.abc import AsyncGenerator, Awaitable, Callable, Mapping
from contextlib import aclosing
from dataclasses import dataclass
from typing import Protocol

from utils.error import DataError, VectorDBError


class Index(Protocol):
    collection_name: str
    async def exists(self) -> bool: ...
    def iterate(self, company_key: str, batch_size: int) -> AsyncGenerator[list[dict], None]: ...
    async def insert_many(self, ids: list, values: list, metadatas: list) -> None: ...


@dataclass(frozen=True)
class ReindexResult:
    documents: int
    verified: bool


def prepare(row: dict, company_key: str, texts: Mapping[str, str]) -> dict:
    if "id" not in row or not isinstance(row.get("metadata"), dict):
        raise DataError("Source record needs a chunk ID and metadata")
    metadata = dict(row["metadata"])
    if metadata.get("company_key") != company_key:
        raise DataError("Source record is outside the company scope")
    content = texts.get(str(row["id"]), metadata.get("content"))
    if not isinstance(content, str) or not content.strip():
        raise DataError("Source chunk has no text; supply a JSONL chunk mapping")
    if not isinstance(metadata.get("is_on"), bool) or not metadata.get("data_type"):
        raise DataError("Source chunk needs active status and document type")
    return {**metadata, "content": content}


def fingerprint(metadata: dict) -> str:
    return hashlib.sha256(json.dumps(metadata, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


async def reindex(
    source: Index,
    target: Index,
    company_key: str,
    embed: Callable[[str], Awaitable[list]],
    texts: Mapping[str, str] | None = None,
    write: bool = False,
    batch_size: int = 100,
) -> ReindexResult:
    """Preview first; write only to a new collection. Never switch live traffic.

    Pause source writes during migration. A failed run leaves an incomplete
    target for inspection; rerun with a new target name. Originals are retained.
    """
    if not company_key or source.collection_name == target.collection_name or not 1 <= batch_size <= 1000:
        raise DataError("Distinct collections, company scope and valid batch size are required")
    if await target.exists():
        raise DataError("Target collection must not exist")
    texts = texts or {}
    expected = {}
    async with aclosing(source.iterate(company_key, batch_size)) as batches:
        async for batch in batches:
            for row in batch:
                metadata = prepare(row, company_key, texts)
                key = str(row["id"])
                if key in expected:
                    raise DataError("Duplicate chunk ID in source scan")
                expected[key] = fingerprint(metadata)
    if not expected:
        raise DataError("No source chunks found in the company scope")
    if not write:
        return ReindexResult(len(expected), False)

    copied = set()
    async with aclosing(source.iterate(company_key, batch_size)) as batches:
        async for batch in batches:
            metadata = [prepare(row, company_key, texts) for row in batch]
            ids = [str(row["id"]) for row in batch]
            for key, item in zip(ids, metadata):
                if key in copied or expected.get(key) != fingerprint(item):
                    raise DataError("Source changed during migration; retry with writes paused")
                copied.add(key)
            for start in range(0, len(batch), 10):
                items = metadata[start:start + 10]
                vectors = [await embed(item["content"]) for item in items]
                await target.insert_many(ids[start:start + 10], vectors, items)
    actual = {}
    async with aclosing(target.iterate(company_key, batch_size)) as batches:
        async for batch in batches:
            for row in batch:
                actual[str(row["id"])] = fingerprint(row["metadata"])
    if copied != expected.keys() or actual != expected:
        raise VectorDBError("Reindex verification failed; keep the original collection active")
    return ReindexResult(len(actual), True)
