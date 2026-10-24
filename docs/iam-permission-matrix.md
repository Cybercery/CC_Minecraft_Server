# Identity and Access Management (IAM) Permission Matrix

This document provides a detailed specification of the Role-Based Access Control (RBAC) security model implemented across the Cloud Minecraft Management Platform.

---

## 1. Role Hierarchy

The platform defines three hierarchical roles:

1. **Administrator (`admin`)**: Full platform control. Can perform container operations, issue raw RCON commands, restore server backups, manage user roles, and inspect security audit logs.
2. **Operator (`operator`)**: Day-to-day operations role. Can view telemetry, start/stop/restart the Minecraft server, inspect console logs, create backups, and acknowledge alerts. Cannot execute raw RCON commands or restore backups.
3. **User (`user`)**: Read-only baseline role assigned to registered players and viewers. Can view server status, telemetry dashboards, backup catalogs, and link their Minecraft account using verification codes.

```
       +-------------------+
       |   Administrator   |  (Full System Control, RCON, Backups, IAM)
       +---------+---------+
                 |
                 v
       +-------------------+
       |     Operator      |  (Lifecycle Control, Backups, Telemetry, Alerts)
       +---------+---------+
                 |
                 v
       +-------------------+
       |       User        |  (Read-only Dashboards, Player Linking)
       +-------------------+
```

---

## 2. Granular Permissions Definition

| Permission Name | Description | Category |
|---|---|---|
| `server:read` | Read server online state, port mappings, and player list | Server |
| `server:start` | Start a stopped Minecraft server container | Server |
| `server:stop` | Gracefully stop the Minecraft server container | Server |
| `server:restart` | Restart the Minecraft server container | Server |
| `server:logs` | Read Minecraft console logs and stdout streams | Server |
| `server:rcon` | Send interactive RCON console commands (e.g. `op`, `gamemode`) | Server |
| `backup:read` | View the backup catalog, file sizes, and SHA-256 hashes | Backups |
| `backup:create` | Trigger an on-demand world snapshot and S3 upload | Backups |
| `backup:restore` | Restore server world from an existing S3 backup snapshot | Backups |
| `metrics:read` | Inspect live telemetry gauges and historical time-series data | Monitoring |
| `alerts:manage` | Acknowledge active alerts and update alert states | Monitoring |
| `users:read` | View the directory of all registered users and assigned roles | IAM |
| `users:manage` | Elevate or demote user roles | IAM |
| `audit:read` | Search and inspect administrative audit logs | Auditing |
| `minecraft:link` | Request 6-character verification code to link in-game account | Verification |

---

## 3. Role-to-Permission Mapping Matrix

| Permission | Administrator | Operator | User |
|---|:---:|:---:|:---:|
| `server:read` | Allowed | Allowed | Allowed |
| `server:start` | Allowed | Allowed | Denied (403) |
| `server:stop` | Allowed | Allowed | Denied (403) |
| `server:restart` | Allowed | Allowed | Denied (403) |
| `server:logs` | Allowed | Allowed | Denied (403) |
| `server:rcon` | Allowed | Denied (403) | Denied (403) |
| `backup:read` | Allowed | Allowed | Allowed |
| `backup:create` | Allowed | Allowed | Denied (403) |
| `backup:restore` | Allowed | Denied (403) | Denied (403) |
| `metrics:read` | Allowed | Allowed | Allowed |
| `alerts:manage` | Allowed | Allowed | Denied (403) |
| `users:read` | Allowed | Denied (403) | Denied (403) |
| `users:manage` | Allowed | Denied (403) | Denied (403) |
| `audit:read` | Allowed | Denied (403) | Denied (403) |
| `minecraft:link` | Allowed | Allowed | Allowed |

---

## 4. API Route Protection Reference

Every protected API route in FastAPI enforces access through FastAPI dependency injection (`Depends(require_permission(...))`):

| Endpoint Route | HTTP Method | Required Permission | Allowed Roles |
|---|:---:|---|---|
| `/server/status` | GET | `server:read` | Admin, Operator, User |
| `/server/start` | POST | `server:start` | Admin, Operator |
| `/server/stop` | POST | `server:stop` | Admin, Operator |
| `/server/restart`| POST | `server:restart`| Admin, Operator |
| `/server/logs` | GET | `server:logs` | Admin, Operator |
| `/server/rcon` | POST | `server:rcon` | Admin only |
| `/backups` | GET | `backup:read` | Admin, Operator, User |
| `/backups` | POST | `backup:create` | Admin, Operator |
| `/backups/{id}/restore` | POST | `backup:restore` | Admin only |
| `/metrics/current` | GET | `metrics:read` | Admin, Operator, User |
| `/metrics/history` | GET | `metrics:read` | Admin, Operator, User |
| `/alerts` | GET | `metrics:read` | Admin, Operator, User |
| `/alerts/{id}/ack` | POST | `alerts:manage` | Admin, Operator |
| `/users` | GET | `users:read` | Admin only |
| `/users/{uid}/role` | PUT | `users:manage` | Admin only |
| `/auth/audit-logs` | GET | `audit:read` | Admin only |
| `/minecraft/verification-code` | POST | `minecraft:link` | Admin, Operator, User |

---

## 5. Security Invariants & Lockout Protection

1. **Bootstrap Provisioning**: On system startup or initial login, if a user's email matches the configured `BOOTSTRAP_ADMIN_EMAIL`, they are automatically granted the `Administrator` role without requiring manual database manipulation.
2. **Self-Demotion Lockout Prevention**: An Administrator cannot demote their own account. Attempting to change one's own role from `Administrator` to `Operator` or `User` returns an explicit `400 Bad Request`.
3. **Audit Trail**: Every modification to a user's role generates an audit record recording the target user UID, the previous role, the new role, the initiator UID, and client IP address.
