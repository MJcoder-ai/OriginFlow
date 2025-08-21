#!/usr/bin/env bash
set -euo pipefail

# Simple end-to-end smoke test for CI and local use.
# It boots the API, creates a session, asks for a plan, executes the tasks, and checks the view.

PORT="${PORT:-8001}"
HOST="127.0.0.1"
BASE="http://${HOST}:${PORT}/api/v1"
SID="ci-smoke-$RANDOM"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq not found; attempting to install (apt-get)..." >&2
  if command -v sudo >/dev/null 2>&1; then
    sudo apt-get update -y && sudo apt-get install -y jq
  else
    echo "jq is required for smoke test" >&2
    exit 1
  fi
fi

cleanup() {
  if [[ -n "${UVICORN_PID:-}" ]]; then
    kill "${UVICORN_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "[smoke] preparing database and starting server..."
mkdir -p .localdb
export DATABASE_URL="sqlite+aiosqlite:///$PWD/.localdb/originflow.db"

poetry run uvicorn backend.main:app --host "${HOST}" --port "${PORT}" --log-level warning &
UVICORN_PID=$!

# Wait for server
for i in {1..60}; do
  if curl -fsS "${BASE}/components/" >/dev/null 2>&1; then
    break
  fi
  sleep 1
  if ! kill -0 "${UVICORN_PID}" >/dev/null 2>&1; then
    echo "[smoke] server process exited unexpectedly" >&2
    exit 1
  fi
done

echo "[smoke] create session: ${SID}"
CREATE=$(curl -fsS -X POST "${BASE}/odl/sessions?session_id=${SID}")
VER=$(echo "${CREATE}" | jq -r '.version // 0')
if [[ "${VER}" == "0" || -z "${VER}" ]]; then
  echo "[smoke] failed to create session: ${CREATE}" >&2
  exit 1
fi

echo "[smoke] planner (single-line layer)"
PLAN=$(curl -fsS "${BASE}/odl/sessions/${SID}/plan?command=$(python3 -c "import urllib.parse; print(urllib.parse.quote('design a 5kW solar PV system'))")&layer=single-line")
PANEL_COUNT=$(echo "${PLAN}" | jq -r '.tasks[] | select(.id=="make_placeholders" and .args.component_type=="panel") | .args.count')
if [[ -z "${PANEL_COUNT}" ]]; then
  echo "[smoke] planner did not return a panel task: ${PLAN}" >&2
  exit 1
fi

HEAD() { curl -fsS "${BASE}/odl/${SID}/head" | jq -r '.version'; }

CURV=$(HEAD)
echo "[smoke] act: inverter (If-Match ${CURV})"
INV=$(curl -fsS -X POST "${BASE}/ai/act" \
  -H "Content-Type: application/json" \
  -H "If-Match: ${CURV}" \
  -d '{"session_id":"'"${SID}"'","task":"make_placeholders","request_id":"r1","args":{"component_type":"inverter","count":1,"layer":"single-line"}}')
CURV=$(HEAD)

echo "[smoke] act: panels x${PANEL_COUNT} (If-Match ${CURV})"
PAN=$(curl -fsS -X POST "${BASE}/ai/act" \
  -H "Content-Type: application/json" \
  -H "If-Match: ${CURV}" \
  -d '{"session_id":"'"${SID}"'","task":"make_placeholders","request_id":"r2","args":{"component_type":"panel","count":'"${PANEL_COUNT}"',"layer":"single-line"}}')
CURV=$(HEAD)

echo "[smoke] act: generate wiring (If-Match ${CURV})"
WIR=$(curl -fsS -X POST "${BASE}/ai/act" \
  -H "Content-Type: application/json" \
  -H "If-Match: ${CURV}" \
  -d '{"session_id":"'"${SID}"'","task":"generate_wiring","request_id":"r3","args":{"layer":"single-line"}}')

echo "[smoke] verify view (single-line layer)"
VIEW=$(curl -fsS "${BASE}/odl/${SID}/view?layer=single-line")
NODES=$(echo "${VIEW}" | jq '.nodes | length')
EDGES=$(echo "${VIEW}" | jq '.edges | length')

if [[ "${NODES}" -lt 2 || "${EDGES}" -lt 1 ]]; then
  echo "[smoke] unexpected view (need at least inverter + one panel and one link): ${VIEW}" >&2
  exit 1
fi

echo "[smoke] verify text endpoint"
TEXT=$(curl -fsS "${BASE}/odl/sessions/${SID}/text?layer=single-line" | jq -r '.text')
echo "${TEXT}" | grep -q "node" || { echo "[smoke] text endpoint missing node lines" >&2; exit 1; }
echo "${TEXT}" | grep -q "link" || { echo "[smoke] text endpoint missing link lines" >&2; exit 1; }

echo "[smoke] OK (nodes=${NODES}, edges=${EDGES})"
