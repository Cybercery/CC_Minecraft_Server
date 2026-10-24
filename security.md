# Security Architecture & Hardening Guide

This document outlines the security controls, authentication mechanisms, defensive hardening practices, and threat mitigation implemented across the Cloud Minecraft Management Platform.

---

## 1. Security Architecture Summary

The platform applies defense-in-depth principles across all network and process boundaries:
1. **Zero-Trust Identity**: Every REST endpoint (except `/health` and plugin verification endpoints) requires an authenticated JWT bearer token verified against Firebase Authentication or deterministic development signatures.
2. **Strict RBAC Enforcement**: Fine-grained authorization gates access based on role permissions (`Administrator`, `Operator`, `User`).
3. **Container Isolation & Socket Proxying**: The backend does not mount the raw `/var/run/docker.sock`. Instead, it communicates via `docker-socket-proxy`, restricting Docker API endpoints to only necessary container lifecycle and log inspection calls.
4. **Least-Privilege Storage Access**: MinIO S3 credentials are restricted to the designated `minecraft-backups` bucket.
5. **Cryptographic Protection of Verification Codes**: Player verification codes are stored exclusively as HMAC SHA-256 hashes using a 256-bit server-side secret key; cleartext codes exist only transiently in memory when generated.
6. **Path Traversal Protection**: Archive restoration explicitly verifies all tar member paths against directory traversal (`../`) and forbidden root mounts.
7. **Security Headers & Rate Limiting**: HTTP response headers follow OWASP recommendations, and SlowAPI enforces rate limits on abuse-prone endpoints.

---

## 2. Authentication & IAM Framework

### 2.1 Firebase Auth Integration
- The frontend dashboard uses the Firebase Web SDK supporting both Google OAuth 2.0 popup flows and email/password credentials.
- When querying backend routes, the frontend includes the Firebase ID token in the `Authorization: Bearer <token>` header.
- The backend `backend/auth.py` validates token signatures against Google's public JWK keys:
  - Validates `iss` (issuer) matches `https://securetoken.google.com/<FIREBASE_PROJECT_ID>`.
  - Validates `aud` (audience) matches `<FIREBASE_PROJECT_ID>`.
  - Validates expiration timestamp (`exp`).

### 2.2 Bootstrap Administrator Provisioning
To avoid the "first user chicken-and-egg problem", when a user authenticates whose email matches `BOOTSTRAP_ADMIN_EMAIL`, the backend automatically provisions their role as `Administrator` in the SQLite `users` table on first login. Subsequent users register with the default `User` role.

### 2.3 Role-Based Access Control (RBAC) Matrix

| Permission String | Description | Administrator | Operator | User |
|---|---|:---:|:---:|:---:|
| `server:read` | View server status and online players | Yes | Yes | Yes |
| `server:start` | Start stopped server container | Yes | Yes | No |
| `server:stop` | Stop running server container | Yes | Yes | No |
| `server:restart`| Restart server container | Yes | Yes | No |
| `server:logs` | Read server console logs | Yes | Yes | No |
| `server:rcon` | Execute arbitrary RCON commands | Yes | No | No |
| `backup:read` | List backup archives and checksums | Yes | Yes | Yes |
| `backup:create` | Trigger on-demand backup snapshot | Yes | Yes | No |
| `backup:restore`| Restore server world from backup archive | Yes | No | No |
| `metrics:read` | View real-time and historical telemetry | Yes | Yes | Yes |
| `alerts:manage` | Acknowledge and resolve system alerts | Yes | Yes | No |
| `users:read` | View registered user directory | Yes | No | No |
| `users:manage` | Change user RBAC roles | Yes | No | No |
| `audit:read` | Inspect administrative audit logs | Yes | No | No |
| `minecraft:link`| Generate verification code & link player | Yes | Yes | Yes |

### 2.4 Administrative Lockout Prevention
In `backend/routes/users.py`, when a user attempts to change their own role:
```python
if current_user.uid == target_uid and new_role != "Administrator":
    raise HTTPException(
        status_code=400,
        detail="Administrators cannot demote themselves to prevent system lockout."
    )
```
This guarantees at least one active administrator remains present in the system.

---

## 3. Storage & Backup Security

### 3.1 SHA-256 Cryptographic Checksums
When a world backup is created:
1. A `.tar.gz` archive is compiled.
2. A SHA-256 hash is calculated across the raw bytes and stored with the backup record in SQLite.
3. Upon restoration, the downloaded archive is hashed before decompression. If the computed hash deviates from the database record, the restoration aborts immediately with a 400 Bad Request to prevent corrupted or tampered file execution.

### 3.2 Tar Path Traversal Defense
Malicious or crafted archive payloads could exploit path traversal vulnerabilities (e.g., `../../etc/passwd`). The extraction routine in `storage/restore.py` sanitizes and inspects every member:
```python
for member in tar.getmembers():
    # Disallow absolute paths and parent directory traversals
    if member.name.startswith("/") or ".." in member.name:
        raise ValueError(f"Malicious archive member detected: {member.name}")
    target_path = os.path.abspath(os.path.join(target_dir, member.name))
    if not target_path.startswith(os.path.abspath(target_dir)):
        raise ValueError(f"Path traversal detected: {member.name}")
```

---

## 4. Minecraft-to-Web Verification Security

- **Short-Lived Ephemeral Codes**: Verification codes are random 6-character strings drawn from uppercase alphanumeric characters (`A-Z`, `0-9`), avoiding ambiguous characters (`0`, `O`, `1`, `I`).
- **HMAC SHA-256 Hashing**: Verification codes are never stored in plaintext within the database. The database persists only `HMAC_SHA256(code, SECRET_KEY)`.
- **Single-Use Enforcement**: Verification sessions are flagged `used = 1` atomically upon successful verification. Replays of previously used codes are rejected.
- **TTL Expiration**: Verification codes expire automatically after 15 minutes (`expires_at < CURRENT_TIMESTAMP`).

---

## 5. Network & Container Hardening

### 5.1 Docker Socket Proxy
Exposing the raw `/var/run/docker.sock` to web application containers presents extreme privilege escalation risks (granting effective root control of the host).
In `docker-compose.yml`, the backend is isolated behind `tecnativa/docker-socket-proxy` with strict flags:
```yaml
environment:
  CONTAINERS: 1
  POST: 1
  AUTH: 0
  BUILD: 0
  COMMIT: 0
  CONFIGS: 0
  DISTRIBUTION: 0
  EXEC: 0
  IMAGES: 0
  INFO: 0
  NETWORKS: 0
  NODES: 0
  PLUGINS: 0
  SERVICES: 0
  SESSION: 0
  SWARM: 0
  SYSTEM: 0
  TASKS: 0
  VOLUMES: 0
```
This restricts the API solely to managing pre-existing containers without the capability to mount host filesystems, spawn root containers, or alter networks.

### 5.2 Security Headers Middleware
In `backend/main.py`, every HTTP response is injected with security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: default-src 'self'`

### 5.3 Non-Root Container Execution
The backend container runs as a dedicated unprivileged user (`appuser`, UID `10001`):
```dockerfile
RUN groupadd -g 10001 appuser && useradd -u 10001 -g appuser -s /bin/sh appuser
USER appuser
```

---

## 6. Audit Trail & Logging

All security-sensitive operations generate immutable audit records in the SQLite `audit_logs` table:
- User role changes (`role_change`)
- Server container actions (`start`, `stop`, `restart`)
- RCON command dispatches (`rcon_command`)
- Backup creation and restoration (`backup_create`, `backup_restore`)
- Account linking events (`minecraft_verify`)

Each log entry records:
- `actor_uid`: ID of the user initiating the action
- `action`: Specific operation performed
- `target_type`: Entity affected (`user`, `server`, `backup`, etc.)
- `target_id`: Identifier of the affected entity
- `details`: JSON payload of parameters (sanitized to remove passwords)
- `ip_address`: Client origin IP
- `timestamp`: ISO-8601 UTC timestamp
