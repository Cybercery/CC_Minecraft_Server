import os
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

import tempfile
test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
test_db_path = test_db_file.name
test_db_file.close()

os.environ["DB_PATH"] = test_db_path
os.environ["MINIO_ROOT_USER"] = "testadmin"
os.environ["MINIO_ROOT_PASSWORD"] = "testpassword123"
os.environ["RCON_PASSWORD"] = "secret123"

from backend.main import app
from backend.database import init_db

class TestPhase2(unittest.TestCase):
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

    @patch("backend.routes.server.docker_service.get_status")
    @patch("backend.routes.server.rcon_service.get_player_list")
    def test_server_status_running(self, mock_player_list, mock_status):
        mock_status.return_value = {
            "status": "running",
            "running": True,
            "container_id": "abc123456789",
            "name": "cloud-minecraft",
            "image": "itzg/minecraft-server:latest"
        }
        mock_player_list.return_value = {
            "raw": "There are 2 of a max of 20 players online: Alex, Steve",
            "online_count": 2,
            "players": ["Alex", "Steve"]
        }

        response = self.client.get("/server/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "running")
        self.assertTrue(data["running"])
        self.assertEqual(data["players_online"], 2)
        self.assertEqual(data["players"], ["Alex", "Steve"])

    @patch("backend.routes.server.docker_service.start_server")
    def test_start_server(self, mock_start):
        mock_start.return_value = {"message": "Server started", "status": "running"}
        response = self.client.post("/server/start")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "running")

    @patch("backend.routes.server.docker_service.stop_server")
    def test_stop_server(self, mock_stop):
        mock_stop.return_value = {"message": "Server stopped", "status": "exited"}
        response = self.client.post("/server/stop")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "exited")

    @patch("backend.routes.server.docker_service.restart_server")
    def test_restart_server(self, mock_restart):
        mock_restart.return_value = {"message": "Server restarted", "status": "running"}
        response = self.client.post("/server/restart")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "running")

    @patch("backend.routes.server.docker_service.get_logs")
    def test_get_logs(self, mock_logs):
        mock_logs.return_value = ["[INFO] Starting server", "[INFO] Done!"]
        response = self.client.get("/server/logs?tail=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["logs"], ["[INFO] Starting server", "[INFO] Done!"])

    @patch("backend.routes.server.rcon_service.execute_command")
    def test_execute_rcon_command(self, mock_rcon):
        mock_rcon.return_value = "Set time to 1000"
        response = self.client.post("/server/rcon", json={"command": "time set day"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["response"], "Set time to 1000")

    def test_execute_rcon_empty_command(self):
        response = self.client.post("/server/rcon", json={"command": "   "})
        self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main()
