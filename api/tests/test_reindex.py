from copy import deepcopy
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from support import DataError, VectorDBError, load_module


reindex = load_module("module/Retrieval/reindex.py").reindex


class MemoryIndex:
    def __init__(self, name: str, records: list[dict], exists: bool = True) -> None:
        self.collection_name = name
        self.records = deepcopy(records)
        self.present = exists
        self.scans = 0
        self.closed = 0

    async def exists(self) -> bool:
        return self.present

    async def iterate(self, company_key: str, batch_size: int):
        self.scans += 1
        try:
            for start in range(0, len(self.records), batch_size):
                yield deepcopy(self.records[start:start + batch_size])
        finally:
            self.closed += 1

    async def insert_many(self, ids: list, values: list, metadatas: list) -> None:
        self.present = True
        self.records.extend({"id": key, "metadata": deepcopy(metadata)}
                            for key, metadata in zip(ids, metadatas))


class ReindexTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.rows = [{"id": "post-1", "metadata": {
            "id": 9, "company_key": "a", "is_on": False,
            "data_type": "post", "content": "AB123 policy",
        }}]
        self.source = MemoryIndex("old", self.rows)
        self.target = MemoryIndex("new", [], exists=False)
        self.embed = AsyncMock(return_value=[0.1])

    async def test_preview_has_no_writes_or_embedding_calls(self) -> None:
        result = await reindex(self.source, self.target, "a", self.embed)
        self.assertEqual(result.documents, 1)
        self.assertFalse(result.verified)
        self.assertFalse(self.target.present)
        self.embed.assert_not_awaited()

    async def test_write_preserves_ids_scope_and_disabled_state(self) -> None:
        result = await reindex(self.source, self.target, "a", self.embed, write=True)
        self.assertTrue(result.verified)
        self.assertEqual(self.target.records, self.rows)
        self.assertEqual(self.source.records, self.rows)
        self.assertEqual(self.source.closed, 2)
        self.assertEqual(self.target.closed, 1)
        self.embed.assert_awaited_once_with("AB123 policy")

    async def test_missing_text_fails_before_target_creation(self) -> None:
        self.source.records[0]["metadata"].pop("content")
        with self.assertRaises(DataError):
            await reindex(self.source, self.target, "a", self.embed, write=True)
        self.assertFalse(self.target.present)
        self.assertEqual(self.source.closed, 1)
        self.embed.assert_not_awaited()

    async def test_external_text_mapping_is_reembedded(self) -> None:
        self.source.records[0]["metadata"].pop("content")
        result = await reindex(self.source, self.target, "a", self.embed,
                               texts={"post-1": "recovered chunk"}, write=True)
        self.assertTrue(result.verified)
        self.embed.assert_awaited_once_with("recovered chunk")

    async def test_existing_target_and_identical_names_are_rejected(self) -> None:
        self.target.present = True
        with self.assertRaises(DataError):
            await reindex(self.source, self.target, "a", self.embed, write=True)
        with self.assertRaises(DataError):
            await reindex(self.source, self.source, "a", self.embed, write=True)
        self.assertEqual(self.source.scans, 0)

    async def test_company_boundary_is_enforced_before_write(self) -> None:
        self.source.records[0]["metadata"]["company_key"] = "b"
        with self.assertRaises(DataError):
            await reindex(self.source, self.target, "a", self.embed, write=True)
        self.assertFalse(self.target.present)

    async def test_source_change_between_passes_is_rejected(self) -> None:
        iterate = self.source.iterate

        async def changing(company_key: str, batch_size: int):
            if self.source.scans:
                self.source.records[0]["metadata"]["content"] = "changed"
            async for batch in iterate(company_key, batch_size):
                yield batch

        self.source.iterate = changing
        with self.assertRaises(DataError):
            await reindex(self.source, self.target, "a", self.embed, write=True)
        self.assertFalse(self.target.present)

    async def test_target_verification_failure_does_not_touch_source(self) -> None:
        async def corrupt(ids: list, values: list, metadatas: list) -> None:
            self.target.present = True

        self.target.insert_many = corrupt
        with self.assertRaises(VectorDBError):
            await reindex(self.source, self.target, "a", self.embed, write=True)
        self.assertEqual(self.source.records, self.rows)

    async def test_embedding_failure_closes_source_scan(self) -> None:
        self.embed.side_effect = ConnectionError("unavailable")
        with self.assertRaises(ConnectionError):
            await reindex(self.source, self.target, "a", self.embed, write=True)
        self.assertEqual(self.source.closed, 2)
        self.assertFalse(self.target.present)
