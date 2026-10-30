import os
from contextlib import ExitStack
from importlib.util import find_spec
from unittest import IsolatedAsyncioTestCase, skipUnless
from unittest.mock import AsyncMock, MagicMock, patch


@skipUnless(find_spec("fastapi"), "Install the locked API requirements")
class LifespanTests(IsolatedAsyncioTestCase):
    async def test_shutdown_reverses_startup_and_closes_every_resource(self) -> None:
        await self.exercise()

    async def test_partial_startup_failure_still_closes_acquired_resources(self) -> None:
        await self.exercise(fail=True)

    async def exercise(self, fail: bool = False) -> None:
        with patch.dict(os.environ, {
            "SERVER_STAGE": "docker",
            "DB_URI": "mysql+aiomysql://test:test@localhost/test",
        }):
            import main
            import models

            events = []

            def action(name: str, error: bool = False) -> AsyncMock:
                async def call(*args: object, **kwargs: object) -> None:
                    events.append(name)
                    if error:
                        raise RuntimeError("startup unavailable")
                return AsyncMock(side_effect=call)

            clients = [main.LLMProxyClient, main.MySQLClient, main.RedisClient, main.RabbitMQClient, main.MilvusClientConnector]
            with ExitStack() as mocks:
                mocks.enter_context(patch.object(models, "init_db", action("database")))
                mocks.enter_context(patch.object(models, "engine", MagicMock(dispose=action("dispose"))))
                mocks.enter_context(patch.object(models, "init_admin", action("admin")))
                mocks.enter_context(patch.object(models, "SessionLocal", MagicMock()))
                mocks.enter_context(patch.object(main.FastTextDetector, "model_init"))
                for index, client in enumerate(clients):
                    mocks.enter_context(patch.object(client, "connect", action(f"open{index}", fail and index == 3)))
                    mocks.enter_context(patch.object(client, "disconnect", action(f"close{index}")))
                if fail:
                    with self.assertRaisesRegex(RuntimeError, "startup unavailable"):
                        async with main.lifespan(main.app):
                            self.fail("Failed startup must not serve requests")
                    count = 4
                else:
                    async with main.lifespan(main.app):
                        events.append("serve")
                    count = 5
                expected = ["database", "admin"] + [f"open{i}" for i in range(count)]
                if not fail:
                    expected.append("serve")
                expected += [f"close{i}" for i in reversed(range(count))] + ["dispose"]
                self.assertEqual(events, expected)

    async def test_proxy_disconnect_closes_file_search_and_is_repeatable(self) -> None:
        from client.groxy import LLMProxyClient

        await LLMProxyClient.connect()
        clients = list(LLMProxyClient._clients.values())
        await LLMProxyClient.connect()
        self.assertEqual(list(LLMProxyClient._clients.values()), clients)
        await LLMProxyClient.disconnect()
        self.assertTrue(all(client.is_closed for client in clients))
        self.assertTrue(all(client is None for client in LLMProxyClient._clients.values()))
        await LLMProxyClient.disconnect()
