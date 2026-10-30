"""Opt-in contract test against an actual Milvus 2.6 server."""

import os
from unittest import IsolatedAsyncioTestCase, skipUnless
from unittest.mock import patch
from unittest.mock import AsyncMock
from uuid import uuid4


@skipUnless(os.getenv("LLM_PLATFORM_TEST_MILVUS_URI", ""), "Milvus integration endpoint is not configured")
class MilvusIntegrationTests(IsolatedAsyncioTestCase):
    async def test_configured_dimension_accepts_matching_vectors(self) -> None:
        import asyncio
        from client.milvus import MilvusClient, MilvusClientConnector

        name = f"test_dimension_{uuid4().hex}"
        with patch.dict(os.environ, {
            "VECTOR_DB_URI": os.getenv("LLM_PLATFORM_TEST_MILVUS_URI", ""),
            "VECTOR_DIMENSION": "1536",
        }):
            client = MilvusClient(name)
            try:
                vector = [1.0] + [0.0] * 1535
                metadata = {"company_key": "a", "is_on": True, "data_type": "post", "content": "AB123"}
                await client.insert_many(["a"], [vector], [metadata])
                self.assertEqual([hit.id for hit in await client.find(vector, filter={"company_key": "a"})], ["a"])
            finally:
                connection = MilvusClientConnector._client
                if connection is not None:
                    if await asyncio.to_thread(connection.has_collection, name, timeout=10):
                        await asyncio.to_thread(connection.drop_collection, name, timeout=10)
                await MilvusClientConnector.disconnect()

    async def test_reindex_legacy_collection_into_searchable_bm25(self) -> None:
        import asyncio
        from pymilvus import DataType
        from client.milvus import MilvusClient, MilvusClientConnector
        from module.Retrieval.reindex import reindex

        names = [f"test_reindex_{uuid4().hex}" for _ in range(2)]
        with patch.dict(os.environ, {"VECTOR_DB_URI": os.getenv("LLM_PLATFORM_TEST_MILVUS_URI", "")}):
            connection = await MilvusClientConnector.get_client()
            try:
                schema = connection.create_schema(auto_id=False, enable_dynamic_field=True)
                schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=1000)
                schema.add_field("vector", DataType.FLOAT_VECTOR, dim=1024)
                schema.add_field("metadata", DataType.JSON)
                schema.add_field("data_type", DataType.VARCHAR, max_length=32)
                schema.add_field("is_on", DataType.BOOL)
                indexes = connection.prepare_index_params()
                indexes.add_index("vector", index_type="AUTOINDEX", metric_type="COSINE")
                await asyncio.to_thread(connection.create_collection, names[0], schema=schema, index_params=indexes, timeout=10)
                source, target = [MilvusClient(name) for name in names]
                vector = [1.0] + [0.0] * 1023
                metadata = [
                    {"id": 1, "company_key": "a", "is_on": True, "data_type": "post", "content": "AB123 refund"},
                    {"id": 2, "company_key": "a", "is_on": False, "data_type": "post", "content": "AB123 disabled"},
                    {"id": 3, "company_key": "b", "is_on": True, "data_type": "post", "content": "AB123 private"},
                ]
                await source.insert_many(["a1", "a2", "b1"], [vector] * 3, metadata)
                self.assertEqual(await source.find_lexical("AB123"), [])
                embed = AsyncMock(return_value=vector)
                preview = await reindex(source, target, "a", embed)
                self.assertEqual(preview.documents, 2)
                self.assertFalse(await target.exists())
                embed.assert_not_awaited()
                result = await reindex(source, target, "a", embed, write=True, batch_size=1)
                self.assertTrue(result.verified)
                self.assertEqual(result.documents, 2)
                filters = {"company_key": "a", "is_on": True}
                self.assertEqual([hit.id for hit in await target.find_lexical("AB123", filter=filters)], ["a1"])
                self.assertEqual([hit.id for hit in await target.find(vector, filter=filters)], ["a1"])
                self.assertEqual(len((await source.fetch(["a1", "a2", "b1"]))["vectors"]), 3)
            finally:
                for name in names:
                    if await asyncio.to_thread(connection.has_collection, name, timeout=10):
                        await asyncio.to_thread(connection.drop_collection, name, timeout=10)
                await MilvusClientConnector.disconnect()

    async def test_bm25_scope_update_and_delete(self) -> None:
        from client.milvus import MilvusClient, MilvusClientConnector

        name = f"test_retrieval_{uuid4().hex}"
        with patch.dict(os.environ, {"VECTOR_DB_URI": os.getenv("LLM_PLATFORM_TEST_MILVUS_URI", "")}):
            client = MilvusClient(name)
            try:
                metadata = [
                    {"id": 1, "company_key": "a", "is_on": True, "data_type": "post", "content": "AB123 refund"},
                    {"id": 2, "company_key": "b", "is_on": True, "data_type": "post", "content": "AB123 private"},
                ]
                await client.insert_many(["a", "b"], [[1.0] + [0.0] * 1023] * 2, metadata)
                filters = {"company_key": "a", "is_on": True}
                hits = await client.find_lexical("AB123", filter=filters)
                self.assertEqual([hit.id for hit in hits], ["a"])
                await client.update(["a"], [{"content": "CD456 replacement"}])
                self.assertEqual(await client.find_lexical("AB123", filter=filters), [])
                self.assertEqual(len(await client.find_lexical("CD456", filter=filters)), 1)
                await client.update(["a"], [{"is_on": False}])
                self.assertEqual(await client.find_lexical("CD456", filter=filters), [])
                await client.remove(id=["a"])
                self.assertEqual((await client.fetch(["a"]))["vectors"], {})
            finally:
                connection = MilvusClientConnector._client
                if connection is not None:
                    import asyncio
                    await asyncio.to_thread(connection.drop_collection, name, timeout=10.0)
                await MilvusClientConnector.disconnect()
