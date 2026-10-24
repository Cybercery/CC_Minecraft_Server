# Progress

## Phase 1: Project Setup and Docker Infrastructure
- Created repository skeleton, `.gitignore`, `.dockerignore`, `.env.example`, and environment generator scripts.
- Implemented `docker-compose.yml` with MinIO / S3Mock, MinIO initialization, and backend services.
- Created `backend/Dockerfile` with non-root security context.
- Configured SQLite database migrations (`schema_version`) and MinIO client health checks.
- Implemented `/health` endpoint returning database schema version and MinIO health status.
- Added automated acceptance tests in `backend/tests/test_phase1.py` verifying `/health` and database migration.
## Phase 2: Minecraft Deployment and Management
- Added Paper Minecraft service (`itzg/minecraft-server`) to `docker-compose.yml` with RCON and health check configuration.
- Implemented `backend/services/docker_service.py` to handle container lifecycle (status, start, stop, restart, logs).
- Implemented `backend/services/rcon_service.py` using `mcrcon` for remote command execution and online player queries.
- Built server management REST API in `backend/routes/server.py` (`/server/status`, `/server/start`, `/server/stop`, `/server/restart`, `/server/logs`, `/server/rcon`).
- Mounted server routes into FastAPI application in `backend/main.py`.
- Added test suite `backend/tests/test_phase2.py` passing all 7 tests for server control, player query, and RCON endpoints.

## Phase 3: Firebase Authentication and IAM/RBAC
- Implemented `backend/auth.py` providing Firebase token verification, dev mock token support, and automatic bootstrap Administrator provisioning (`BOOTSTRAP_ADMIN_EMAIL`).
- Defined 3-tier Role-Based Access Control matrix (Administrator, Operator, User) in `backend/permissions.py`.
- Added database schema migration version 2 for `users` and `audit_logs` tables in `backend/database.py`.
- Created structured audit logging service `backend/services/audit_service.py` to persist administrative, authentication, and execution events.
- Created `backend/routes/auth.py` (`/auth/me`, `/auth/audit-logs`) and `backend/routes/users.py` (`/users`, `/users/{uid}/role`) with self-demote lockout prevention.
- Retrofitted RBAC permission dependencies and audit logging across all Phase 2 server endpoints.
- Added comprehensive acceptance test suite in `backend/tests/test_phase3.py` (all 5 tests passing, whole test suite of 14 tests passing).

## Phase 4: Minecraft-to-Web Verification Plugin
- Added database schema migration version 3 for `minecraft_links` and `verification_sessions` in `backend/database.py`.
- Built `backend/services/verification_service.py` featuring SHA-256 HMAC verification code hashing, 6-character uppercase codes, TTL expiration, single-use enforcement, and link management.
- Implemented `/minecraft/verification-code`, `/minecraft/link`, `/minecraft/plugin/verify`, and `/minecraft/plugin/player/{uuid}` in `backend/routes/minecraft.py`.
- Scaffolded Java 21 Paper plugin in `minecraft-plugin/` with `plugin.yml`, `config.yml`, event listeners (join, move freeze, block break/place cancellation, blindness effect, chat suppression), and `/verify <code>` command.
- Provided build script `scripts/build-plugin.sh` supporting native Maven and Docker builds.
- Added acceptance test in `backend/tests/test_phase4.py` (all 15 tests across phases 1–4 passing).

## Phase 5: MinIO Storage and Automated Backups
- Added database schema migration version 4 for `backups` table tracking S3 keys, file sizes, SHA256 checksums, and trigger types.
- Implemented `storage/backup.py` with RCON save flush coordination, `.tar.gz` gzip compression, SHA256 integrity calculation, and MinIO S3 upload.
- Implemented `storage/restore.py` verifying SHA256 checksums against corruption, preventing tar path-traversal attacks, and safely controlling Minecraft server downtime during restoration.
- Implemented `storage/retention.py` enforcing backup count limits (`BACKUP_RETENTION_COUNT`) by deleting old backup archives from MinIO and records from SQLite.
- Configured automated cron scheduler in `storage/scheduler.py` via APScheduler.
- Mounted `/backups` routes in `backend/routes/backups.py` with RBAC permissions (`backup:read`, `backup:create`, `backup:restore`).
- Added test suite `backend/tests/test_phase5.py` (all 18 tests across phases 1–5 passing).
