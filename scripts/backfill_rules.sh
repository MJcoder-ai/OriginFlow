#!/usr/bin/env bash
# Backfill OriginFlow recording rules into Prometheus TSDB via a short-lived Job.
# Safely scales the Prometheus StatefulSet down (unless --no-scale), mounts its PVC,
# runs promtool to generate TSDB blocks for the requested window, copies them into /prometheus,
# and scales the StatefulSet back up. Requires cluster RBAC to scale and create Job.
#
# Usage:
#   scripts/backfill_rules.sh \
#     --start 2025-08-01T00:00:00Z \
#     --end 2025-08-19T00:00:00Z \
#     [--step 30s] \
#     [--ns monitoring] \
#     [--prom-url http://prometheus-k8s.monitoring.svc.cluster.local:9090] \
#     [--pvc prometheus-prometheus-k8s-db-prometheus-k8s-0] \
#     [--rules-cm originflow-recording-rules] \
#     [--rules-file infra/prometheus/rules/originflow-recording.rules.yml] \
#     [--prom-sts prometheus-k8s] \
#     [--image prom/prometheus:v2.52.0] \
#     [--keep-job] [--no-scale]
#
# Notes:
# - The rules ConfigMap must exist or will be created from --rules-file.
# - The PVC name is cluster-specific; override --pvc to match your environment.
# - Prometheus version and image tag should match your running Prometheus.

set -euo pipefail

START=""
END=""
STEP="30s"
NS="monitoring"
PROM_URL="http://prometheus-k8s.monitoring.svc.cluster.local:9090"
PVC="prometheus-prometheus-k8s-db-prometheus-k8s-0"
RULES_CM="originflow-recording-rules"
RULES_FILE="infra/prometheus/rules/originflow-recording.rules.yml"
STS="prometheus-k8s"
IMAGE="prom/prometheus:v2.52.0"
KEEP_JOB="0"
NO_SCALE="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --start) START="${2:-}"; shift 2;;
    --end) END="${2:-}"; shift 2;;
    --step) STEP="${2:-}"; shift 2;;
    --ns) NS="${2:-}"; shift 2;;
    --prom-url) PROM_URL="${2:-}"; shift 2;;
    --pvc) PVC="${2:-}"; shift 2;;
    --rules-cm) RULES_CM="${2:-}"; shift 2;;
    --rules-file) RULES_FILE="${2:-}"; shift 2;;
    --prom-sts) STS="${2:-}"; shift 2;;
    --image) IMAGE="${2:-}"; shift 2;;
    --keep-job) KEEP_JOB="1"; shift 1;;
    --no-scale) NO_SCALE="1"; shift 1;;
    -h|--help)
      sed -n '1,50p' "$0"; exit 0;;
    *)
      echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

if [[ -z "${START}" || -z "${END}" ]]; then
  echo "ERROR: --start and --end are required (ISO8601 UTC recommended)" >&2
  exit 1
fi

command -v kubectl >/dev/null 2>&1 || { echo "kubectl not found"; exit 1; }

JOB_NAME="originflow-promtool-backfill-$(date -u +%s)"

echo "==> Namespace: ${NS}"
echo "==> Prometheus STS: ${STS}"
echo "==> PVC: ${PVC}"
echo "==> Prometheus query URL: ${PROM_URL}"
echo "==> Window: ${START} .. ${END} (step=${STEP})"
echo "==> Rules CM: ${RULES_CM} (from ${RULES_FILE})"
echo "==> Image: ${IMAGE}"
echo "==> Job: ${JOB_NAME}"
echo

echo "==> Ensuring rules ConfigMap exists..."
if ! kubectl -n "${NS}" get configmap "${RULES_CM}" >/dev/null 2>&1; then
  kubectl -n "${NS}" create configmap "${RULES_CM}" \
    --from-file="$(basename "${RULES_FILE}")=${RULES_FILE}"
else
  echo "ConfigMap ${RULES_CM} already exists; skip create."
fi

SCALED=0
if [[ "${NO_SCALE}" != "1" ]]; then
  echo "==> Scaling down StatefulSet ${STS} ..."
  kubectl -n "${NS}" scale sts "${STS}" --replicas=0
  echo "Waiting for scale-down..."
  kubectl -n "${NS}" rollout status sts "${STS}" --timeout=5m || true
  SCALED=1
else
  echo "==> --no-scale set; NOT scaling ${STS}."
fi

echo "==> Creating backfill Job ${JOB_NAME} ..."
cat <<YAML | kubectl -n "${NS}" apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: ${JOB_NAME}
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: promtool
          image: ${IMAGE}
          imagePullPolicy: IfNotPresent
          command:
            - /bin/sh
            - -lc
            - |
              set -euo pipefail
              echo "Backfill window: ${START} .. ${END} step ${STEP}"
              promtool tsdb create-blocks-from rules \
                --start="${START}" \
                --end="${END}" \
                --step="${STEP}" \
                --out=/tmp/of-backfill \
                --query-url="${PROM_URL}" \
                /etc/originflow/rules/originflow-recording.rules.yml
              echo "Copying blocks into /prometheus ..."
              cp -r /tmp/of-backfill/* /prometheus/ || true
              echo "Backfill done."
          volumeMounts:
            - name: prom-data
              mountPath: /prometheus
            - name: rules
              mountPath: /etc/originflow/rules
      volumes:
        - name: prom-data
          persistentVolumeClaim:
            claimName: ${PVC}
        - name: rules
          configMap:
            name: ${RULES_CM}
            items:
              - key: originflow-recording.rules.yml
                path: originflow-recording.rules.yml
YAML

echo "==> Waiting for completion ..."
set +e
kubectl -n "${NS}" wait --for=condition=complete job/"${JOB_NAME}" --timeout=2h
RC=$?
set -e

echo "==> Fetching logs ..."
kubectl -n "${NS}" logs job/"${JOB_NAME}" --all-containers=true || true

if [[ "${KEEP_JOB}" != "1" ]]; then
  echo "==> Cleaning up Job ${JOB_NAME} ..."
  kubectl -n "${NS}" delete job "${JOB_NAME}" --ignore-not-found
else
  echo "==> --keep-job set; keeping Job ${JOB_NAME} for inspection."
fi

if [[ "${SCALED}" == "1" ]]; then
  echo "==> Scaling StatefulSet ${STS} back up ..."
  kubectl -n "${NS}" scale sts "${STS}" --replicas=1
  kubectl -n "${NS}" rollout status sts "${STS}" --timeout=5m || true
fi

if [[ "${RC}" -ne 0 ]]; then
  echo "ERROR: Job did not complete successfully." >&2
  exit "${RC}"
fi

echo "==> Backfill complete."
