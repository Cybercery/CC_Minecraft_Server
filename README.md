# Cloud Minecraft Management Platform

A resilient, cloud-native, self-hosted Minecraft server management system built with **FastAPI**, **Docker**, **MinIO (S3-compatible object storage)**, **PaperMC**, and a **React + TypeScript** administrator dashboard.

---

## System Overview

```
                                      +--------------------+
                                      |   Browser Client   |
                                      +---------+----------+
                                                | HTTP / HTTPS
                                                v
+------------------+  RCON / Events   +--------------------+  S3 API   +--------------------+
|  PaperMC Server  |<================>|  FastAPI Backend   |==========>|  MinIO Object St.  |
| (itzg/minecraft) |   (Port 25575)   |   (Port 8000)      | (Port 9000)|  (S3 Snapshots)   |
+------------------+                  +---------+----------+           +--------------------+
                                                |
                                                v
                                      +--------------------+
                                      |   SQLite + WAL     |
                                      | (Auth, RBAC, Logs) |
                                      +--------------------+
```

The platform delivers enterprise-grade cloud operations for private and community Minecraft game servers, including:
- **Role-Based Access Control (RBAC)**: 3-tier hierarchy (`Administrator`, `Operator`, `User`) backed by Firebase Authentication with automatic bootstrap provisioning.
- **In-Game Verification System**: Custom PaperMC Java 21 plugin holding unverified players in an immobilized state until a 6-character HMAC SHA-256 verification code is claimed on the web dashboard.
- **Automated S3 Backups & Disaster Recovery**: RCON world save flushing, compressed `.tar.gz` archiving, SHA-256 checksum verification, MinIO S3 object storage upload, and one-click restoration with path-traversal prevention.
- **Telemetry & Monitoring**: Live system CPU, RAM, disk utilization metrics, RCON player counts, threshold-based automated alerts with acknowledgment workflows, and audit logging.
- **Glassmorphic Control Console**: Fast, modern React 19 + TypeScript dashboard providing live container controls, streaming console logs, real-time command dispatch, and IAM role assignment.

---

## Architecture & Technology Stack

| Layer | Component | Description |
|---|---|---|
| **Frontend** | React 19, TypeScript, Vite | Dark-mode glassmorphic interface, Firebase Auth SDK, real-time telemetry polling |
| **Backend API** | FastAPI, Uvicorn, Python 3.12 | Async REST endpoints, SlowAPI rate-limiting, security headers |
| **Database** | SQLite3 (WAL Mode) | Persistent transactional storage with incremental schema migrations (v1-v6) |
| **Game Server** | PaperMC 1.20+ (`itzg/minecraft-server`) | High-performance Java 21 server container with RCON integration |
| **In-Game Plugin** | Java 21 Paper Plugin | Join freeze, blind effect, `/verify <code>` command, REST verification client |
| **Object Storage** | MinIO (S3-compatible) | Bucket-scoped S3 storage for immutable world snapshots with retention policy |
| **Security Proxy** | Docker Socket Proxy | Read/write socket isolation preventing unauthorized Docker API operations |

---

## Quick Start Guide

### 1. Prerequisites
- Docker Engine 24+ and Docker Compose v2+
- Python 3.12+ (for local test running)
- Node.js 20+ & npm (for frontend building)
- Java 21 & Maven (optional, for native plugin compilation)

### 2. Environment Configuration
Generate secure random credentials:
```bash
# On Linux / macOS / Git Bash:
./scripts/generate-env.sh

# Or using Python:
python scripts/generate-env.py
```
Review and customize `.env` as required (set `BOOTSTRAP_ADMIN_EMAIL` to your administrative email).

### 3. Launching with Docker Compose
Start the full stack:
```bash
docker compose up -d
```

Service endpoints:
- **Web Dashboard**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **MinIO Console**: [http://localhost:9001](http://localhost:9001)
- **Minecraft Server**: `localhost:25565`

---

## Detailed Documentation Directory

For in-depth operational and technical specifications, refer to:

- [Setup & Deployment Guide](file:///c:/Users/kunal/Desktop/College/Notes/Sem%20XI/Cloud%20Computing/CC_Minecraft_Server/setup-guide.md): Environment variables, Docker Compose configuration, production deployment instructions.
- [System Architecture](file:///c:/Users/kunal/Desktop/College/Notes/Sem%20XI/Cloud%20Computing/CC_Minecraft_Server/architecture.md): Service decomposition, data flows, and infrastructure models.
- [Architecture Diagram (Mermaid)](file:///c:/Users/kunal/Desktop/College/Notes/Sem%20XI/Cloud%20Computing/CC_Minecraft_Server/docs/architecture-diagram.mmd): Structural and sequence diagrams.
- [IAM & RBAC Permission Matrix](file:///c:/Users/kunal/Desktop/College/Notes/Sem%20XI/Cloud%20Computing/CC_Minecraft_Server/docs/iam-permission-matrix.md): Roles, permissions, API authorization checks, and lockout prevention.
- [Monitoring & Alerting Specification](file:///c:/Users/kunal/Desktop/College/Notes/Sem%20XI/Cloud%20Computing/CC_Minecraft_Server/docs/monitoring.md): Metrics engine, collection loops, alerting thresholds, and retention policies.
- [Backup & Disaster Recovery Protocol](file:///c:/Users/kunal/Desktop/College/Notes/Sem%20XI/Cloud%20Computing/CC_Minecraft_Server/docs/backup-recovery.md): S3 snapshot lifecycle, restore procedures, DR drills, and path traversal safeguards.
- [Security Hardening Guide](file:///c:/Users/kunal/Desktop/College/Notes/Sem%20XI/Cloud%20Computing/CC_Minecraft_Server/security.md): Threat models, socket proxying, rate limiting, HMAC hashing, and security headers.
- [Verification & Testing Guide](file:///c:/Users/kunal/Desktop/College/Notes/Sem%20XI/Cloud%20Computing/CC_Minecraft_Server/testing.md): Automated pytest suites (39 tests), DR validation scripts, and integration procedures.
- [Live Demonstration Guide](file:///c:/Users/kunal/Desktop/College/Notes/Sem%20XI/Cloud%20Computing/CC_Minecraft_Server/docs/demonstration-guide.md): Scripted step-by-step walkthrough for evaluation and live demos.

---

## Automated Testing & Disaster Recovery

Run the complete backend test suite:
```bash
.\.venv\Scripts\python.exe -m pytest backend/tests
```

Execute end-to-end integration test script:
```bash
bash scripts/integration-test.sh
```

Execute automated 6-scenario Disaster Recovery drill:
```bash
bash scripts/dr-drill.sh
```

---

## License

MIT License. See [LICENSE](file:///c:/Users/kunal/Desktop/College/Notes/Sem%20XI/Cloud%20Computing/CC_Minecraft_Server/LICENSE) for details.
