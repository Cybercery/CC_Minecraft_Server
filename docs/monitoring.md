# Telemetry, Monitoring, and Alerting System

This document describes the telemetry collection pipeline, database schemas, metric aggregation, and threshold-based alerting mechanisms.

---

## 1. Monitoring Architecture

The monitoring subsystem operates autonomously within the backend service:
1. **Collector Loop**: Driven by an APScheduler background scheduler executing every 30 seconds (`COLLECTION_INTERVAL_SECONDS`).
2. **Telemetry Sources**:
   - Host/Container CPU utilization via `psutil.cpu_percent()`.
   - Host/Container RAM consumption (MB and percentage) via `psutil.virtual_memory()`.
   - Dedicated game volume disk storage percentage via `psutil.disk_usage()`.
   - Live connected player count obtained via Minecraft RCON command query (`/list`).
   - Minecraft Docker container lifecycle state (`running`, `exited`, `paused`, `restarting`).
3. **Storage & Indexing**: Metric samples are written to the SQLite `server_metrics` table with a B-tree index on `timestamp`.
4. **Alert Rule Evaluation Engine**: Evaluates recent telemetry against configurable thresholds and creates alert incidents.

```
+-----------------------------------------------------------+
|                   APScheduler Job                         |
+-----------------------------------------------------------+
       |
       | Every 30s
       v
+-------------------+      RCON       +---------------------+
| metrics_collector |<--------------->|  Minecraft Server   |
+---------+---------+  (Player Count) +---------------------+
          |
          | Gather CPU, RAM, Disk, Container Status
          v
+-------------------+
|  SQLite Database  |
| (server_metrics)  |
+---------+---------+
          |
          v
+-------------------+
| Alert Evaluator   |====> If CPU > 85%, RAM > 90%, Disk > 90%
+---------+---------+      Create Alert Incident in SQLite
          |
          v
+-------------------+
| Retention Purger  |====> Prune samples older than 30 days
+-------------------+
```

---

## 2. Metrics Database Schema

Table name: `server_metrics`

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Unique sequence identifier |
| `timestamp` | TEXT NOT NULL | ISO-8601 UTC timestamp of sample collection |
| `cpu_percent` | REAL NOT NULL | Total system CPU utilization (0.0 to 100.0) |
| `memory_mb` | REAL NOT NULL | Memory allocated/used in megabytes |
| `memory_percent` | REAL NOT NULL | Memory utilization percentage (0.0 to 100.0) |
| `disk_percent` | REAL NOT NULL | Volume disk storage percentage (0.0 to 100.0) |
| `online_players` | INTEGER NOT NULL | Active online players connected to server |
| `container_status`| TEXT NOT NULL | Container state string (`running`, `exited`, etc.) |

Index: `idx_server_metrics_timestamp` on `server_metrics(timestamp)`.

---

## 3. REST API Endpoints

### 3.1 Real-Time Snapshot: `GET /metrics/current`
Returns the latest single recorded metric sample:
```json
{
  "timestamp": "2026-10-24T10:45:00.123456Z",
  "cpu_percent": 18.4,
  "memory_mb": 2145.8,
  "memory_percent": 26.8,
  "disk_percent": 42.1,
  "online_players": 4,
  "container_status": "running"
}
```

### 3.2 Historical Telemetry: `GET /metrics/history`
Query parameters:
- `hours` (integer, default `24`): Time window to query.
- `limit` (integer, default `100`): Maximum number of records to return.

Returns a chronologically ordered array of historical metric points.

### 3.3 Manual On-Demand Collection: `POST /metrics/collect`
Triggers an immediate collection run outside the scheduled interval. Requires `server:start` or `alerts:manage` permission.

---

## 4. Alerting Engine & Incident Management

Table name: `alerts`

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Alert identifier |
| `alert_type` | TEXT NOT NULL | Alert category (`cpu_high`, `memory_high`, `disk_high`, `server_offline`) |
| `message` | TEXT NOT NULL | Human-readable alert explanation |
| `severity` | TEXT NOT NULL | Severity level (`warning`, `critical`) |
| `status` | TEXT NOT NULL | Incident state (`active`, `acknowledged`, `resolved`) |
| `created_at` | TEXT NOT NULL | Timestamp when alert condition was detected |
| `acknowledged_at`| TEXT | Timestamp when operator acknowledged the alert |
| `resolved_at` | TEXT | Timestamp when condition cleared |

### 4.1 Evaluation Rules
- **CPU Overload**: Triggers `cpu_high` (`critical`) when `cpu_percent >= 85.0%`.
- **Memory Pressure**: Triggers `memory_high` (`warning` at 85%, `critical` at 90%).
- **Disk Exhaustion**: Triggers `disk_high` (`critical`) when `disk_percent >= 90.0%`.
- **Container Outage**: Triggers `server_offline` (`critical`) when container status transitions to `exited` or `dead`.

### 4.2 Acknowledging Alerts
Operators or Administrators can acknowledge active alerts via `POST /alerts/{id}/ack`. This records the operator's UID, changes the state to `acknowledged`, and suppresses duplicate notifications while the team investigates.

---

## 5. Metric Pruning & Retention

To prevent unbounded database growth on embedded storage:
- The scheduled retention cleanup runs daily.
- Deletes all records in `server_metrics` where `timestamp < datetime('now', '-30 days')`.
- Ensures long-term storage consumption remains predictable and under 15 MB even with continuous 30-second polling.
