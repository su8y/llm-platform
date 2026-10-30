from importlib.util import find_spec
from unittest import IsolatedAsyncioTestCase, skipUnless
from unittest.mock import AsyncMock, patch


@skipUnless(find_spec("httpx") and find_spec("numpy"), "Install the locked API requirements")
class ProxyTransportTests(IsolatedAsyncioTestCase):
    async def test_embedding_recovers_from_one_connection_failure(self) -> None:
        import base64
        import httpx
        import numpy
        from client.groxy import LLMProxyClient

        await LLMProxyClient.connect()
        vector = base64.b64encode(numpy.array([0.25, 0.5], dtype=numpy.float32)).decode()
        response = httpx.Response(200, json={"vectors": vector}, request=httpx.Request("POST", "http://proxy/llm/embeddings"))
        client = AsyncMock()
        client.post.side_effect = [httpx.ConnectError("unavailable"), response]
        try:
            with patch.object(LLMProxyClient, "_ensure_client", AsyncMock()), patch.object(LLMProxyClient, "_close_client", AsyncMock()) as reconnect:
                LLMProxyClient._clients["embedding"], original = client, LLMProxyClient._clients["embedding"]
                try:
                    result = await LLMProxyClient.embeddings("question", "test")
                    self.assertEqual(result, [0.25, 0.5])
                    self.assertEqual(client.post.await_count, 2)
                    reconnect.assert_awaited_once_with("embedding")
                finally:
                    LLMProxyClient._clients["embedding"] = original
        finally:
            await LLMProxyClient.disconnect()

    async def test_repeated_connection_failure_is_bounded_and_normalized(self) -> None:
        import httpx
        from client.groxy import LLMProxyClient
        from utils.error import LLMProxyError

        await LLMProxyClient.connect()
        client = AsyncMock()
        client.post.side_effect = httpx.RemoteProtocolError("unavailable")
        try:
            with patch.object(LLMProxyClient, "_ensure_client", AsyncMock()), patch.object(LLMProxyClient, "_close_client", AsyncMock()):
                LLMProxyClient._clients["embedding"], original = client, LLMProxyClient._clients["embedding"]
                try:
                    with self.assertRaises(LLMProxyError):
                        await LLMProxyClient.embeddings("question", "test")
                    self.assertEqual(client.post.await_count, 2)
                finally:
                    LLMProxyClient._clients["embedding"] = original
        finally:
            await LLMProxyClient.disconnect()
