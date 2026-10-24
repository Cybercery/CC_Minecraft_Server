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

---

## 3. Docker Compose Stack Deployment

### 3.1 Initial Launch
Start all services in detached mode:
```bash
docker compose up -d
```

### 3.2 Service Health Verification
Check that all containers have reached a healthy state:
```bash
docker compose ps
```

Expected status output:
- `backend`: Up (healthy) on port `8000`
- `minio`: Up (healthy) on ports `9000`, `9001`
- `minio-init`: Exited (0) (completed initial bucket and policy provisioning)
- `minecraft`: Up (healthy) on port `25565`
- `frontend`: Up on port `3000`
- `docker-proxy`: Up on internal port `2375`

### 3.3 Verifying API Health
Run a curl probe against the health endpoint:
```bash
curl http://localhost:8000/health
```
Expected response:
```json
{
  "status": "healthy",
  "database": {
    "status": "connected",
    "schema_version": 6
  },
  "minio": {
    "status": "healthy",
    "bucket": "minecraft-backups"
  }
}
```

---

## 4. Minecraft Verification Plugin Setup

The repository provides pre-configured plugin sources in `minecraft-plugin/`.

### 4.1 Building the Plugin Jar
If building from source:
```bash
# Using native Maven:
cd minecraft-plugin
mvn clean package

# Or using the build script:
bash scripts/build-plugin.sh
```
The compiled artifact `minecraft-plugin-1.0.0.jar` will be placed in `minecraft-plugin/target/`.

### 4.2 Installing into the Minecraft Server
Copy the plugin jar into the server's plugins volume:
```bash
docker cp minecraft-plugin/target/minecraft-plugin-1.0.0.jar cc_minecraft_server-minecraft-1:/data/plugins/
docker compose restart minecraft
```

### 4.3 Plugin Configuration
The plugin configuration `config.yml` connects to the FastAPI backend:
```yaml
backend-url: "http://backend:8000"
poll-interval-seconds: 3
restriction-message: "§cYou must verify your account on the web portal to play!"
```

---

## 5. Production Maintenance & Day-2 Operations

### 5.1 Viewing Server Logs
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

## 6. Teardown & Reset

To cleanly stop the application while preserving worlds and data:
```bash
docker compose down
```

To perform a complete wipe and fresh reinstallation:
```bash
docker compose down -v
rm -rf backend/data/* minio/data/*
```
