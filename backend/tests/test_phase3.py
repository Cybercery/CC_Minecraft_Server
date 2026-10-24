import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

import tempfile
test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
test_db_path = test_db_file.name
test_db_file.close()

os.environ["DB_PATH"] = test_db_path
os.environ["BOOTSTRAP_ADMIN_EMAIL"] = "admin@example.com"

from backend.main import app
from backend.database import init_db

class TestPhase3(unittest.TestCase):
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
        self.admin_headers = {"Authorization": "Bearer mock:admin_1:admin@example.com"}
        self.user_headers = {"Authorization": "Bearer mock:user_1:user1@example.com"}
        self.other_user_headers = {"Authorization": "Bearer mock:user_2:user2@example.com"}

    def test_unauthorized_access(self):
        # Missing auth header
        res = self.client.get("/auth/me")
        self.assertEqual(res.status_code, 401)

    def test_bootstrap_admin_provisioning(self):
        # First login with bootstrap admin email gets Administrator role
        res = self.client.get("/auth/me", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["email"], "admin@example.com")
        self.assertEqual(data["role"], "Administrator")

    def test_standard_user_provisioning(self):
        # Non-admin email gets User role
        res = self.client.get("/auth/me", headers=self.user_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["email"], "user1@example.com")
        self.assertEqual(data["role"], "User")

    def test_user_management_rbac(self):
        # Ensure user_2 is provisioned
        self.client.get("/auth/me", headers=self.other_user_headers)

        # Standard user cannot list users
        res_denied = self.client.get("/users", headers=self.user_headers)
        self.assertEqual(res_denied.status_code, 403)

        # Admin can list users
        res_list = self.client.get("/users", headers=self.admin_headers)
        self.assertEqual(res_list.status_code, 200)
        users = res_list.json()
        self.assertGreaterEqual(len(users), 2)

        # Standard user cannot change roles
        res_change_denied = self.client.put(
            "/users/user_2/role",
            json={"role": "Operator"},
            headers=self.user_headers
        )
        self.assertEqual(res_change_denied.status_code, 403)

        # Admin can promote user_2 to Operator
        res_change = self.client.put(
            "/users/user_2/role",
            json={"role": "Operator"},
            headers=self.admin_headers
        )
        self.assertEqual(res_change.status_code, 200)
        self.assertEqual(res_change.json()["role"], "Operator")

        # Admin cannot demote self
        res_self_demote = self.client.put(
            "/users/admin_1/role",
            json={"role": "User"},
            headers=self.admin_headers
        )
        self.assertEqual(res_self_demote.status_code, 400)

    def test_audit_logs(self):
        from backend.services.audit_service import audit_service
        audit_service.log_action(
            action="test_action",
            resource="system",
            status="success",
            uid="admin_1",
            email="admin@example.com"
        )

        # Regular user cannot read audit logs
        res_denied = self.client.get("/auth/audit-logs", headers=self.user_headers)
        self.assertEqual(res_denied.status_code, 403)

        # Admin can read audit logs
        res = self.client.get("/auth/audit-logs", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        logs = res.json()
        self.assertIsInstance(logs, list)
        self.assertGreaterEqual(len(logs), 1)
        actions = [log["action"] for log in logs]
        self.assertIn("test_action", actions)

if __name__ == "__main__":
    unittest.main()
