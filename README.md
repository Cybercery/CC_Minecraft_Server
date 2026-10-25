# Cloud Minecraft Management Platform

A resilient, cloud-native, self-hosted Minecraft server management system built with **FastAPI**, **Docker**, **MinIO (S3-compatible object storage)**, **PaperMC**, and a **React 19 + TypeScript** administrator dashboard reverse-proxied with **Nginx** and secured with automated **Cloudflare Tunnels**.

---

## System Architecture & Topology

```
+-----------------------------------------------------------------------------------------+
|                                    PUBLIC INTERNET                                      |
+-----------------------------------------------------------------------------------------+
       |                                                                   |
       | HTTPS (Cloudflare Quick Tunnel)                                   | TCP Game Packets (Playit.gg)
       v                                                                   v
+-------------------------------+                                 +--------------------+
|  cloud-web-tunnel             |                                 | Playit.gg Tunnel   |
|  (Cloudflare cloudflared)     |                                 | (Local Agent)      |
+---------------+---------------+                                 +---------+----------+
                |                                                           |
                v (Internal Docker Network: cloudnet)                       v
+---------------+---------------+                                 +---------+----------+
|  Frontend Container           |                                 |  PaperMC Server    |
|  - React 19 Dashboard (Vite)  |                                 | (itzg/minecraft)   |
|  - Nginx Reverse Proxy (5173) |                                 | Port 25565         |
+---------------+---------------+                                 +---------+----------+
                |                                                           ^
                | Reverse Proxied API Calls (/auth, /server, /minecraft...) |
                v                                                           | RCON (Port 25575)
+---------------+---------------+                                           | & REST Verification
|  FastAPI Backend (Port 8000)  |===========================================+
|  (Private to 127.0.0.1)       |
+---------------+---------------+
  |             |
  | S3 API      v
  |      +---------------+
  |      | SQLite + WAL  |
  |      | (v6 Schema)   |
  |      +---------------+
  v
+---------------+---------------+
|  MinIO Object Storage         |
|  (World Snapshots / Backups)  |
+-------------------------------+
```

The platform delivers enterprise-grade cloud operations for private and community Minecraft game servers:
- **Zero-Trust Security**: MinIO, backend API, RCON, and Docker socket are bound strictly to `127.0.0.1` and internal networks. Only the Nginx frontend (via Cloudflare tunnel) and Minecraft game port (via Playit.gg) are accessible publicly.
- **Role-Based Access Control (RBAC)**: 3-tier hierarchy (`Administrator`, `Operator`, `User`) backed by Firebase Authentication with automatic bootstrap provisioning.
- **In-Game Verification System**: Custom PaperMC Java 21 plugin holding unverified players in an immobilized state until a 6-character HMAC SHA-256 verification code is claimed on the web dashboard. Supports both Mojang online and offline/cracked accounts.
- **Automated S3 Backups & Disaster Recovery**: RCON world save flushing, compressed `.tar.gz` archiving, SHA-256 checksum verification, MinIO S3 object storage upload, and one-click restoration with path-traversal prevention.
- **Telemetry & Monitoring**: Live system CPU, RAM, disk utilization metrics, RCON player counts, threshold-based automated alerts with acknowledgment workflows, and audit logging.
- **Glassmorphic Control Console**: Fast, modern React 19 + TypeScript dashboard providing live container controls, streaming console logs, real-time command dispatch, and IAM role assignment.

---

## From Clone to Live Public Hosting (Quick Reference)

Follow these exact commands to take this project from a fresh Git clone to a publicly hosted, secure Minecraft server and web management console.

### 1. Clone the Repository
```powershell
git clone <YOUR_REPOSITORY_URL> minecraft_server_project
cd minecraft_server_project
```

### 2. Configure Environment Secrets
```powershell
# Copy the environment template:
Copy-Item .env.example .env

# Or on Linux / macOS:
cp .env.example .env
```

Open `.env` in any text editor and ensure:
- `BOOTSTRAP_ADMIN_EMAIL=your_email@gmail.com` *(receives Administrator privileges on first login)*
- `DOCKER_GID=0` *(0 on Windows Docker Desktop; run `getent group docker` on Linux)*
- `MINECRAFT_ONLINE_MODE=false` *(allow both official and cracked/offline clients; or set to `true` for Mojang-only)*
- `ENFORCE_SECURE_PROFILE=false`
- `FIREBASE_PROJECT_ID=your-firebase-project-id`

### 3. Build & Launch the Complete Stack
```powershell
docker compose up -d
```
Docker Compose will launch 5 containers:
1. `cloud-minecraft`: PaperMC 1.20.4 server with the `CloudVerification` plugin.
2. `minecraft_server_project-backend-1`: FastAPI backend and database engine.
3. `minecraft_server_project-frontend-1`: Nginx reverse proxy + React 19 dashboard on port `5173`.
4. `minecraft_server_project-minio-1`: MinIO S3 snapshot storage.
5. `cloud-web-tunnel`: Cloudflare tunnel creating an encrypted, zero-configuration public URL.

Verify all services are running:
```powershell
docker compose ps
```

### 4. Retrieve Your Public Web Dashboard URL
```powershell
docker logs cloud-web-tunnel
```
Copy the generated URL:
```text
https://<your-subdomain>.trycloudflare.com
```

### 5. Authorize the Domain in Firebase
1. Open [Firebase Console](https://console.firebase.google.com/) &rarr; **Authentication** &rarr; **Settings** &rarr; **Authorized Domains**.
2. Click **Add Domain** and enter:
   ```text
   <your-subdomain>.trycloudflare.com
   ```
3. Click **Done**. Your web dashboard is now live and fully authenticated worldwide!

### 6. Expose the Minecraft Game Port (25565) via Playit.gg
1. Download and run [Playit.gg](https://playit.gg/download).
2. Click **Add Tunnel** &rarr; Select **Minecraft Java** &rarr; Local Port `25565`.
3. Copy your permanent public address (e.g. `your-server.gl.joinmc.link`).

### 7. Join and Verify In-Game
1. Launch Minecraft 1.20.4 and join via your Playit address (`your-server.gl.joinmc.link`).
2. You will be immobilized with a prompt to verify your account.
3. Open your Cloudflare web dashboard URL (`https://<your-subdomain>.trycloudflare.com`) and log in with Google.
4. Click **"Generate Verification Code"** (e.g. `PLWE9E`).
5. Type in Minecraft chat:
   ```text
   /verify PLWE9E
   ```
6. Verification completes immediately: movement unlocks, and your role permissions are applied!

---

## Detailed Documentation Directory

For comprehensive technical architecture, security reviews, and operational playbooks:

- [Hosting & Cloud Deployment Guide](file:///e:/minecraft_server_project/hosting-guide.md): Complete guide for free tunnel hosting, zero-trust network isolation, and Playit.gg.
- [Setup & Deployment Guide](file:///e:/minecraft_server_project/setup-guide.md): Local environment setup, volume management, and online/offline mode configuration.
- [System Architecture](file:///e:/minecraft_server_project/architecture.md): Service decomposition, reverse proxy topology, and internal data flows.
- [Architecture Diagram (Mermaid)](file:///e:/minecraft_server_project/docs/architecture-diagram.mmd): Detailed component and sequence diagrams.
- [IAM & RBAC Permission Matrix](file:///e:/minecraft_server_project/docs/iam-permission-matrix.md): Roles, permissions, authorization checks, and privilege escalation prevention.
- [Monitoring & Alerting Specification](file:///e:/minecraft_server_project/docs/monitoring.md): Metrics engine, collection loops, alerting thresholds, and retention policies.
- [Backup & Disaster Recovery Protocol](file:///e:/minecraft_server_project/docs/backup-recovery.md): S3 snapshot lifecycle, restore procedures, DR drills, and path traversal safeguards.
- [Security Hardening Guide](file:///e:/minecraft_server_project/security.md): Threat models, socket proxying, rate limiting, HMAC hashing, and security headers.
- [Verification & Testing Guide](file:///e:/minecraft_server_project/testing.md): Automated pytest suites (47 tests), DR validation scripts, and integration procedures.
- [Live Demonstration Guide](file:///e:/minecraft_server_project/docs/demonstration-guide.md): Step-by-step walkthrough for live evaluations and user demonstrations.

---

## Essential Day-2 Commands

### Managing Containers
```powershell
# Stop all containers
docker compose down

# Restart the entire stack
docker compose up -d

# Restart only Minecraft server (e.g. after config changes)
docker compose restart minecraft

# Rebuild frontend after modifying React code
docker compose build frontend && docker compose up -d frontend
```

### Inspecting Logs
```powershell
# Live Minecraft server console
docker logs -f cloud-minecraft

# Live backend API logs
docker logs -f minecraft_server_project-backend-1

# View public web tunnel URL
docker logs cloud-web-tunnel
```

### In-Game Server Administration (RCON from Host)
```powershell
# Check online players
docker exec cloud-minecraft rcon-cli list

# Grant operator / op permissions
docker exec cloud-minecraft rcon-cli op <YourPlayerName>

# Send server broadcast
docker exec cloud-minecraft rcon-cli say Server maintenance in 10 minutes!
```

---

## Automated Testing & Disaster Recovery

Run the complete backend test suite (47 tests):
```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests
```

Execute automated 6-scenario Disaster Recovery drill:
```bash
bash scripts/dr-drill.sh
```

---

## License

MIT License. See [LICENSE](file:///e:/minecraft_server_project/LICENSE) for details.
