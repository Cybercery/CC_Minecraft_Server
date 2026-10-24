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

## Phase 6: Python Monitoring and Historical Metrics
- Added database schema migration version 5 for `server_metrics` table with index on timestamp in `backend/database.py`.
- Implemented `monitoring/collector.py` capturing system CPU percentage, memory consumption, disk utilization, online player counts via RCON, and container status.
- Implemented `monitoring/metrics.py` providing real-time snapshot reads, historical time-series queries with custom lookback windows, and timestamp-based retention purges.
- Exposed REST API endpoints `/metrics/current`, `/metrics/history`, and `/metrics/collect` in `backend/routes/metrics.py`.
- Added test suite `backend/tests/test_phase6.py` (all 21 tests across phases 1–6 passing).

## Phase 7: React Dashboard and Visualization
- Initialized React 19 + TypeScript + Vite modern web application in `frontend/`.
- Configured Firebase Web SDK supporting both Google OAuth popup authentication and Email/Password sign in.
- Built design system in `frontend/src/index.css` featuring dark-mode glassmorphism cards, Plus Jakarta Sans & JetBrains Mono typography, status badges, and action buttons.
- Implemented modular, role-aware dashboard views:
  - `AuthModal.tsx`: Google and Email/Password authentication.
  - `Sidebar.tsx`: Role-filtered navigation and user profile status.
  - `ServerControl.tsx`: Live state indicator, container start/stop/restart controls, live 4-second auto-refreshing console terminal, and RCON command dispatch.
  - `MonitoringDashboard.tsx`: Telemetry cards (CPU, RAM, Disk, Online players) and historical records table.
  - `BackupsManagement.tsx`: Snapshot creation, MinIO S3 object browser, SHA256 integrity display, and single-click restore.
  - `MinecraftLinking.tsx`: 6-character code generator with TTL expiration and account linking guide.
  - `UserManagement.tsx`: IAM access management table for viewing and assigning Administrator, Operator, and User roles.
  - `AuditLogsViewer.tsx`: Structured log inspection table.
- Added multi-stage `frontend/Dockerfile` with Nginx production serving and integrated `frontend` into `docker-compose.yml`.
- Verified clean production compilation with `npm run build` in `frontend/`.

## Phase 9: Integration Testing and Disaster Recovery
- Created comprehensive end-to-end integration test suite `backend/tests/test_phase9.py` with 16 tests spanning: unauthenticated access checks, RBAC enforcement, admin bootstrap provisioning, role-change audit logging, backup/restore full lifecycle, metrics collection, alert evaluation and acknowledgment, verification code lifecycle, health endpoint, and security headers.
- Fixed `monitoring/alerts.py` threshold reads to be dynamic from `os.environ` (enabling test override of settings singleton).
- Fixed `backend/routes/users.py` to call `audit_service.log_action()` outside the `db_session` block to prevent SQLite WAL lock contention; renamed action to `role_change` for semantic clarity.
- Added `lookup_code()` method to `backend/services/verification_service.py` for non-destructive code inspection.
- Wrote `scripts/integration-test.sh`: runs all Python test suites, optional Docker Compose smoke test, and frontend production build verification.
- Wrote `scripts/dr-drill.sh`: Disaster Recovery drill script covering 6 scenarios — golden backup/restore path, RCON graceful degradation, metrics continuity, alert audit trail, health endpoint resilience, and RBAC boundary enforcement — all via live HTTP calls against the running stack.
- All 38 tests across phases 1–9 passing.
