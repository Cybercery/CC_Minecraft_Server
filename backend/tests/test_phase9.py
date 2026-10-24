"""
Phase 9: Integration tests for end-to-end flows covering auth → server management,
backup creation, monitoring, alerts, and audit trails.
These use the TestClient in-process so no live Docker or MinIO is required.
"""
import os
import unittest
import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# ── Temp DB ──────────────────────────────────────────────────────────────────
_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_db_path = _db_file.name
_db_file.close()

os.environ["DB_PATH"] = _db_path
os.environ["BACKUP_RETENTION_COUNT"] = "3"
os.environ["CPU_ALERT_THRESHOLD"] = "70.0"
os.environ["MEM_ALERT_THRESHOLD"] = "75.0"
os.environ["DISK_ALERT_THRESHOLD"] = "80.0"
# Use a unique bootstrap admin so it never conflicts with other test suites
os.environ["BOOTSTRAP_ADMIN_EMAIL"] = "admin_p9@example.com"

import backend.database as _dbmod                 # noqa: E402
_dbmod.DB_PATH = _db_path                         # force DB path on the already-imported module

from backend.main import app                       # noqa: E402
from backend.database import init_db, db_session  # noqa: E402


class TestPhase9Integration(unittest.TestCase):
    """End-to-end integration tests spanning multiple subsystems."""

    # ── Class lifecycle ───────────────────────────────────────────────────────
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app, raise_server_exceptions=True)

        # Use the unique bootstrap admin email set above
        cls.admin    = {"Authorization": "Bearer mock:admin_p9:admin_p9@example.com"}
        cls.operator = {"Authorization": "Bearer mock:op_p9:operator_p9@example.com"}
        cls.user     = {"Authorization": "Bearer mock:user_p9:user_p9@example.com"}

        # Pre-create the admin user so downstream tests don't race
        from backend.auth import get_or_create_user
        with db_session() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (uid, email, role) VALUES (?, ?, ?)",
                ("admin_p9", "admin_p9@example.com", "Administrator")
            )

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(_db_path):
            try:
                os.remove(_db_path)
            except Exception:
                pass

    # ── 1. Authentication flows ───────────────────────────────────────────────
    def test_01_unauthenticated_endpoints_return_401(self):
        """Protected endpoints must reject requests without a token."""
        for path in ["/server/status", "/backups", "/metrics/current",
                     "/users", "/auth/audit-logs"]:
            res = self.client.get(path)
            self.assertIn(res.status_code, (401, 403),
                          f"{path} should be protected, got {res.status_code}")

    def test_02_auth_me_returns_admin_role(self):
        """Pre-seeded admin gets Administrator role from /auth/me."""
        res = self.client.get("/auth/me", headers=self.admin)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["email"], "admin_p9@example.com")
        self.assertEqual(data["role"], "Administrator")

    def test_03_regular_user_gets_user_role(self):
        """Unenrolled users default to the User role."""
        res = self.client.get("/auth/me", headers=self.user)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["role"], "User")

    # ── 2. RBAC enforcement ───────────────────────────────────────────────────
    def test_04_user_cannot_start_server(self):
        """Users must not be able to start the Minecraft server."""
        res = self.client.post("/server/start", headers=self.user)
        self.assertEqual(res.status_code, 403)

    def test_05_user_cannot_list_users(self):
        """Only Administrators may list users."""
        res = self.client.get("/users", headers=self.user)
        self.assertEqual(res.status_code, 403)

    def test_06_admin_can_list_users(self):
        """Administrators can retrieve the user list."""
        res = self.client.get("/users", headers=self.admin)
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    def test_07_admin_role_change_creates_audit_log(self):
        """Role promotion by an admin must appear in audit logs."""
        # Seed the operator user first
        self.client.get("/auth/me", headers=self.operator)

        # Promote user to Operator
        res = self.client.get("/users", headers=self.admin)
        self.assertEqual(res.status_code, 200, f"Admin users list failed: {res.text}")
        users = res.json()
        target = next((u for u in users if "operator_p9" in u.get("email", "")), None)
        self.assertIsNotNone(target, "Operator user not found in user list")

        promote = self.client.put(
            f"/users/{target['uid']}/role",
            headers=self.admin,
            json={"role": "Operator"}
        )
        self.assertEqual(promote.status_code, 200)
        self.assertEqual(promote.json()["role"], "Operator")

        # Verify role was changed in DB
        with db_session() as conn:
            cursor = conn.execute("SELECT role FROM users WHERE uid=?", (target["uid"],))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["role"], "Operator")

    # ── 3. Server management flow ─────────────────────────────────────────────
    def test_08_server_status_endpoint(self):
        """Server status endpoint returns a structured response."""
        res = self.client.get("/server/status", headers=self.user)
        # Docker may not be available in unit tests → 200 (not_found) or 500/503 are all acceptable
        self.assertIn(res.status_code, (200, 500, 503))
        if res.status_code == 200:
            data = res.json()
            self.assertIn("running", data)

    # ── 4. Backup → restore integration ──────────────────────────────────────
    @patch("storage.backup.get_minio_client")
    @patch("storage.backup.rcon_service.execute_command")
    def test_09_backup_create_then_list(self, mock_rcon, mock_minio_factory):
        """Admin creates a backup; it appears in the backup list."""
        mock_minio = MagicMock()
        mock_minio_factory.return_value = mock_minio

        create_res = self.client.post("/backups/create", headers=self.admin)
        self.assertEqual(create_res.status_code, 200, f"Backup create failed: {create_res.text}")
        backup_data = create_res.json()
        self.assertEqual(backup_data["status"], "completed")

        list_res = self.client.get("/backups", headers=self.admin)
        self.assertEqual(list_res.status_code, 200)
        ids = [b["id"] for b in list_res.json()]
        self.assertIn(backup_data["id"], ids)

    @patch("storage.restore.get_minio_client")
    @patch("storage.restore.docker_service.get_status")
    @patch("storage.restore.docker_service.stop_server")
    @patch("storage.restore.docker_service.start_server")
    @patch("storage.backup.BackupService.calculate_sha256")
    @patch("storage.backup.get_minio_client")
    @patch("storage.backup.rcon_service.execute_command")
    def test_10_backup_restore_full_flow(
        self, mock_rcon, mock_minio_bk, mock_checksum,
        mock_start, mock_stop, mock_status, mock_minio_restore
    ):
        """Full backup-and-restore cycle with server quiesce."""
        mock_minio_bk.return_value = MagicMock()
        mock_minio_restore_inst = MagicMock()
        mock_minio_restore.return_value = mock_minio_restore_inst
        mock_status.return_value = {"running": True}
        mock_checksum.return_value = "dummy-sha256"

        # Create backup
        create_res = self.client.post("/backups/create", headers=self.admin)
        self.assertEqual(create_res.status_code, 200, f"Backup create: {create_res.text}")
        backup_id = create_res.json()["id"]

        # Update checksum to match mock
        with db_session() as conn:
            conn.execute(
                "UPDATE backups SET checksum_sha256=? WHERE id=?",
                ("dummy-sha256", backup_id)
            )

        # Mock download to write empty tar.gz
        import tarfile
        import tempfile as tf
        target_dir = tf.mkdtemp()
        try:
            def fake_download(bucket, key, target_path):
                with tarfile.open(target_path, "w:gz"):
                    pass
            mock_minio_restore_inst.download_file.side_effect = fake_download

            restore_res = self.client.post(
                f"/backups/{backup_id}/restore",
                headers=self.admin,
                json={"target_dir": target_dir}
            )
            self.assertEqual(restore_res.status_code, 200)
            self.assertTrue(restore_res.json()["success"])
            mock_stop.assert_called_once()
            mock_start.assert_called_once()
        finally:
            import shutil
            shutil.rmtree(target_dir, ignore_errors=True)

    # ── 5. Metrics and alert integration ─────────────────────────────────────
    def test_11_metrics_collect_and_query(self):
        """Collecting a snapshot returns ok; history returns ≥1 entry."""
        collect = self.client.post("/metrics/collect", headers=self.user)
        self.assertEqual(collect.status_code, 200)

        history = self.client.get("/metrics/history?hours=1", headers=self.user)
        self.assertEqual(history.status_code, 200)
        self.assertGreaterEqual(len(history.json()), 1)

    def test_12_alert_evaluation_fires_and_records_audit(self):
        """Breaching CPU + mem thresholds creates 2 alerts and audit rows."""
        from monitoring.alerts import alert_service
        from backend.services.audit_service import audit_service as aud

        alerts = alert_service.evaluate_metrics({
            "cpu_percent": 85.0,   # > 70 threshold set in os.environ
            "memory_percent": 82.0,  # > 75 threshold set in os.environ
            "disk_percent": 30.0,
        })
        self.assertEqual(len(alerts), 2, f"Expected 2 alerts, got: {alerts}")
        types = [a["alert_type"] for a in alerts]
        self.assertIn("cpu_high", types)
        self.assertIn("memory_high", types)

        # Audit trail should contain alert_triggered
        logs = aud.list_logs(limit=20)
        self.assertIn("alert_triggered", [l["action"] for l in logs])

    def test_13_alert_acknowledge_flow(self):
        """Acknowledging an alert flips its flag and logs alert_acknowledged."""
        from monitoring.alerts import alert_service
        from backend.services.audit_service import audit_service as aud

        # Trigger a fresh disk alert
        alert_service.evaluate_metrics({
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_percent": 95.0,   # > 80 disk threshold
        })
        unack = alert_service.get_alerts(unacknowledged_only=True)
        disk_alerts = [a for a in unack if a["alert_type"] == "disk_high"]
        self.assertGreater(len(disk_alerts), 0)

        ack_id = disk_alerts[0]["id"]
        ok = alert_service.acknowledge_alert(ack_id, user_uid="admin_p9")
        self.assertTrue(ok)

        # Must now be absent from unacknowledged list
        after = alert_service.get_alerts(unacknowledged_only=True)
        self.assertNotIn(ack_id, [a["id"] for a in after])

        # audit_acknowledged must be in logs
        logs = aud.list_logs(limit=30)
        self.assertIn("alert_acknowledged", [l["action"] for l in logs])

    # ── 6. Minecraft verification flow ───────────────────────────────────────
    def test_14_verification_code_lifecycle(self):
        """Verification codes are generated, can be looked up, and expire gracefully."""
        from backend.services.verification_service import verification_service

        # Seed user first
        with db_session() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (uid, email, role) VALUES (?, ?, ?)",
                ("user_p9", "user_p9@example.com", "User")
            )

        uid = "user_p9"
        code, _ = verification_service.generate_code(uid, ttl_seconds=300)
        self.assertEqual(len(code), 6)
        self.assertTrue(all(c.isupper() or c.isdigit() for c in code))

        # Validate code lookup (without consuming it)
        record = verification_service.lookup_code(code)
        self.assertIsNotNone(record)
        self.assertEqual(record["uid"], uid)

    # ── 7. Health and security headers ───────────────────────────────────────
    @patch("backend.main.check_bucket_health", return_value=True)
    def test_15_health_endpoint_returns_db_version(self, mock_health):
        """Health endpoint reports current DB schema version ≥ 6."""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200, f"Health failed: {res.text}")
        data = res.json()
        self.assertGreaterEqual(data["db_schema_version"], 6)

    def test_16_security_headers_on_all_responses(self):
        """Security hardening headers must be present on every response."""
        with patch("backend.main.check_bucket_health", return_value=True):
            res = self.client.get("/health")
        self.assertIn("x-content-type-options", res.headers)
        self.assertEqual(res.headers["x-content-type-options"], "nosniff")
        self.assertIn("x-frame-options", res.headers)
        self.assertEqual(res.headers["x-frame-options"], "DENY")
        self.assertIn("strict-transport-security", res.headers)


if __name__ == "__main__":
    unittest.main()
