import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

import tempfile

test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
test_db_path = test_db_file.name
test_db_file.close()

os.environ["DB_PATH"] = test_db_path
os.environ["MINIO_ROOT_USER"] = "testadmin"
os.environ["MINIO_ROOT_PASSWORD"] = "testpassword123"

from backend.main import app
from backend.database import init_db

class TestPhase1(unittest.TestCase):
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

    @patch("backend.main.check_bucket_health")
    def test_health_check_healthy(self, mock_bucket_health):
        mock_bucket_health.return_value = True
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertGreaterEqual(data["db_schema_version"], 1)
        self.assertTrue(data["minio_healthy"])

    @patch("backend.main.check_bucket_health")
    def test_health_check_minio_unhealthy(self, mock_bucket_health):
        mock_bucket_health.return_value = False
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 503)
        self.assertIn("MinIO degraded", response.json()["detail"])

if __name__ == "__main__":
    unittest.main()
