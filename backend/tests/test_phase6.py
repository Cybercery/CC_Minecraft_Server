import os
import unittest
from fastapi.testclient import TestClient
import tempfile

test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
test_db_path = test_db_file.name
test_db_file.close()

os.environ["DB_PATH"] = test_db_path

from backend.main import app
from backend.database import init_db

class TestPhase6(unittest.TestCase):
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
        self.user_headers = {"Authorization": "Bearer mock:user_p6:user6@example.com"}

    def test_current_metrics(self):
        res = self.client.get("/metrics/current", headers=self.user_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("cpu_percent", data)
        self.assertIn("memory_percent", data)
        self.assertIn("disk_percent", data)
        self.assertIn("online_players", data)
        self.assertIn("is_running", data)

    def test_trigger_snapshot_and_history(self):
        # Trigger metric snapshot record
        res_snapshot = self.client.post("/metrics/collect", headers=self.user_headers)
        self.assertEqual(res_snapshot.status_code, 200)

        # Query history
        res_history = self.client.get("/metrics/history?hours=1", headers=self.user_headers)
        self.assertEqual(res_history.status_code, 200)
        history = res_history.json()
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 1)
        self.assertIn("cpu_percent", history[0])

    def test_metrics_purge(self):
        from monitoring.metrics import metrics_service
        from backend.database import db_session
        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO server_metrics (
                    cpu_percent, memory_bytes, memory_percent,
                    disk_used_bytes, disk_total_bytes, disk_percent,
                    online_players, is_running, timestamp
                ) VALUES (10.0, 1000, 20.0, 5000, 10000, 50.0, 0, 0, '2020-01-01T00:00:00')
                """
            )
        deleted = metrics_service.purge_old_metrics(retention_days=7)
        self.assertGreaterEqual(deleted, 1)

if __name__ == "__main__":
    unittest.main()
