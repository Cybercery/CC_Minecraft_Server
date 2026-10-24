# Project Final Report: Cloud Minecraft Server Management Platform

**Course**: Cloud Computing  
**Project**: Cloud-Native Resilient Minecraft Server Management Platform  
**Architecture**: Microservices, Event Coordination, S3 Object Storage, RBAC & Telemetry  

---

## Executive Summary

The **Cloud Minecraft Server Management Platform** is a secure, cloud-native operational system designed to manage, monitor, back up, and secure dedicated Minecraft game server workloads. The platform solves the operational challenges associated with running community and institutional game servers: uncoordinated file-level backups causing chunk corruption, unmanaged privilege escalation on administrative consoles, server resource exhaustion, and security risks associated with granting web applications raw root access to the host Docker daemon.

The system incorporates:
1. **Containerized Microservice Architecture**: Managed via Docker Compose with dedicated networks, volume isolation, and least-privilege service configurations.
2. **Robust Multi-Tenant Security & IAM**: 3-tier Role-Based Access Control (`Administrator`, `Operator`, `User`) backed by Firebase Authentication with automatic bootstrap provisioning and administrative self-demotion lockout protection.
3. **Hardened Docker Daemon Access**: Complete isolation of the host Docker socket via `tecnativa/docker-socket-proxy`, restricting the API solely to essential container operations.
4. **Cryptographic S3 Disaster Recovery**: RCON chunk synchronization (`save-off`, `save-all flush`), gzip compression, streaming SHA-256 integrity validation, automated S3 upload to MinIO, and tar path-traversal prevention.
5. **Real-time Autonomous Telemetry & Incident Management**: 30-second time-series metrics capture (CPU, RAM, disk, online players, container lifecycle), indexed storage, automated threshold alert evaluation, and operator acknowledgment workflows.
6. **In-Game Verification Plugin**: Custom Java 21 PaperMC plugin implementing join freezes, potion blindness, chat suppression, and HMAC SHA-256 verification code validation.
7. **Production Glassmorphic Dashboard**: Modern React 19 + TypeScript web application featuring live terminal streaming, RCON command dispatch, telemetry visualizers, snapshot managers, and user management.

---

## 1. System Engineering & Implementation Phases

The platform was built across 10 structured engineering phases:

### Phase 1: Docker Infrastructure & Base Services
- Configured multi-container topology in `docker-compose.yml` comprising `backend`, `minio`, `minio-init`, `minecraft`, `frontend`, and `docker-socket-proxy`.
- Established database schema migration engine in SQLite utilizing Write-Ahead Logging (`WAL`) mode.
- Built MinIO initialization service creating dedicated S3 buckets with custom access policies.
- Validated with automated acceptance tests (`backend/tests/test_phase1.py`).

### Phase 2: Minecraft Workload & RCON Control
- Integrated PaperMC Minecraft server (`itzg/minecraft-server`) with Java 21 runtime.
- Built `backend/services/docker_service.py` to handle container lifecycle state checks, start, stop, restart, and log tailing.
- Built `backend/services/rcon_service.py` using `mcrcon` with socket timeout safeguards, reconnection policies, and command sanitization.
- Verified with 7 automated tests (`backend/tests/test_phase2.py`).

### Phase 3: Firebase Authentication & IAM/RBAC
- Integrated Firebase JWT token validation with support for production JWK keys and deterministic mock tokens for automated testing.
- Created 3-tier permission matrix (`permissions.py`) mapping 15 granular permissions across `Administrator`, `Operator`, and `User` roles.
- Implemented `audit_service.py` to record an immutable audit trail of all privileged actions.
- Protected user management with self-demote lockout prevention, ensuring at least one administrator always retains access.
- Verified with 5 automated tests (`backend/tests/test_phase3.py`).

### Phase 4: Minecraft-to-Web Verification Plugin
- Scaffolded Java 21 Paper plugin in `minecraft-plugin/` with event listeners (join, move freeze, block break/place cancellation, blindness effect, chat suppression).
- Built verification service using HMAC SHA-256 hashing with server secret key, 15-minute TTL, and single-use enforcement.
- Integrated `/verify <code>` in-game command communicating via REST with the backend.
- Verified with acceptance test suite (`backend/tests/test_phase4.py`).

### Phase 5: MinIO S3 Storage & Automated Backups
- Implemented world archival in `storage/backup.py` with RCON flush coordination, `.tar.gz` packaging, SHA-256 hash generation, and S3 streaming.
- Built `storage/restore.py` verifying SHA-256 hashes against database records and inspecting archive members to prevent tar path-traversal attacks.
- Configured automated retention pruning (`storage/retention.py`) and APScheduler cron scheduling.
- Verified with acceptance test suite (`backend/tests/test_phase5.py`).

### Phase 6: Telemetry, Metrics & Historical Queries
- Built background telemetry collector in `monitoring/collector.py` using `psutil` and RCON queries.
- Created `server_metrics` table with B-tree index on `timestamp` for fast lookback queries.
- Exposed `/metrics/current`, `/metrics/history`, and `/metrics/collect` REST endpoints.
- Implemented rolling 30-day retention cleanup.
- Verified with acceptance test suite (`backend/tests/test_phase6.py`).

### Phase 7: React Dashboard & Visualization
- Developed React 19 + TypeScript + Vite frontend.
- Implemented dark-mode glassmorphic design system in `frontend/src/index.css`.
- Built modular views: Auth Modal, Role-Filtered Sidebar, Server Control & Live Terminal, Telemetry Dashboard, Backups Management, Minecraft Linking, IAM User Management, and Audit Log Viewer.
- Configured multi-stage production Nginx Docker container.

### Phase 8: Alerting, Security Hardening & Rate Limiting
- Built rule-based alerting engine in `monitoring/alerts.py` evaluating CPU, RAM, Disk, and container states with warning/critical levels.
- Added operator acknowledgment endpoints and database persistence.
- Enforced OWASP security headers, SlowAPI rate-limiting, and non-root container users.
- Isolated Docker daemon communication using `docker-socket-proxy`.
- Verified with acceptance test suite (`backend/tests/test_phase8.py`).

### Phase 9: Integration Testing & Disaster Recovery
- Authored 16 end-to-end integration test scenarios in `backend/tests/test_phase9.py`.
- Developed `scripts/integration-test.sh` for automated pipeline execution.
- Developed `scripts/dr-drill.sh` covering 6 live disaster recovery failure scenarios.
- Verified all 39 test cases passing with 100% pass rate.

### Phase 10: Documentation & Architectural Verification
- Authored comprehensive documentation suite:
  - `README.md`
  - `architecture.md`
  - `setup-guide.md`
  - `security.md`
  - `testing.md`
  - `docs/iam-permission-matrix.md`
  - `docs/monitoring.md`
  - `docs/backup-recovery.md`
  - `docs/demonstration-guide.md`
  - `docs/architecture-diagram.mmd`
  - `FINAL_REPORT.md`

---

## 2. Test & Quality Assurance Results

| Metrics | Result |
|---|---|
| Total Automated Backend Tests | **39 passed, 0 failed** |
| Test Execution Time | **~27 seconds** |
| Frontend TypeScript Build | **Clean compilation (0 errors)** |
| Disaster Recovery Drill | **6 scenarios validated** |
| Database Migration Integrity | **Schema v1 through v6 verified** |

---

## 3. Conclusion & System Highlights

The Cloud Minecraft Management Platform satisfies all criteria for a resilient, production-ready cloud management solution:
- **Resilience**: Automated S3 backups with cryptographic validation ensure zero unrecoverable data loss.
- **Security**: Strict RBAC, Docker socket proxying, HMAC code hashing, and comprehensive audit logs protect the infrastructure against internal and external threats.
- **Observability**: Live telemetry and automated alerting enable operators to detect and resolve performance degradation before service outages occur.
- **Usability**: The intuitive glassmorphic dashboard provides unified control over the entire game server lifecycle.
