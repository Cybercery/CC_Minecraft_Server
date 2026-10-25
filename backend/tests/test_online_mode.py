import os
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import tempfile

test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
test_db_path = test_db_file.name
test_db_file.close()

os.environ["DB_PATH"] = test_db_path
os.environ["PLUGIN_API_KEY"] = "test-plugin-key-online-mode"
os.environ["CODE_HMAC_SECRET"] = "test-hmac-key-online-mode"
os.environ["MINECRAFT_ONLINE_MODE"] = "true"

from backend.main import app
from backend.database import init_db, db_session
from backend.services.docker_service import docker_service
from backend.services.verification_service import verification_service
from backend.config import settings

class TestOnlineOfflineMode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
            except Exception:
                pass

    def setUp(self):
        self.client = TestClient(app)
        self.user_headers = {"Authorization": "Bearer mock:user_om1:om1@example.com"}
        self.user2_headers = {"Authorization": "Bearer mock:user_om2:om2@example.com"}
        plugin_key = os.environ.get("PLUGIN_API_KEY") or settings.PLUGIN_API_KEY or "test-plugin-key-online-mode"
        self.plugin_headers = {"X-Plugin-Api-Key": plugin_key}
        verification_service.reset_rate_limits()

    def test_01_default_online_mode_setting(self):
        # By default settings should have MINECRAFT_ONLINE_MODE = True
        self.assertTrue(settings.MINECRAFT_ONLINE_MODE)

    @patch("backend.services.docker_service.docker_service.get_container")
    def test_02_get_online_mode_from_container(self, mock_get_container):
        # When container has ONLINE_MODE=false
        mock_container = MagicMock()
        mock_container.attrs = {"Config": {"Env": ["ONLINE_MODE=false", "EULA=TRUE"]}}
        mock_get_container.return_value = mock_container

        mode = docker_service.get_online_mode()
        self.assertFalse(mode)

        # When container has ONLINE_MODE=true
        mock_container.attrs = {"Config": {"Env": ["ONLINE_MODE=true", "EULA=TRUE"]}}
        mode_online = docker_service.get_online_mode()
        self.assertTrue(mode_online)

    @patch("backend.services.docker_service.docker_service.get_container")
    def test_03_server_status_returns_online_mode(self, mock_get_container):
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_container.id = "1234567890abcdef"
        mock_container.name = "cloud-minecraft"
        mock_container.image.tags = ["itzg/minecraft-server:latest"]
        mock_container.attrs = {"Config": {"Env": ["ONLINE_MODE=false"]}}
        mock_get_container.return_value = mock_container

        res = self.client.get("/server/status", headers=self.user_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("online_mode", data)
        self.assertFalse(data["online_mode"])

    def test_04_server_properties_endpoint_unauthorized(self):
        # No auth header -> 401
        res = self.client.get("/server/properties")
        self.assertEqual(res.status_code, 401)

    @patch("backend.services.docker_service.docker_service.get_container")
    def test_05_server_properties_endpoint_authenticated(self, mock_get_container):
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_container.attrs = {"Config": {"Env": ["ONLINE_MODE=true"]}}
        mock_exec_res = MagicMock()
        mock_exec_res.exit_code = 0
        mock_exec_res.output = b"online-mode=true\nmax-players=20\nenable-rcon=true\nmotd=A Minecraft Server\n"
        mock_container.exec_run.return_value = mock_exec_res
        mock_get_container.return_value = mock_container

        res = self.client.get("/server/properties", headers=self.user_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["source"], "container_filesystem")
        self.assertTrue(data["online_mode"])
        self.assertTrue(data["properties_file_found"])
        self.assertEqual(data["parsed"]["online-mode"], "true")
        self.assertIn("inspect_command_running", data)
        self.assertIn("inspect_command_stopped", data)

    def test_06_verification_code_generation_rate_limit(self):
        # Successfully generate up to 10 codes
        for _ in range(10):
            res = self.client.post("/minecraft/verification-code", headers=self.user_headers)
            self.assertEqual(res.status_code, 200)

        # 11th request in same window should trigger HTTP 429
        res_limit = self.client.post("/minecraft/verification-code", headers=self.user_headers)
        self.assertEqual(res_limit.status_code, 429)

    def test_07_verification_failed_attempts_rate_limit(self):
        target_uuid = "00000000-0000-0000-0000-000000000001"
        # 5 failed attempts with invalid code
        for _ in range(5):
            res = self.client.post(
                "/minecraft/plugin/verify",
                headers=self.plugin_headers,
                json={"code": "BADCOD", "minecraft_uuid": target_uuid, "minecraft_username": "Hacker"}
            )
            self.assertEqual(res.status_code, 400)

        # 6th attempt should be blocked by rate limit
        res_blocked = self.client.post(
            "/minecraft/plugin/verify",
            headers=self.plugin_headers,
            json={"code": "BADCOD", "minecraft_uuid": target_uuid, "minecraft_username": "Hacker"}
        )
        self.assertEqual(res_blocked.status_code, 400)
        self.assertIn("Too many failed verification attempts", res_blocked.json()["detail"])

    def test_08_verification_uuid_conflict_handling(self):
        # User 1 generates code and links offline UUID
        offline_uuid = "11111111-2222-3333-4444-555555555555"
        res_c1 = self.client.post("/minecraft/verification-code", headers=self.user_headers)
        code1 = res_c1.json()["code"]

        res_v1 = self.client.post(
            "/minecraft/plugin/verify",
            headers=self.plugin_headers,
            json={"code": code1, "minecraft_uuid": offline_uuid, "minecraft_username": "DevPlayer"}
        )
        self.assertEqual(res_v1.status_code, 200)

        # User 2 generates code and attempts to link the SAME offline UUID
        res_c2 = self.client.post("/minecraft/verification-code", headers=self.user2_headers)
        code2 = res_c2.json()["code"]

        res_v2 = self.client.post(
            "/minecraft/plugin/verify",
            headers=self.plugin_headers,
            json={"code": code2, "minecraft_uuid": offline_uuid, "minecraft_username": "DevPlayer"}
        )
        self.assertEqual(res_v2.status_code, 400)
        self.assertIn("already linked to another user account", res_v2.json()["detail"])

if __name__ == "__main__":
    unittest.main()
