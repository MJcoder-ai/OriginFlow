# Backfilling Recording Rules (Ops Playbook)

This guide shows how to precompute the **recorded series** we added
(`*:p95_5m_by_*`, `*:avg_5m_by_*`, etc.) over a historical window so your
dashboards don’t look “flat” right after rollout.

You have three approaches—pick one:

---
## A) Simple warm-up (no true backfill)
**When to use:** You just rolled out the rules and can wait ~5–15 minutes.

1. Deploy the recording rules (see `prometheusrule-originflow.yaml`).
2. Leave dashboards as-is. Panels will fill as Prometheus evaluates rules going forward.

Pros: zero risk; no migration work.  
Cons: panels don’t show history prior to rollout.

---
## B) Offline backfill with `promtool` (create TSDB blocks)
**When to use:** You want historical values for the recorded series.

### Prereqs
- The **Prometheus version** of `promtool` should match your server minor version.
- Your Prometheus **query endpoint** (e.g. `http://prometheus:9090`) must have
  the raw base metrics retained for the period you want to backfill.
- Enough disk space to write generated blocks.

### Command (standalone)
Evaluate the recording rules for a time window and generate blocks:
```bash
promtool tsdb create-blocks-from rules \
  --start=2025-08-01T00:00:00Z \
  --end=2025-08-19T00:00:00Z \
  --step=30s \
  --out=/tmp/of-backfill \
  --query-url=http://prometheus.monitoring.svc:9090 \
  infra/prometheus/rules/originflow-recording.rules.yml
```
Notes:
- `--start/--end`: the historical window to precompute.
- `--step`: match your evaluation interval (e.g., 30s/60s).
- `--query-url`: points to the Prometheus that has the base series.
- Multiple rule files are supported—pass them all.

You’ll get one or more **TSDB block directories** in `/tmp/of-backfill`.

### Import blocks into Prometheus TSDB (local / VM / container)
> **Important:** Only write blocks when the server is stopped, or into the same PVC without an active Prometheus Pod.

1. **Scale down** Prometheus (if in K8s):
   ```bash
   kubectl -n monitoring scale sts prometheus-k8s --replicas=0
   ```
2. **Back up** the data dir (precaution).
3. **Copy** generated blocks into the Prometheus data directory (e.g., `/prometheus`).
4. **Scale up** Prometheus:
   ```bash
   kubectl -n monitoring scale sts prometheus-k8s --replicas=1
   ```
Prometheus will discover the new blocks at startup.

### Verification
Open Grafana or run PromQL:
```promql
http_request_duration_seconds:p95_5m_by_route_tenant[1h]
```
You should see historical samples within the backfilled window.

**Rollback:** remove the imported block folders (by ULID) and restart Prometheus.

---
## C) Kubernetes Job that writes blocks to the Prometheus PVC
**When to use:** You want a reproducible cluster-native backfill without copying files by hand.

Flow:
1. Scale Prometheus **down** (to free the PVC mount).
2. Run a short-lived **Job** that mounts the same PVC, runs `promtool`, and writes blocks directly to `/prometheus`.
3. Scale Prometheus **up**.

Ensure the `originflow-recording-rules` ConfigMap exists (see deploy guide) so the Job can mount the rules.

See `infra/k8s/tools/promtool-backfill-job.yaml` for a template.

---
## Tips & Caveats
- Keep backfill windows **reasonable** (e.g., days to weeks, not years) to limit load on the source Prometheus.
- For multi-tenant data, ensure your source Prometheus has **all** tenant labels and retention required.
- If you run **Thanos** or long-term storage, you can also backfill using a Thanos Ruler workflow—but that’s more involved and not covered here.


---
## One-liner via Makefile + helper script
If you prefer a simple, parameterized command:

```bash
# Make the helper executable once
chmod +x scripts/backfill_rules.sh

# Run backfill in one line (keeps defaults for ns/pvc/prom-url/etc.)
make -f Makefile.backfill.mk backfill-rules \
  BACKFILL_START=2025-08-01T00:00:00Z \
  BACKFILL_END=2025-08-19T00:00:00Z
```

Advanced options:
```bash
make -f Makefile.backfill.mk backfill-rules \
  BACKFILL_START=2025-08-01T00:00:00Z BACKFILL_END=2025-08-19T00:00:00Z \
  BACKFILL_STEP=60s NS=monitoring \
  PROM_QUERY_URL=http://prometheus-k8s.monitoring.svc.cluster.local:9090 \
  PROM_PVC=prometheus-prometheus-k8s-db-prometheus-k8s-0 \
  RULES_CM=originflow-recording-rules \
  RULES_FILE=infra/prometheus/rules/originflow-recording.rules.yml \
  PROM_STS=prometheus-k8s \
  IMAGE=prom/prometheus:v2.52.0 \
  KEEP_JOB=1
```

### Auto-detect Prometheus STS/PVC, then backfill
If you use kube-prometheus-stack or upstream kube-prometheus and don’t want to
manually pass the StatefulSet and PVC names:
```bash
make -f Makefile.backfill.mk backfill-rules-auto \
  BACKFILL_START=2025-08-01T00:00:00Z \
  BACKFILL_END=2025-08-19T00:00:00Z \
  RELEASE=kube-prometheus-stack   # optional; narrows by app.k8s.io/instance
```
To only print detected values:
```bash
make -f Makefile.backfill.mk detect-prom-vars [RELEASE=kube-prometheus-stack]
```
The target:
- Looks for StatefulSets with `app.kubernetes.io/name=prometheus` (and `app.kubernetes.io/instance=$RELEASE` if provided),
- Picks the most recent one,
- Reads its first `volumeClaimTemplates[].metadata.name`,
- Forms the PVC name as `<template>-<sts>-0`.

## CI-driven backfill (GitHub Actions)
You can run the entire detection → cache → backfill flow from CI:

- See [CI_BACKFILL.md](CI_BACKFILL.md)
- Workflow file: `.github/workflows/backfill-recording-rules.yml`

This is the recommended approach for repeatable, auditable operations.

