# Testing & Verification Strategy

This document describes the automated testing suites, testing methodologies, coverage areas, and Disaster Recovery validation procedures for the Cloud Minecraft Management Platform.

---

## 1. Overview of Test Architecture

The platform uses a layered testing strategy consisting of:
- **Unit and Service Tests**: Validates individual components (HMAC code generator, permission checkers, S3 client adapter, SQLite migrations).
- **API Acceptance Tests (Phases 1–8)**: Validates HTTP status codes, payloads, error handling, rate limiting, and RBAC enforcement.
- **End-to-End Integration Suite (Phase 9)**: 16 integration scenarios validating multi-service workflows (authentication, role transition, backup creation/restore, code generation & claiming, alerts lifecycle).
- **Automated Disaster Recovery (DR) Drill Script**: A runnable bash script (`scripts/dr-drill.sh`) testing live system recovery, RCON graceful degradation, and health endpoint resilience.
- **Frontend Build Validation**: Automated TypeScript type-checking and Vite production asset bundling.

---

## 2. Test Suites Summary

The automated test suite in `backend/tests/` contains **39 passing automated tests**:

| Test File | Phase / Focus | Test Count | Scenarios Tested |
|---|---|:---:|---|
| `test_phase1.py` | Setup & Docker Infrastructure | 2 | `/health` endpoint response, schema version reporting, MinIO health probe. |
| `test_phase2.py` | Minecraft Deployment & RCON | 7 | Container status, start, stop, restart, console logs, online player queries, RCON command dispatch. |
| `test_phase3.py` | Firebase Auth & IAM/RBAC | 5 | Bootstrap admin provisioning, role permission checks, user listing, role assignment, self-demote lockout prevention. |
| `test_phase4.py` | Minecraft Verification Plugin | 1 | Verification code generation, SHA-256 HMAC verification, player status check, link creation. |
| `test_phase5.py` | MinIO Storage & Backups | 3 | Backup creation, S3 upload, SHA-256 integrity validation, archive restoration, retention enforcement. |
| `test_phase6.py` | Metrics & Historical Monitoring | 3 | Live metric capture, historical time-series queries, retention purges. |
| `test_phase8.py` | Alerts & Hardening | 2 | Alert rule evaluation (CPU, memory, disk), unacknowledged status filtering, alert acknowledgment. |
| `test_phase9.py` | End-to-End Integration | 16 | Unauthenticated access rejections, RBAC boundaries for all 3 roles, backup/restore lifecycle, verification code expiration, audit log persistence, security headers. |
| **Total** | | **39** | **100% Pass Rate** |

---

## 3. Running Automated Tests

### 3.1 Running Backend Pytest Suites
Activate the local virtual environment and execute pytest:
```bash
# Windows PowerShell:
.\.venv\Scripts\python.exe -m pytest backend/tests -v

# Linux / macOS:
pytest backend/tests -v
```

### 3.2 Running Phase-Specific Tests
To run tests for a single phase (e.g., Phase 9 Integration):
```bash
.\.venv\Scripts\python.exe -m pytest backend/tests/test_phase9.py -v
```

### 3.3 Running the Complete Integration Script
The shell script `scripts/integration-test.sh` executes the end-to-end test workflow:
```bash
bash scripts/integration-test.sh
```
It performs:
1. Python environment and dependency validation.
2. Complete pytest execution across all 39 test cases.
3. Frontend TypeScript compilation (`tsc -b`) and Vite production bundle creation (`npm run build`).
4. Optional Docker Compose live smoke test if containers are running.

---

## 4. Disaster Recovery (DR) Drill Script

The script `scripts/dr-drill.sh` validates business continuity and fault recovery across 6 distinct scenarios:

```bash
bash scripts/dr-drill.sh
```

### Scenario Matrix:

1. **Scenario 1: Golden Backup & Restore Path**
   - Creates an on-demand snapshot via the `/backups` endpoint.
   - Validates MinIO S3 object presence and SHA-256 hash matching.
   - Triggers restore and checks server container restart and world persistence.

2. **Scenario 2: Graceful RCON Degradation**
   - Simulates RCON network interruption or Minecraft container downtime.
   - Verifies the backup engine falls back safely to disk snapshots without throwing unhandled exceptions.
   - Verifies the collector records a container status of `offline` without crashing background workers.

3. **Scenario 3: Metrics Continuity**
   - Verifies the metrics collection loop survives temporary system spikes.
   - Ensures historical queries return properly sorted time-series telemetry.

4. **Scenario 4: Alerting & Audit Trail Integrity**
   - Simulates metric thresholds triggering an alert.
   - Acknowledges the alert and asserts state change to `acknowledged`.
   - Confirms that an immutable audit log entry is written for both alert resolution and privileged actions.

5. **Scenario 5: Health Endpoint Resilience**
   - Queries `/health` during partial service degradation (e.g. MinIO connectivity drop).
   - Confirms `/health` returns informative degradation indicators rather than returning unhandled 500 crashes.

6. **Scenario 6: RBAC Boundary & Privilege Escalation Defenses**
   - Simulates a standard `User` trying to issue RCON commands (`/server/rcon`), demote administrators, or trigger restores.
   - Verifies exact `403 Forbidden` responses and security audit records.

---

## 5. Frontend Quality & Bundle Verification

To verify that the frontend codebase contains no TypeScript errors and builds for production:
```bash
cd frontend
npm run build
```
Expected output:
- `✓ built in ~2s` with zero TypeScript errors.
- Compact gzipped bundle output (`dist/assets/index-*.js`, `dist/assets/index-*.css`).
