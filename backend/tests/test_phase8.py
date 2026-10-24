import os
import unittest
from fastapi.testclient import TestClient
import tempfile

test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
test_db_path = test_db_file.name
test_db_file.close()

os.environ["DB_PATH"] = test_db_path
os.environ["CPU_ALERT_THRESHOLD"] = "75.0"
os.environ["MEM_ALERT_THRESHOLD"] = "80.0"
os.environ["DISK_ALERT_THRESHOLD"] = "85.0"

from backend.main import app
from backend.database import init_db

class TestPhase8(unittest.TestCase):
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

    def test_security_headers_present(self):
        # Health check response must contain hardening headers
        response = self.client.get("/health")
        self.assertIn("x-content-type-options", response.headers)
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertIn("x-frame-options", response.headers)
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertIn("strict-transport-security", response.headers)

    def test_alert_evaluation_and_audit(self):
        from monitoring.alerts import alert_service

        # Breach CPU and RAM
        mock_metrics = {
            "cpu_percent": 88.5,
            "memory_percent": 82.0,
            "disk_percent": 40.0
        }

        alerts = alert_service.evaluate_metrics(mock_metrics)
        self.assertEqual(len(alerts), 2)
        alert_types = [a["alert_type"] for a in alerts]
        self.assertIn("cpu_high", alert_types)
        self.assertIn("memory_high", alert_types)

        # Retrieve recorded alerts
        unack = alert_service.get_alerts(unacknowledged_only=True)
        self.assertGreaterEqual(len(unack), 2)

        # Acknowledge first alert
        first_id = unack[0]["id"]
        ack_success = alert_service.acknowledge_alert(first_id, user_uid="admin_tester")
        self.assertTrue(ack_success)

        # Check audit log recorded alert triggering and acknowledgment
        from backend.services.audit_service import audit_service
        logs = audit_service.list_logs(limit=10)
        actions = [log["action"] for log in logs]
        self.assertIn("alert_triggered", actions)
        self.assertIn("alert_acknowledged", actions)

if __name__ == "__main__":
    unittest.main()
