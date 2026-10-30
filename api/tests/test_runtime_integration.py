import os
from unittest import IsolatedAsyncioTestCase, skipUnless
from uuid import uuid4


@skipUnless(os.getenv("LLM_PLATFORM_TEST_API_URL", ""), "Disposable runtime endpoints are not configured")
class RuntimeIntegrationTests(IsolatedAsyncioTestCase):
    async def test_health_schema_and_admin_login(self) -> None:
        import httpx

        async with httpx.AsyncClient(base_url=os.environ["LLM_PLATFORM_TEST_API_URL"], timeout=15) as client:
            health = await client.get("/check")
            self.assertEqual(health.status_code, 200)
            self.assertEqual(health.json()["code"], 200)
            schema = await client.get("/openapi.json")
            self.assertEqual(schema.status_code, 200)
            self.assertIn("/user/login", schema.json()["paths"])
            login = await client.post("/user/login", json={"user_id": "test-admin", "user_password": "test-admin-password"})
            self.assertEqual(login.status_code, 200)
            self.assertEqual(login.json()["code"], 200)
            token = login.json()["data"]["accessToken"]
            self.assertTrue(token)
            # 로그인 직후 사용자 정보 조회는 모든 모델 테이블·컬럼을 조인한다 → 스키마 드리프트 회귀 검출
            info = await client.get("/user/get_info", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(info.status_code, 200)
            self.assertEqual(info.json()["data"]["userId"], "test-admin")
            self.assertTrue(info.json()["data"]["emailAvailable"], "ADMIN_EMAIL_AVAILABLE 기본값으로 AI 메일 메뉴가 켜져야 한다")

    async def test_mail_receive_setting_roundtrip_hides_secrets(self) -> None:
        import httpx

        async with httpx.AsyncClient(base_url=os.environ["LLM_PLATFORM_TEST_API_URL"], timeout=30) as client:
            login = await client.post("/user/login", json={"user_id": "test-admin", "user_password": "test-admin-password"})
            headers = {"Authorization": f"Bearer {login.json()['data']['accessToken']}"}
            body = {"sourceType": "imap", "imapHost": "imap.example.test", "imapPort": 993, "imapUseSsl": True,
                    "imapUsername": "cs@example.test", "imapPassword": "secret-pw", "imapFolder": "INBOX", "pollIntervalSec": 60, "isActive": False}
            saved = await client.post("/email/setting/upsert", json=body, headers=headers)
            self.assertEqual(saved.status_code, 200, saved.text)
            self.assertEqual(saved.json()["code"], 200)
            data = saved.json()["data"]
            self.assertTrue(data["hasImapPassword"])
            self.assertNotIn("secret-pw", saved.text)
            self.assertNotIn("imap_password_enc", data)
            listed = await client.get("/email/setting/list", headers=headers)
            self.assertEqual([row["source_type"] for row in listed.json()["data"]], ["imap"])
            # 비밀번호를 비워 다시 저장해도 저장된 값이 유지된다
            body["imapPassword"] = ""
            again = await client.post("/email/setting/upsert", json=body, headers=headers)
            self.assertTrue(again.json()["data"]["hasImapPassword"])
            # 잘못된 소스는 400
            bad = await client.post("/email/setting/upsert", json={**body, "sourceType": "pop3"}, headers=headers)
            self.assertEqual(bad.status_code, 400)
            deleted = await client.post("/email/setting/delete", json={"sourceType": "imap"}, headers=headers)
            self.assertEqual(deleted.json()["code"], 200)
            self.assertEqual((await client.get("/email/setting/list", headers=headers)).json()["data"], [])

    async def test_smtp_setting_roundtrip_hides_password(self) -> None:
        import httpx

        async with httpx.AsyncClient(base_url=os.environ["LLM_PLATFORM_TEST_API_URL"], timeout=30) as client:
            login = await client.post("/user/login", json={"user_id": "test-admin", "user_password": "test-admin-password"})
            headers = {"Authorization": f"Bearer {login.json()['data']['accessToken']}"}
            self.assertIsNone((await client.get("/email/setting/smtp/get", headers=headers)).json()["data"])
            body = {"smtpHost": "smtp.example.test", "smtpPort": 587, "smtpUseSsl": False, "smtpUseTls": True,
                    "smtpUsername": "cs@example.test", "smtpPassword": "smtp-secret", "fromAddress": "cs@example.test", "fromName": "CS", "isActive": True}
            saved = await client.post("/email/setting/smtp/upsert", json=body, headers=headers)
            self.assertEqual(saved.status_code, 200, saved.text)
            self.assertTrue(saved.json()["data"]["hasSmtpPassword"])
            self.assertNotIn("smtp-secret", saved.text)
            body["smtpPassword"] = ""
            self.assertTrue((await client.post("/email/setting/smtp/upsert", json=body, headers=headers)).json()["data"]["hasSmtpPassword"])
            bad = await client.post("/email/setting/smtp/upsert", json={**body, "fromAddress": "not-an-email"}, headers=headers)
            self.assertEqual(bad.status_code, 400)
            self.assertEqual((await client.post("/email/setting/smtp/delete", json={}, headers=headers)).json()["code"], 200)
            self.assertIsNone((await client.get("/email/setting/smtp/get", headers=headers)).json()["data"])

    async def test_registration_creates_milvus_collection_and_can_login(self) -> None:
        import httpx

        user = f"test_{uuid4().hex[:10]}"
        async with httpx.AsyncClient(base_url=os.environ["LLM_PLATFORM_TEST_API_URL"], timeout=30) as client:
            response = await client.post("/user/register", json={
                "user_id": user, "user_password": "test-password", "company_name": user,
                "email_address": f"{user}@example.test", "lang": "ko",
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["code"], 200)
            login = await client.post("/user/login", json={"user_id": user, "user_password": "test-password"})
            self.assertEqual(login.json()["code"], 200)
            self.assertTrue(login.json()["data"]["accessToken"])

    async def test_proxy_mcp_and_exporter_boot_without_vendor_credentials(self) -> None:
        import httpx

        async with httpx.AsyncClient(timeout=15) as client:
            schema = await client.get(os.environ["LLM_PLATFORM_TEST_PROXY_URL"] + "/openapi.json")
            self.assertEqual(schema.status_code, 200)
            self.assertIn("/llm/embeddings", schema.json()["paths"])
            tools = await client.post(os.environ["LLM_PLATFORM_TEST_MCP_URL"], headers={
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            }, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
            self.assertEqual(tools.status_code, 200)
            self.assertIn('"tools"', tools.text)
            metrics = await client.get(os.environ["LLM_PLATFORM_TEST_EXPORTER_URL"] + "/metrics")
            self.assertEqual(metrics.status_code, 200)
            self.assertIn("container_info{", metrics.text)
            self.assertNotIn("# Error", metrics.text)
