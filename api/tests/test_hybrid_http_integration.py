import asyncio
import json
import os
from unittest import IsolatedAsyncioTestCase, skipUnless
from unittest.mock import patch
from uuid import uuid4


@skipUnless(os.getenv("LLM_PLATFORM_TEST_VENDOR_URL", ""), "Disposable provider fixture is not configured")
class HybridHTTPIntegrationTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        import httpx
        from client.groxy import LLMProxyClient
        from client.milvus import MilvusClient

        self.environment = patch.dict(os.environ, {
            "VECTOR_DB_URI": os.environ["LLM_PLATFORM_TEST_MILVUS_URI"],
            "LLM_PROXY_URL": os.environ["LLM_PLATFORM_TEST_PROXY_URL"],
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.http = httpx.AsyncClient(base_url=os.environ["LLM_PLATFORM_TEST_VENDOR_URL"], timeout=10)
        self.addAsyncCleanup(self.http.aclose)
        await LLMProxyClient.connect()
        self.addAsyncCleanup(LLMProxyClient.disconnect)
        self.names = [f"test_http_{uuid4().hex}" for _ in range(2)]
        self.source, self.target = [MilvusClient(name) for name in self.names]
        self.addAsyncCleanup(self.drop_collections)
        self.proxy = LLMProxyClient

    async def drop_collections(self) -> None:
        from client.milvus import MilvusClientConnector

        connection = await MilvusClientConnector.get_client()
        try:
            for name in self.names:
                if await asyncio.to_thread(connection.has_collection, name, timeout=10):
                    await asyncio.to_thread(connection.drop_collection, name, timeout=10)
        finally:
            await MilvusClientConnector.disconnect()

    async def seed(self) -> None:
        texts = ["AB123 환불 안내", "CD456 교환 정책", "PRIVATE_AB123", "DISABLED_AB123", "WRONG_FILE_AB123", "WRONG_TYPE_AB123"]
        metadata = [{
            "id": index, "company_key": "a", "is_on": True,
            "upload_file_id": 7, "data_type": "post", "content": text,
        } for index, text in enumerate(texts)]
        metadata[2]["company_key"] = "b"
        metadata[3]["is_on"] = False
        metadata[4]["upload_file_id"] = 8
        metadata[5]["data_type"] = "email"
        vectors = [await self.proxy.embeddings(text, "llm-platform-install") for text in texts]
        self.assertTrue(all(len(vector) == 1024 for vector in vectors))
        await self.source.insert_many([str(i) for i in range(len(texts))], vectors, metadata)
        (await self.http.post("/reset")).raise_for_status()

    async def test_real_http_proxy_refines_once_and_enforces_scope(self) -> None:
        from module.Retrieval.core import SearchScope
        from module.Retrieval.service import Retriever

        await self.seed()
        retriever = Retriever(self.source, self.proxy, "llm-platform-install", "vllm", "fixture")
        hits = await retriever.find("AB123", SearchScope("a", 7, ("post",)), history=[{"role": "human", "message": "환불"}])
        self.assertEqual({hit.id for hit in hits}, {"0", "1"})
        stats = (await self.http.get("/stats")).json()
        self.assertEqual(stats["embeddings"], ["AB123", "CD456"])
        self.assertEqual(len(stats["chats"]), 1)
        context = json.dumps(stats["chats"], ensure_ascii=False)
        for marker in ("PRIVATE_", "DISABLED_", "WRONG_FILE_", "WRONG_TYPE_"):
            self.assertNotIn(marker, context)
        self.assertIn("환불", context)

    async def test_invalid_streamed_decision_keeps_original_results(self) -> None:
        from module.Retrieval.core import SearchScope
        from module.Retrieval.service import Retriever

        await self.seed()
        retriever = Retriever(self.source, self.proxy, "llm-platform-install", "vllm", "fixture")
        hits = await retriever.find("INVALID_DECISION", SearchScope("a", 7, ("post",)))
        self.assertEqual({hit.id for hit in hits}, {"0", "1"})
        stats = (await self.http.get("/stats")).json()
        self.assertEqual(stats["embeddings"], ["INVALID_DECISION"])
        self.assertEqual(len(stats["chats"]), 1)

    async def test_reindex_embeds_through_real_proxy_http(self) -> None:
        from module.Retrieval.reindex import reindex

        await self.seed()

        async def embed(text: str) -> list:
            return await self.proxy.embeddings(text, "llm-platform-install")

        preview = await reindex(self.source, self.target, "a", embed)
        self.assertEqual(preview.documents, 5)
        self.assertFalse(await self.target.exists())
        self.assertEqual((await self.http.get("/stats")).json()["embeddings"], [])
        result = await reindex(self.source, self.target, "a", embed, write=True, batch_size=2)
        self.assertTrue(result.verified)
        self.assertEqual(result.documents, 5)
        self.assertEqual(len((await self.http.get("/stats")).json()["embeddings"]), 5)
        filters = {"company_key": "a", "is_on": True, "upload_file_id": 7, "data_type": {"$in": ["post"]}}
        self.assertEqual([hit.id for hit in await self.target.find_lexical("AB123", filter=filters)], ["0"])
        self.assertEqual(len((await self.source.fetch([str(i) for i in range(6)]))["vectors"]), 6)
