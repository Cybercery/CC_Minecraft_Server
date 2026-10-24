import os
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import tempfile
import io

test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
test_db_path = test_db_file.name
test_db_file.close()

os.environ["DB_PATH"] = test_db_path
os.environ["BACKUP_RETENTION_COUNT"] = "2"

from backend.main import app
from backend.database import init_db

class TestPhase5(unittest.TestCase):
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
        self.admin_headers = {"Authorization": "Bearer mock:admin_p5:admin@example.com"}
        self.user_headers = {"Authorization": "Bearer mock:user_p5:user5@example.com"}

    @patch("storage.backup.get_minio_client")
    @patch("storage.backup.rcon_service.execute_command")
    def test_backup_create_and_list(self, mock_rcon, mock_minio_factory):
        mock_minio = MagicMock()
        mock_minio_factory.return_value = mock_minio

        # 1. Regular user forbidden from creating backup
        res_denied = self.client.post("/backups/create", headers=self.user_headers)
        self.assertEqual(res_denied.status_code, 403)

        # 2. Admin creates manual backup
        res_create = self.client.post("/backups/create", headers=self.admin_headers)
        self.assertEqual(res_create.status_code, 200)
        data = res_create.json()
        self.assertEqual(data["status"], "completed")
        self.assertTrue(data["filename"].endswith(".tar.gz"))
        self.assertTrue(mock_minio.put_object.called)

        # 3. Regular user forbidden from reading backups
        res_list_user = self.client.get("/backups", headers=self.user_headers)
        self.assertEqual(res_list_user.status_code, 403)

        # 4. Admin lists backups
        res_list = self.client.get("/backups", headers=self.admin_headers)
        self.assertEqual(res_list.status_code, 200)
        backups = res_list.json()
        self.assertGreaterEqual(len(backups), 1)
        self.assertEqual(backups[0]["id"], data["id"])

    @patch("storage.restore.get_minio_client")
    @patch("storage.restore.docker_service.get_status")
    @patch("storage.restore.docker_service.stop_server")
    @patch("storage.restore.docker_service.start_server")
    @patch("storage.backup.BackupService.calculate_sha256")
    def test_restore_backup(self, mock_checksum, mock_start, mock_stop, mock_status, mock_minio_factory):
        mock_status.return_value = {"running": True}
        mock_checksum.return_value = "dummy-checksum"

        mock_minio = MagicMock()
        mock_minio_factory.return_value = mock_minio

        # Create a dummy backup entry directly in database
        from backend.database import db_session
        with db_session() as conn:
            cursor = conn.execute(
                """
                INSERT INTO backups (filename, s3_key, size_bytes, checksum_sha256, backup_type, status)
                VALUES ('test_restore.tar.gz', 'backups/test_restore.tar.gz', 100, 'dummy-checksum', 'manual', 'completed')
                """
            )
            backup_id = cursor.lastrowid

        # Make mock download write a valid tar archive to target download path
        def fake_download(bucket, key, target_path):
            import tarfile
            with tarfile.open(target_path, "w:gz") as tar:
                pass

        mock_minio.download_file.side_effect = fake_download

        temp_target = tempfile.mkdtemp()
        try:
            # Regular user cannot restore
            res_denied = self.client.post(
                f"/backups/{backup_id}/restore",
                headers=self.user_headers,
                json={"target_dir": temp_target}
            )
            self.assertEqual(res_denied.status_code, 403)

            # Admin restores
            res_restore = self.client.post(
                f"/backups/{backup_id}/restore",
                headers=self.admin_headers,
                json={"target_dir": temp_target}
            )
            self.assertEqual(res_restore.status_code, 200)
            self.assertTrue(res_restore.json()["success"])
            self.assertTrue(mock_stop.called)
            self.assertTrue(mock_start.called)
        finally:
            import shutil
            shutil.rmtree(temp_target, ignore_errors=True)

    @patch("storage.retention.get_minio_client")
    def test_retention_policy(self, mock_minio_factory):
        mock_minio = MagicMock()
        mock_minio_factory.return_value = mock_minio

        from storage.retention import retention_service
        from backend.database import db_session

        # Insert 3 backups (configured limit is 2)
        with db_session() as conn:
            conn.execute("DELETE FROM backups")
            conn.execute("INSERT INTO backups (filename, s3_key, size_bytes, checksum_sha256, created_at) VALUES ('b1.tar.gz', 'backups/b1.tar.gz', 10, 'c1', '2026-01-01 10:00:00')")
            conn.execute("INSERT INTO backups (filename, s3_key, size_bytes, checksum_sha256, created_at) VALUES ('b2.tar.gz', 'backups/b2.tar.gz', 10, 'c2', '2026-01-01 11:00:00')")
            conn.execute("INSERT INTO backups (filename, s3_key, size_bytes, checksum_sha256, created_at) VALUES ('b3.tar.gz', 'backups/b3.tar.gz', 10, 'c3', '2026-01-01 12:00:00')")

        purged = retention_service.apply_retention(keep_count=2)
        self.assertEqual(len(purged), 1)
        self.assertEqual(purged[0]["filename"], "b1.tar.gz")
        self.assertTrue(mock_minio.delete_object.called)

        with db_session() as conn:
            cursor = conn.execute("SELECT COUNT(*) as cnt FROM backups")
            count = cursor.fetchone()["cnt"]
            self.assertEqual(count, 2)

if __name__ == "__main__":
    unittest.main()
