import os
import unittest
from fastapi.testclient import TestClient
import tempfile

test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
test_db_path = test_db_file.name
test_db_file.close()

os.environ["DB_PATH"] = test_db_path
os.environ["PLUGIN_API_KEY"] = "test-plugin-secret-key-12345"
os.environ["CODE_HMAC_SECRET"] = "test-hmac-secret-67890"

from backend.main import app
from backend.database import init_db

class TestPhase4(unittest.TestCase):
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
        self.user_headers = {"Authorization": "Bearer mock:user_p4:user4@example.com"}
        self.plugin_headers = {"X-Plugin-Api-Key": "test-plugin-secret-key-12345"}
        self.invalid_plugin_headers = {"X-Plugin-Api-Key": "wrong-key"}

    def test_user_minecraft_link_flow(self):
        # 1. User starts with no linked account
        res_link = self.client.get("/minecraft/link", headers=self.user_headers)
        self.assertEqual(res_link.status_code, 200)
        self.assertFalse(res_link.json()["linked"])

        # 2. User generates a verification code
        res_code = self.client.post("/minecraft/verification-code", headers=self.user_headers)
        self.assertEqual(res_code.status_code, 200)
        code_data = res_code.json()
        code = code_data["code"]
        self.assertEqual(len(code), 6)

        # 3. Plugin tries to verify with invalid key -> 401
        res_bad_key = self.client.post(
            "/minecraft/plugin/verify",
            headers=self.invalid_plugin_headers,
            json={
                "code": code,
                "minecraft_uuid": "069a79f4-44e9-4726-a5be-fca90e38aaf5",
                "minecraft_username": "Notch"
            }
        )
        self.assertEqual(res_bad_key.status_code, 401)

        # 4. Plugin queries unlinked player -> linked: False
        res_player = self.client.get(
            "/minecraft/plugin/player/069a79f4-44e9-4726-a5be-fca90e38aaf5",
            headers=self.plugin_headers
        )
        self.assertEqual(res_player.status_code, 200)
        self.assertFalse(res_player.json()["linked"])

        # 5. Plugin submits valid verification code
        res_verify = self.client.post(
            "/minecraft/plugin/verify",
            headers=self.plugin_headers,
            json={
                "code": code,
                "minecraft_uuid": "069a79f4-44e9-4726-a5be-fca90e38aaf5",
                "minecraft_username": "Notch"
            }
        )
        self.assertEqual(res_verify.status_code, 200)
        self.assertTrue(res_verify.json()["success"])

        # 6. Reusing same code fails
        res_reuse = self.client.post(
            "/minecraft/plugin/verify",
            headers=self.plugin_headers,
            json={
                "code": code,
                "minecraft_uuid": "069a79f4-44e9-4726-a5be-fca90e38aaf5",
                "minecraft_username": "Notch"
            }
        )
        self.assertEqual(res_reuse.status_code, 400)

        # 7. Plugin queries player now -> linked: True, verified: True
        res_player_after = self.client.get(
            "/minecraft/plugin/player/069a79f4-44e9-4726-a5be-fca90e38aaf5",
            headers=self.plugin_headers
        )
        self.assertEqual(res_player_after.status_code, 200)
        self.assertTrue(res_player_after.json()["verified"])
        self.assertEqual(res_player_after.json()["username"], "Notch")

        # 8. User queries link status on web -> linked: True
        res_user_link = self.client.get("/minecraft/link", headers=self.user_headers)
        self.assertEqual(res_user_link.status_code, 200)
        self.assertTrue(res_user_link.json()["linked"])
        self.assertEqual(res_user_link.json()["minecraft_username"], "Notch")

        # 9. User unlinks account
        res_unlink = self.client.delete("/minecraft/link", headers=self.user_headers)
        self.assertEqual(res_unlink.status_code, 200)

        # 10. Check again -> linked: False
        res_check = self.client.get("/minecraft/link", headers=self.user_headers)
        self.assertEqual(res_check.status_code, 200)
        self.assertFalse(res_check.json()["linked"])

if __name__ == "__main__":
    unittest.main()
