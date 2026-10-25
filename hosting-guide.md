# Complete Hosting & Deployment Guide

This guide covers everything required to go from **cloning this repository** to having a **live, publicly accessible Minecraft server and web management dashboard** hosted directly from your computer for free.

---

## 1. Architecture & Port Exposure Overview

The stack is designed with a **zero-trust, private-by-default** model:

| Component | Port | Network Access | Purpose |
| :--- | :--- | :--- | :--- |
| **Minecraft Server** | `25565` (TCP) | **Public via Playit.gg** | Game packets only. Players connect here. |
| **Web Dashboard** | `5173` (HTTP/S) | **Public via Cloudflare Tunnel** | React 19 UI with Nginx reverse proxy. |
| **Backend API** | `8000` | **Private (127.0.0.1)** | FastAPI REST engine. Proxied internally by Nginx. |
| **RCON Remote Console**| `25575` | **Private (127.0.0.1)** | Server command execution. Never exposed to web. |
| **MinIO S3 Storage** | `9090` / `9191` | **Private (127.0.0.1)** | S3 world backups and snapshot storage. |
| **Docker Socket** | Unix socket | **Private (Internal)** | Container control. Gated behind admin RBAC. |

---

## 2. Prerequisites

Before starting, ensure you have:
1. **Git**: Installed from [git-scm.com](https://git-scm.com).
2. **Docker Desktop**: Version 24+ with Docker Compose v2+ ([docker.com](https://www.docker.com/products/docker-desktop/)).
3. **Firebase Account**: A free Firebase project for authentication ([console.firebase.google.com](https://console.firebase.google.com/)).
4. **Playit.gg Client**: Free gaming tunnel for port 25565 ([playit.gg/download](https://playit.gg/download)).

---

## 3. Step-by-Step Setup: From Clone to Live Hosting

### Step 1: Clone the Repository
Open PowerShell or your terminal and run:
```powershell
git clone <YOUR_REPOSITORY_URL> minecraft_server_project
cd minecraft_server_project
```

---

### Step 2: Configure Environment Variables
Copy the template to create your `.env` file:
```powershell
# On Windows PowerShell:
Copy-Item .env.example .env

# On Linux / macOS:
cp .env.example .env
```

Open `.env` in your editor and configure the essential settings:

```dotenv
# 1. Administrator Email (Your Google/Firebase login email)
BOOTSTRAP_ADMIN_EMAIL=your_email@gmail.com

# 2. Host Docker GID (0 for Windows Docker Desktop, or run `getent group docker` on Linux)
DOCKER_GID=0

# 3. Authentication Mode
# Set to 'false' to allow both official and unofficial/offline (cracked) clients
# Set to 'true' for strict Mojang session authentication only
MINECRAFT_ONLINE_MODE=false
ENFORCE_SECURE_PROFILE=false

# 4. Secret Keys (Generate secure random strings)
RCON_PASSWORD=YourSecureRconPassword123
PLUGIN_API_KEY=Your32CharacterRandomSecretKeyForPlugin
CODE_HMAC_SECRET=Your32CharacterSecretForVerificationCodes

# 5. Firebase Project (From Firebase Console Project Settings)
FIREBASE_PROJECT_ID=your-firebase-project-id
```

---

### Step 3: Build & Launch the Docker Stack
Run the following command to download images, compile the frontend, and start all containers in the background:

```powershell
docker compose up -d
```

Verify that all services are running and healthy:
```powershell
docker compose ps
```

You should see 5 active containers:
- `cloud-minecraft` (healthy)
- `minecraft_server_project-backend-1` (healthy)
- `minecraft_server_project-frontend-1`
- `minecraft_server_project-minio-1`
- `cloud-web-tunnel`

---

### Step 4: Retrieve Your Public Web Dashboard URL
The automated `tunnel` container generates an encrypted HTTPS URL on startup. Retrieve it from the logs:

```powershell
docker logs cloud-web-tunnel
```

Look for the block:
```text
+--------------------------------------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
|  https://your-unique-subdomain.trycloudflare.com                                           |
+--------------------------------------------------------------------------------------------+
```

Copy the `https://....trycloudflare.com` URL.

---

### Step 5: Whitelist Your Domain in Firebase Console
For security, Firebase Auth blocks logins from unauthorized domains. Whitelist your tunnel URL:

1. Open the **[Firebase Console](https://console.firebase.google.com/)**.
2. Select your project &rarr; go to **Build** &rarr; **Authentication**.
3. Click the **Settings** tab at the top &rarr; **Authorized Domains**.
4. Click **Add Domain** and enter **only the hostname**:
   ```text
   your-unique-subdomain.trycloudflare.com
   ```
5. Click **Done**.

Now anyone can open that URL in their browser and sign in via Google!

---

### Step 6: Expose Minecraft Port (25565) via Playit.gg
To allow players on the internet to join your server without modifying your router or sharing your personal IP:

1. Launch **Playit.gg** on your PC.
2. The app will open a browser window to claim your computer.
3. Click **Add Tunnel**:
   - **Tunnel Type**: `Minecraft Java`
   - **Local Port**: `25565` (TCP)
   - Click **Create Tunnel**.
4. Playit provides a permanent public address (e.g. `your-server.gl.joinmc.link`).
5. Share this address with your players!

---

### Step 7: In-Game Verification Workflow
1. Player launches Minecraft 1.20.4 and joins via the Playit address (`your-server.gl.joinmc.link`).
2. Upon joining, unverified players are frozen and blinded with a welcome message:
   ```text
   Welcome to the Minecraft Server!
   Your account is not verified.
   Generate a code on the web dashboard and type:
   /verify <code>
   ```
3. Player visits your dashboard URL: `https://your-unique-subdomain.trycloudflare.com`.
4. Player signs in with Google & clicks **"Generate Verification Code"** (e.g., `PLWE9E`).
5. Player types in Minecraft chat:
   ```text
   /verify PLWE9E
   ```
6. The account is instantly linked! Movement restrictions lift, and player achievements/inventory are secured to their account.

---

## 4. Day-2 Operations & Maintenance Commands

### Switching Authentication Modes (Online vs. Offline)
To change between Premium Mojang mode and Offline/Cracked mode:
1. Edit [.env](file:///e:/minecraft_server_project/.env):
   - For Premium only: `MINECRAFT_ONLINE_MODE=true` and `ENFORCE_SECURE_PROFILE=true`
   - For Offline/All clients: `MINECRAFT_ONLINE_MODE=false` and `ENFORCE_SECURE_PROFILE=false`
2. Restart the containers:
   ```powershell
   docker compose up -d minecraft backend
   ```

### Inspecting Server Logs
```powershell
# Live Minecraft console logs
docker logs -f cloud-minecraft

# Backend API logs
docker logs -f minecraft_server_project-backend-1

# Web tunnel logs (to check URL)
docker logs cloud-web-tunnel
```

### Running RCON Commands from Terminal
You can execute commands on the Minecraft server directly from the host:
```powershell
docker exec cloud-minecraft rcon-cli list
docker exec cloud-minecraft rcon-cli op YourUsername
docker exec cloud-minecraft rcon-cli say Hello from terminal!
```

### Backups & World Snapshots
- **Via Web Dashboard**: Open **Backups** tab &rarr; click **"Create Snapshot"**.
- **Automated**: Scheduled daily at 03:00 UTC via APScheduler and stored in MinIO S3.

### Stopping & Restarting the Server
```powershell
# Gracefully stop all containers
docker compose down

# Restart the entire stack
docker compose up -d
```

---

## 5. Troubleshooting & FAQ

| Problem | Cause | Solution |
| :--- | :--- | :--- |
| `Failed to log in: Invalid session` | Server is in online mode, but client is unofficial/offline | Set `MINECRAFT_ONLINE_MODE=false` in `.env` and run `docker compose up -d minecraft`. |
| `Error generating code: Invalid or expired authentication credentials` | Clock drift between local PC and Google token issuance | The backend includes 60s clock skew tolerance (`clock_skew_seconds=60`). Ensure your system clock is synchronized. |
| `Verification failed: HTTP 400` | Client tried HTTP/2 cleartext upgrade | Recompile plugin with forced `HttpClient.Version.HTTP_1_1` (already resolved in latest jar). |
| `auth/unauthorized-domain` in web browser | Tunnel domain not whitelisted in Firebase | Copy the exact hostname from `docker logs cloud-web-tunnel` into Firebase Console &rarr; Auth &rarr; Settings &rarr; Authorized Domains. |
| `PermissionError: [Errno 13] Permission denied` | Docker socket GID mismatch | Set `DOCKER_GID=0` in `.env` for Windows Docker Desktop. |
