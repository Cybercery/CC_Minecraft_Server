# Implementation Plan and Task Checklist

## Phase 1: Project setup and Docker infrastructure
- [x] Create repository skeleton (directories, `.gitignore`, `.dockerignore`).
- [x] Create `.env.example` and `scripts/generate-env.sh`.
- [x] Create `docker-compose.yml` with `minio`, `minio-init`, and `backend`.
- [x] Write `backend/Dockerfile`.
- [x] Set up `backend/config.py` and `backend/database.py`.
- [x] Create `backend/services/minio_client.py`.
- [x] Create `backend/main.py` with `/health` endpoint.
- [x] Run acceptance tests for Phase 1.
- [x] Document in `PROGRESS.md` and commit.

## Phase 2: Minecraft deployment and management
- [x] Add `minecraft` service to `docker-compose.yml`.
- [x] Implement `backend/services/docker_service.py`.
- [x] Implement `backend/services/rcon_service.py`.
- [x] Create `backend/routes/server.py` with endpoints.
- [x] Update `main.py` to include server routes.
- [x] Run acceptance tests for Phase 2.
- [x] Document in `PROGRESS.md` and commit.

## Phase 3: Firebase Authentication and IAM/RBAC
- [x] Implement `backend/auth.py`.
- [x] Implement `backend/permissions.py`.
- [x] Create database migrations for `users` and `audit_logs`.
- [x] Implement `backend/services/audit_service.py`.
- [x] Create `backend/routes/auth.py` and `backend/routes/users.py`.
- [x] Retrofit authorization to Phase 2 endpoints.
- [x] Run acceptance tests for Phase 3.
- [x] Document in `PROGRESS.md` and commit.

## Phase 4: Minecraft-to-web verification plugin
- [x] Create database migrations for `minecraft_links` and `verification_sessions`.
- [x] Implement `backend/services/verification_service.py`.
- [x] Create `backend/routes/minecraft.py`.
- [x] Set up `minecraft-plugin/` (Maven, Java 21, Paper API).
- [x] Implement plugin join logic, API interaction, and restrictions.
- [x] Implement plugin verification polling and release logic.
- [x] Write `scripts/build-plugin.sh`.
- [x] Run acceptance tests for Phase 4.
- [x] Document in `PROGRESS.md` and commit.

## Phase 5: MinIO storage and automated backups
- [x] Create database migrations for `backups`.
- [x] Implement `backend/storage/backup.py`, `backend/storage/restore.py`, `backend/storage/retention.py`.
- [x] Create `backend/routes/backups.py`.
- [x] Implement scheduler for backups.
- [x] Run acceptance tests for Phase 5.
- [x] Document in `PROGRESS.md` and commit.

## Phase 6: Python monitoring and historical metrics
- [x] Create database migrations for `metrics`.
- [x] Implement `backend/monitoring/collector.py` and `backend/monitoring/metrics.py`.
- [x] Create `backend/routes/metrics.py`.
- [x] Run acceptance tests for Phase 6.
- [x] Document in `PROGRESS.md` and commit.

## Phase 7: React dashboard and visualization
- [x] Set up Vite + React + TypeScript in `frontend/`.
- [x] Write `frontend/Dockerfile`.
- [x] Add `frontend` service to `docker-compose.yml`.
- [x] Implement dashboard pages (Auth, Overview, Server Management, Monitoring, Backups, IAM, Minecraft Linking).
- [x] Run acceptance tests for Phase 7.
- [x] Document in `PROGRESS.md` and commit.

## Phase 8: Alerts, audit logging, and security hardening
- [ ] Create database migrations for `alerts`.
- [ ] Implement `backend/monitoring/alerts.py`.
- [ ] Update audit logging to cover all privileged actions.
- [ ] Implement security hardening (docker-socket-proxy, bucket-scoped service account, rate limiting, security headers).
- [ ] Run acceptance tests for Phase 8.
- [ ] Document in `PROGRESS.md` and commit.

## Phase 9: Integration testing and disaster recovery
- [ ] Write unit and API tests in `backend/tests/`.
- [ ] Write `scripts/integration-test.sh`.
- [ ] Write `scripts/dr-drill.sh`.
- [ ] Perform DR scenarios.
- [ ] Run acceptance tests for Phase 9.
- [ ] Document in `PROGRESS.md` and commit.

## Phase 10: Documentation and final demonstration
- [ ] Write `README.md`, `architecture.md`, `setup-guide.md`, `security.md`, `testing.md`.
- [ ] Write `docs/iam-permission-matrix.md`, `docs/monitoring.md`, `docs/backup-recovery.md`, `docs/demonstration-guide.md`.
- [ ] Create architecture diagram `docs/architecture-diagram.mmd`.
- [ ] Compile Final Report.
