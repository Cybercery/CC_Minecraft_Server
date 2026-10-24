# Backup, Recovery, and Disaster Recovery Specification

This document details the architecture, cryptographic verification, automated retention, and restoration workflows of the Cloud Minecraft Management Platform.

---

## 1. Backup Strategy Overview

World state data on Minecraft servers is prone to corruption from unexpected power failures, out-of-memory container crashes, or accidental player griefing. The backup engine guarantees recovery point objectives (RPO < 6 hours) and recovery time objectives (RTO < 3 minutes) using the following workflow:

1. **RCON World Flush**: Synchronizes in-memory chunk data to disk before archiving.
2. **Deterministic Archival**: Packages the world directory using gzip-compressed tar (`.tar.gz`).
3. **Cryptographic Checksumming**: Computes a SHA-256 integrity hash over the archive payload.
4. **S3 Object Upload**: Streams the archive to MinIO S3-compatible storage.
5. **Retention Enforcement**: Purges oldest backup archives when count exceeds `BACKUP_RETENTION_COUNT`.

---

## 2. Backup Workflow Sequence

```
[Operator/Scheduler]
        |
        v
+------------------+  1. POST /backups
| FastAPI Backend  |-------------------------+
+------------------+                         |
        |                                    |
        | 2. save-off & save-all flush       |
        v                                    |
+------------------+                         |
|  PaperMC Server  |                         |
+------------------+                         |
        |                                    |
        | 3. Chunks committed to disk        |
        v                                    |
+------------------+                         |
| Filesystem World |                         |
+------------------+                         |
        |                                    |
        | 4. Tar & Gzip Compress             |
        v                                    |
+------------------+                         |
| Archive (.tar.gz)|                         |
+------------------+                         |
        |                                    |
        | 5. Compute SHA-256                 |
        v                                    |
+------------------+                         |
|   SHA-256 Hash   |                         |
+------------------+                         |
        |                                    v
        | 6. S3 PutObject            7. INSERT INTO backups
        v                                    v
+------------------+                +------------------+
|   MinIO Bucket   |                | SQLite Database  |
+------------------+                +------------------+
        |                                    |
        +------------------+-----------------+
                           |
                           v
              8. Enforce Retention Limit
```

### 2.1 RCON Coordination Details
If world files are copied while the Minecraft server writes chunks, the resulting archive may contain half-written chunks (chunk tearing).
To ensure 100% data consistency:
```python
# storage/backup.py
rcon.send_command("save-off")          # Disables automatic background world saving
rcon.send_command("save-all flush")    # Forces all queued dirty chunks to sync to disk
# ... perform tar compression ...
rcon.send_command("save-on")           # Re-enables automatic background world saving
```
If RCON is temporarily unreachable (e.g. server booting), the backup system falls back to a cold file-level snapshot and logs an audit warning.

---

## 3. Database Schema

Table name: `backups`

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Backup record sequence ID |
| `filename` | TEXT NOT NULL | Local archive filename (e.g., `backup_20261024_103000.tar.gz`) |
| `s3_key` | TEXT NOT NULL | S3 storage key path (e.g., `backups/backup_20261024_103000.tar.gz`) |
| `file_size` | INTEGER NOT NULL | Exact archive size in bytes |
| `sha256` | TEXT NOT NULL | SHA-256 cryptographic hexadecimal digest |
| `trigger_type` | TEXT NOT NULL | Trigger origin (`manual`, `scheduled`, `pre_restore`) |
| `created_at` | TEXT NOT NULL | ISO-8601 UTC creation timestamp |

---

## 4. Restoration Protocol

World restoration is a privileged operation restricted to the `Administrator` role (`POST /backups/{id}/restore`).

### 4.1 Safety Checks Prior to Decompression
1. **Pre-Restore Safety Snapshot**: An automatic snapshot (`trigger_type: pre_restore`) of the current world is generated before modifying files on disk.
2. **SHA-256 Integrity Verification**: The archive is streamed from MinIO S3, and its SHA-256 checksum is computed. If the digest does not match the database record, restoration is aborted immediately with a `400 Bad Request`.
3. **Path Traversal Sanitization**: Every file entry inside the tar archive is validated. Any member containing `../`, leading slashes `/`, or resolving outside the target world directory is rejected.

### 4.2 Restoration Execution Steps
1. The Minecraft server container is stopped gracefully via Docker API.
2. The existing world data directory is emptied.
3. The verified backup archive is extracted into the world directory.
4. The Minecraft server container is restarted.
5. An audit log entry (`action: backup_restore`) is committed to SQLite.

---

## 5. Automated Retention Policy

When a new backup completes successfully:
1. The system queries all records from the `backups` table ordered by `created_at ASC`.
2. If `total_count > BACKUP_RETENTION_COUNT` (default: 10):
   - The oldest `total_count - BACKUP_RETENTION_COUNT` backups are identified.
   - For each expired backup, `s3.delete_object(Bucket=..., Key=...)` purges the archive from MinIO S3.
   - The corresponding record is deleted from the SQLite `backups` table.
   - A retention purge event is logged to the audit trail.
