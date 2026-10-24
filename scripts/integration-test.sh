#!/usr/bin/env bash
# =============================================================================
# scripts/integration-test.sh
# End-to-end integration test runner for the Minecraft Cloud Platform.
# Runs all pytest test suites and prints a summary.
# Usage: bash scripts/integration-test.sh [--docker]
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

DOCKER_MODE=false
for arg in "$@"; do
  [[ "$arg" == "--docker" ]] && DOCKER_MODE=true
done

echo "============================================================"
echo "  Minecraft Cloud Platform — Integration Test Suite"
echo "============================================================"
echo ""

# ── 1. Python unit + API tests ─────────────────────────────────────────────
echo "[1/3] Running Python backend test suite..."
echo "--------------------------------------------------------------"
python -m pytest backend/tests/ -v --tb=short 2>&1
UNIT_STATUS=$?

if [[ $UNIT_STATUS -eq 0 ]]; then
  echo ""
  echo "✅  All backend unit/integration tests passed."
else
  echo ""
  echo "❌  Backend tests failed (exit code $UNIT_STATUS)."
fi
echo ""

# ── 2. Docker Compose smoke test ──────────────────────────────────────────
if [[ "$DOCKER_MODE" == "true" ]]; then
  echo "[2/3] Running Docker Compose smoke tests..."
  echo "--------------------------------------------------------------"

  echo "  Starting services..."
  docker compose up -d --wait 2>&1 || true

  # Wait up to 60 s for the backend health endpoint
  echo "  Waiting for backend /health..."
  BACKEND_URL="http://localhost:${BACKEND_PORT:-8000}"
  HEALTHY=false
  for i in $(seq 1 12); do
    if curl -sf "$BACKEND_URL/health" > /dev/null 2>&1; then
      HEALTHY=true
      break
    fi
    echo "    ...attempt $i/12 (5 s)"
    sleep 5
  done

  if [[ "$HEALTHY" == "true" ]]; then
    echo "  Backend is healthy."
    # Quick API smoke tests
    echo "  Testing /health endpoint..."
    HEALTH_JSON=$(curl -sf "$BACKEND_URL/health")
    echo "  Response: $HEALTH_JSON"
    if echo "$HEALTH_JSON" | grep -q '"status":"ok"'; then
      echo "✅  Docker smoke test passed."
      DOCKER_STATUS=0
    else
      echo "❌  Unexpected /health response."
      DOCKER_STATUS=1
    fi
  else
    echo "❌  Backend did not become healthy within 60 s."
    docker compose logs backend --tail=30
    DOCKER_STATUS=1
  fi
  echo ""
else
  echo "[2/3] Docker smoke test skipped (pass --docker to enable)."
  DOCKER_STATUS=0
  echo ""
fi

# ── 3. Frontend build verification ────────────────────────────────────────
echo "[3/3] Verifying frontend production build..."
echo "--------------------------------------------------------------"
(cd frontend && npm run build 2>&1)
FRONTEND_STATUS=$?
if [[ $FRONTEND_STATUS -eq 0 ]]; then
  echo "✅  Frontend build succeeded."
else
  echo "❌  Frontend build failed."
fi
echo ""

# ── Summary ────────────────────────────────────────────────────────────────
echo "============================================================"
echo "  INTEGRATION TEST SUMMARY"
echo "============================================================"
echo "  Backend tests  : $([ $UNIT_STATUS    -eq 0 ] && echo 'PASS ✅' || echo 'FAIL ❌')"
echo "  Docker smoke   : $([ $DOCKER_STATUS  -eq 0 ] && echo 'PASS ✅' || echo 'FAIL ❌  (or skipped)')"
echo "  Frontend build : $([ $FRONTEND_STATUS -eq 0 ] && echo 'PASS ✅' || echo 'FAIL ❌')"
echo "============================================================"

OVERALL=0
[[ $UNIT_STATUS -ne 0 ]] && OVERALL=1
[[ $DOCKER_STATUS -ne 0 ]] && OVERALL=1
[[ $FRONTEND_STATUS -ne 0 ]] && OVERALL=1

if [[ $OVERALL -eq 0 ]]; then
  echo "  ALL CHECKS PASSED 🎉"
else
  echo "  SOME CHECKS FAILED — review output above."
fi
echo "============================================================"
exit $OVERALL
