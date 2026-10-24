# Live Demonstration & Evaluation Guide

This step-by-step walkthrough is designed for evaluators, instructors, and engineers demonstrating the capabilities of the Cloud Minecraft Management Platform.

---

## 1. Demo Preparation

### 1.1 Start the Stack
Ensure Docker Compose is running:
```bash
docker compose up -d
```
Verify all containers are healthy:
```bash
docker compose ps
```

### 1.2 Access the Dashboards
- Open the Web Dashboard in your browser: [http://localhost:3000](http://localhost:3000)
- Open the FastAPI Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Open the MinIO Console: [http://localhost:9001](http://localhost:9001) (Credentials in `.env`)

---

## 2. Demonstration Flow

### Step 1: Authentication & Bootstrap Admin Assignment
1. On [http://localhost:3000](http://localhost:3000), click **Sign In**.
2. Sign in with the configured `BOOTSTRAP_ADMIN_EMAIL` (e.g. `admin@example.com`).
3. **Observe**: The sidebar profile badge displays `ADMINISTRATOR` status and unlocks all administrative sections (**Server Controls**, **Monitoring**, **Backups**, **IAM Management**, **Audit Logs**, **Player Verification**).
4. Demonstrate that a regular user logging in with another email receives the `USER` role with read-only views.

### Step 2: Live Server Management & Real-time Terminal
1. Navigate to **Server Controls**.
2. **Observe**:
   - The green `RUNNING` status pill.
   - The live terminal console streaming recent PaperMC Minecraft logs (auto-refreshed every 4 seconds).
3. In the **RCON Command Dispatcher**, enter:
   ```text
   say Hello Cloud Computing!
   ```
   Click **Dispatch**.
4. **Observe**: The command output confirms execution, and the console log immediately reflects the broadcast message.
5. Demonstrate container controls by clicking **Restart**; show how the status transitions from `RESTARTING` to `RUNNING`.

### Step 3: Minecraft Verification Plugin Workflow
1. Navigate to **Minecraft Linking**.
2. Click **Generate Code**.
3. **Observe**: A 6-character alphanumeric code (e.g., `KT89X2`) appears with a 15-minute countdown timer.
4. Launch Minecraft (or use curl to simulate the plugin hook):
   ```bash
   curl -X POST http://localhost:8000/minecraft/plugin/verify \
     -H "Content-Type: application/json" \
     -d '{"player_uuid": "069a79f4-44e9-4726-a5be-fca90e38aaf5", "player_name": "Steve_Cloud", "code": "KT89X2"}'
   ```
5. **Observe**: The API returns `{"status": "verified", "player_name": "Steve_Cloud"}`.
6. Refresh the page: the Minecraft account is now permanently linked to the user profile. Attempting to use `KT89X2` again is rejected immediately.

### Step 4: Live Telemetry, Historical Metrics & Alert Simulation
1. Navigate to **Telemetry & Metrics**.
2. **Observe**:
   - Real-time gauge cards displaying CPU Utilization, Memory Usage, Disk Percentage, and Online Players.
   - The historical telemetry table showing recorded 30-second time-series samples.
3. Simulate an alert by clicking **Simulate Alert** or triggering high CPU:
   ```bash
   curl -X POST http://localhost:8000/alerts/simulate \
     -H "Authorization: Bearer <ADMIN_TOKEN>"
   ```
4. **Observe**: A red banner alert appears on the dashboard (`CPU Usage Critical: 88.5%`).
5. Click **Acknowledge**: The status switches to `Acknowledged`, recording the operator timestamp.

### Step 5: Automated MinIO S3 Backup & Checksum Verification
1. Navigate to **Backups Management**.
2. Click **Create Snapshot Now**.
3. **Observe**:
   - The backend coordinates with Minecraft via RCON (`save-off`, `save-all flush`, `save-on`).
   - The `.tar.gz` archive is created, SHA-256 is calculated, and the archive is streamed to MinIO.
   - A new row appears in the backup table displaying file size, SHA-256 hash preview, and creation date.
4. Open the MinIO Console at [http://localhost:9001](http://localhost:9001), navigate to the `minecraft-backups` bucket, and show the uploaded tarball.
5. In the dashboard, click **Restore** on the backup:
   - Point out that the system performs SHA-256 checksum re-validation.
   - Point out that path traversal sanitization runs before any file is extracted.
   - The server restarts smoothly with world state intact.

### Step 6: IAM Role Management & Lockout Defense
1. Navigate to **User Management**.
2. View the table of registered users.
3. Locate a test user and promote them from `User` to `Operator`.
4. Attempt to demote your own active Administrator account to `User`:
   - Click to change your own role to `User`.
   - **Observe**: The system rejects the action with an error notification: *"Administrators cannot demote themselves to prevent system lockout."*

### Step 7: Security Audit Log Inspection
1. Navigate to **Audit Logs**.
2. **Observe**: Every privileged action performed during the demo is cataloged in the audit log table:
   - `role_change`
   - `rcon_command`
   - `backup_create`
   - `backup_restore`
   - `minecraft_verify`
3. Point out that the logs record the exact actor UID, client IP address, action parameters, and timestamp.

---

## 3. Automated DR Drill Demonstration

To demonstrate system resilience and recovery under simulated failures during evaluation, execute the live Disaster Recovery script:
```bash
bash scripts/dr-drill.sh
```

Show the terminal output executing and passing all 6 failure recovery scenarios:
1. Golden backup & restore verification
2. Graceful RCON network degradation
3. Metrics continuity during spikes
4. Alert lifecycle & audit verification
5. Health endpoint resilience
6. RBAC unauthorized access rejection
