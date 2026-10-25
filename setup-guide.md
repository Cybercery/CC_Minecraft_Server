# Setup and Deployment Guide

This guide covers complete instructions for installing, configuring, and operating the Cloud Minecraft Management Platform across development and production environments.

---

## 1. System Requirements

### Hardware Requirements
- **CPU**: 2 vCPU cores minimum (4 vCPU cores recommended for active Minecraft worlds).
- **RAM**: 4 GB RAM minimum (8 GB recommended: 4GB dedicated to Minecraft, 1GB for MinIO, 1GB for backend/database, 2GB OS/buffer cache).
- **Storage**: 20 GB free disk space (SSD recommended for world chunk generation and snapshot archiving).

### Software Requirements
- **Docker Engine**: version 24.0.0 or higher
- **Docker Compose**: version 2.20.0 or higher
- **Network**: Open ports:
  - `3000`: React Web Dashboard (HTTP)
  - `8000`: FastAPI Backend REST API
  - `9000`: MinIO S3 API
  - `9001`: MinIO Web Console
  - `25565`: Minecraft Game Port (TCP)
  - `25575`: RCON Remote Console (Internal Docker network only in production)

---

## 2. Configuration & Environment Setup

### 2.1 Generating Environment Secrets
Run the automated environment generator:
```bash
# On Linux / macOS / Git Bash:
chmod +x scripts/generate-env.sh
./scripts/generate-env.sh

# On Windows PowerShell:
python scripts/generate-env.py
```

This creates a production `.env` file pre-populated with secure, cryptographically random credentials.

### 2.2 Environment Variables Reference

| Variable | Default / Format | Description |
|---|---|---|
| `ENVIRONMENT` | `production` | Running environment mode (`production` or `development`) |
| `SECRET_KEY` | 64-char hex string | Application secret used for internal signing and HMAC codes |
| `MINIO_ROOT_USER` | `minioadmin` | MinIO root administrator username |
| `MINIO_ROOT_PASSWORD` | 32-char random string | MinIO root password |
| `MINIO_BUCKET` | `minecraft-backups` | S3 bucket name for snapshot archives |
| `MINIO_ENDPOINT` | `http://minio:9000` | S3 API endpoint URI |
| `MINIO_REGION` | `us-east-1` | S3 region identifier |
| `RCON_PASSWORD` | 32-char random string | Password for Minecraft RCON remote command execution |
| `BOOTSTRAP_ADMIN_EMAIL`| `admin@example.com` | Email that automatically receives the `Administrator` role on initial login |
| `BACKUP_RETENTION_COUNT`| `10` | Number of recent backups retained before automated pruning |
| `METRICS_RETENTION_DAYS`| `30` | Number of days historical metrics are preserved before purging |
| `MC_MEMORY` | `2G` | Memory allocated to the Minecraft server container JVM |
| `MINECRAFT_ONLINE_MODE` | `true` | `true` for Mojang/Microsoft session authentication; `false` for private offline dev/testing |

---

## 3. Server Configuration & Authentication Modes (Online vs. Offline)

### 3.1 Understanding `server.properties` and the `mc_data` Volume
The Minecraft `server.properties` file does **not** reside in the host project workspace. Here is why:
- The `minecraft` service in `docker-compose.yml` mounts the server's working directory (`/data`) to a **named Docker volume** (`mc_data`). Named volumes are managed internally by the Docker engine (in Linux `/var/lib/docker/volumes/` or within the Docker Desktop VM on Windows/macOS) to ensure filesystem performance and prevent accidental world corruption.
- The `itzg/minecraft-server` container dynamically generates `/data/server.properties` upon first startup based on the container's environment variables.
- By setting `OVERRIDE_SERVER_PROPERTIES: "true"` in `docker-compose.yml`, the container entrypoint will safely apply environment variable updates (including `ONLINE_MODE`) to `/data/server.properties` upon every restart, while preserving world terrain, player data, and plugin configurations.

### 3.2 Switching Authentication Modes

#### Mode A: Premium Mode (Mojang Authentication — Default)
- **Configuration** in `.env`:
  ```bash
  MINECRAFT_ONLINE_MODE=true
  ```
- **Behavior**: All client connections authenticate against Mojang/Microsoft session servers. Player identities and UUIDs are cryptographically validated by Mojang before the player joins.
- **Apply & Restart**:
  ```bash
  docker compose up -d minecraft
  ```

#### Mode B: Private Offline Testing Mode
- **Configuration** in `.env`:
  ```bash
  MINECRAFT_ONLINE_MODE=false
  ```
- **Behavior**: The server accepts client connections without contacting Mojang session servers. PaperMC assigns deterministic version-3 offline UUIDs based on the player's username (`OfflinePlayer:<username>`).
- **Apply & Restart**:
  ```bash
  docker compose up -d minecraft
  ```

### 3.3 Inspecting Server Configuration

#### When the Minecraft Container is Running:
View the full active `server.properties`:
```bash
docker exec cloud-minecraft cat /data/server.properties
```

Check the active `online-mode` property specifically:
```bash
docker exec cloud-minecraft grep "online-mode" /data/server.properties
```

Or query via the authenticated backend API:
```bash
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/server/properties
```

#### When the Minecraft Container is Stopped:
To safely inspect configuration files directly from the Docker volume without starting the game server or modifying world data:
```bash
docker run --rm -v minecraft_server_project_mc_data:/data alpine cat /data/server.properties
```
Or filter for `online-mode`:
```bash
docker run --rm -v minecraft_server_project_mc_data:/data alpine grep "online-mode" /data/server.properties
```

### 3.4 Identity Handling & Security Limitations in Offline Mode
- **In-Game Restrictions Remain Active**: Even in offline mode, unverified players are immobilized (frozen, blinded, chat/block interactions disabled) by the `CloudVerification` plugin upon joining.
- **Web Verification Required**: To lift restrictions, the player must log in to the web dashboard (authenticated via Firebase), generate a temporary 6-character HMAC SHA-256 verification code (5-minute TTL, single-use), and run `/verify <code>` in-game.
- **Offline Limitations**: In offline mode, client session certificates are not validated with Mojang. Therefore, anyone on the local network can start a Minecraft client with any username. While verification binds that in-game UUID to the web account, offline mode should **strictly be used in private, trusted development and testing environments**, never on public internet-facing servers.
- **UUID Divergence**: Switching between online and offline modes changes player UUIDs from online Mojang UUIDs to offline MD5-hashed UUIDs. If switching modes, players may need to re-link using `/verify <code>`.

---

## 4. Docker Compose Stack Deployment

### 4.1 Initial Launch
Start all services in detached mode:
```bash
docker compose up -d
```

### 4.2 Service Health Verification
Check that all containers have reached a healthy state:
```bash
docker compose ps
```

Expected status output:
- `backend`: Up (healthy) on port `8000`
- `minio`: Up (healthy) on ports `9000`, `9001`
- `minio-init`: Exited (0) (completed initial bucket and policy provisioning)
- `minecraft`: Up (healthy) on port `25565`
- `frontend`: Up on port `5173`

### 4.3 Verifying API Health
Run a curl probe against the health endpoint:
```bash
curl http://localhost:8000/health
```
Expected response:
```json
{
  "status": "ok",
  "db_schema_version": 6,
  "minio_healthy": true
}
```

---

## 5. Minecraft Verification Plugin Setup

The repository provides pre-configured plugin sources in `minecraft-plugin/`.

### 5.1 Building the Plugin Jar
If building from source:
```bash
# Using native Maven:
cd minecraft-plugin
mvn clean package

# Or using the build script:
bash scripts/build-plugin.sh
```
The compiled artifact `cloud-verification-1.0.0.jar` will be placed in `minecraft-plugin/target/`.

### 5.2 Installing into the Minecraft Server
Copy the plugin jar into the server's plugins volume:
```bash
docker cp minecraft-plugin/target/cloud-verification-1.0.0.jar cloud-minecraft:/data/plugins/
docker compose restart minecraft
```

### 5.3 Plugin Configuration
The plugin configuration `config.yml` connects to the FastAPI backend:
```yaml
api_url: "http://backend:8000/minecraft/plugin"
api_key: ""
unverified_freeze: true
unverified_blindness: true
poll_interval_seconds: 5
```

---

## 6. Production Maintenance & Day-2 Operations

### 6.1 Viewing Server Logs
- **FastAPI backend logs**:
  ```bash
  docker compose logs -f backend
  ```
- **Minecraft game server console**:
  ```bash
  docker compose logs -f minecraft
  ```

### 5.2 Performing Manual Backups
You can trigger on-demand backups through the web interface or via curl:
```bash
curl -X POST http://localhost:8000/backups \
  -H "Authorization: Bearer <ADMIN_OR_OPERATOR_TOKEN>"
```

### 5.3 Restoring from Backup
To restore a snapshot:
```bash
curl -X POST http://localhost:8000/backups/<BACKUP_ID>/restore \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

### 5.4 Database Backups
The SQLite database file is located at `backend/data/minecraft_management.db`. To take an online hot backup without downtime:
```bash
sqlite3 backend/data/minecraft_management.db ".backup 'backend/data/backup_$(date +%Y%m%d).db'"
```

---

## 7. Teardown & Reset

To cleanly stop the application while preserving worlds and data:
```bash
docker compose down
```

To perform a complete wipe and fresh reinstallation:
```bash
docker compose down -v
rm -rf backend/data/* minio/data/*
```
