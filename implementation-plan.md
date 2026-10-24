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
- [ ] Add `minecraft` service to `docker-compose.yml`.
- [ ] Implement `backend/services/docker_service.py`.
- [ ] Implement `backend/services/rcon_service.py`.
- [ ] Create `backend/routes/server.py` with endpoints.
- [ ] Update `main.py` to include server routes.
- [ ] Run acceptance tests for Phase 2.
- [ ] Document in `PROGRESS.md` and commit.

## Phase 3: Firebase Authentication and IAM/RBAC
- [ ] Implement `backend/auth.py`.
- [ ] Implement `backend/permissions.py`.
- [ ] Create database migrations for `users` and `audit_logs`.
- [ ] Implement `backend/services/audit_service.py`.
- [ ] Create `backend/routes/auth.py` and `backend/routes/users.py`.
- [ ] Retrofit authorization to Phase 2 endpoints.
- [ ] Run acceptance tests for Phase 3.
- [ ] Document in `PROGRESS.md` and commit.

## Phase 4: Minecraft-to-web verification plugin
- [ ] Create database migrations for `minecraft_links` and `verification_sessions`.
- [ ] Implement `backend/services/verification_service.py`.
- [ ] Create `backend/routes/minecraft.py`.
- [ ] Set up `minecraft-plugin/` (Maven, Java 21, Paper API).
- [ ] Implement plugin join logic, API interaction, and restrictions.
- [ ] Implement plugin verification polling and release logic.
- [ ] Write `scripts/build-plugin.sh`.
- [ ] Run acceptance tests for Phase 4.
- [ ] Document in `PROGRESS.md` and commit.

## Phase 5: MinIO storage and automated backups
- [ ] Create database migrations for `backups`.
- [ ] Implement `backend/storage/backup.py`, `backend/storage/restore.py`, `backend/storage/retention.py`.
- [ ] Create `backend/routes/backups.py`.
- [ ] Implement scheduler for backups.
- [ ] Run acceptance tests for Phase 5.
- [ ] Document in `PROGRESS.md` and commit.

## Phase 6: Python monitoring and historical metrics
- [ ] Create database migrations for `metrics`.
- [ ] Implement `backend/monitoring/collector.py` and `backend/monitoring/metrics.py`.
- [ ] Create `backend/routes/metrics.py`.
- [ ] Run acceptance tests for Phase 6.
- [ ] Document in `PROGRESS.md` and commit.

## Phase 7: React dashboard and visualization
- [ ] Set up Vite + React + TypeScript in `frontend/`.
- [ ] Write `frontend/Dockerfile`.
- [ ] Add `frontend` service to `docker-compose.yml`.
- [ ] Implement dashboard pages (Auth, Overview, Server Management, Monitoring, Backups, IAM, Minecraft Linking).
- [ ] Run acceptance tests for Phase 7.
- [ ] Document in `PROGRESS.md` and commit.

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
