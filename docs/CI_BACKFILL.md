# CI Backfill Workflow

This repository includes a GitHub Actions workflow:

- `.github/workflows/backfill-recording-rules.yml`

It **detects** your Prometheus StatefulSet and PVC, **caches** those detection
outputs with the **chosen time window**, and **triggers** the Kubernetes Job to
backfill recorded series (p95 latency and avg/p95 sizes).

## Prerequisites

1. **Cluster access** for the GitHub runner:
   - Create a repository secret `KUBECONFIG_DATA` containing either:
     - a **base64-encoded** kubeconfig, or
     - a **plain-text** kubeconfig (the workflow detects and handles both).
2. Ensure the recording rules are present (Operator CR or `.rules` file), and the
   helper artifacts exist:
   - `infra/k8s/monitoring/prometheusrule-originflow.yaml`
   - `infra/prometheus/rules/originflow-recording.rules.yml`
   - `scripts/backfill_rules.sh` (executable)
   - `Makefile.backfill.mk`

## Running the workflow

Open **Actions → Backfill recorded series (Prometheus)** → **Run workflow**.

Inputs:
- `window_hours` (default `24`) – used if `start` is empty.
- `start` / `end` – ISO8601 UTC (`2025-08-01T00:00:00Z`). If `end` empty, defaults to now (UTC).
- `step` – promtool evaluation step (default `30s`).
- `ns` – namespace (default `monitoring`).
- `release` – Helm release (optional) to narrow detection
  (`app.kubernetes.io/instance=<release>`).
- `prom_url` – override Prometheus query URL (else Makefile default applies).
- `keep_job` – keep the backfill Job post-run (default false).
- `no_scale` – do **not** scale Prometheus STS (advanced; default false).
- `dry_run` – detect + cache + artifact only; **no** backfill Job executed.

Guardrails:
- `BACKFILL_MAX_HOURS=168` (7 days) – requests beyond this limit **fail fast**.

## What the workflow does
1. **Computes the window** (`start`, `end`) with guardrails.
2. **Detects** the Prometheus STS/PVC using `make detect-prom-vars`.
3. **Caches** detection + window under `.cache/backfill` via `actions/cache`.
4. **Uploads artifacts** (`backfill_vars.env`, `backfill_window.env`).
5. **Runs backfill** using `make backfill-rules-auto` unless `dry_run=true`.

## Outputs & artifacts
- `backfill_vars.env` – contains `PROM_STS=<name>` and `PROM_PVC=<name>`.
- `backfill_window.env` – contains the resolved `start` and `end` timestamps.
- Cached copies under `.cache/backfill` (cache key includes branch/ref, ns, release).

## Safety notes
- Use `dry_run=true` first to verify detection in your cluster.
- The workflow can scale the Prometheus StatefulSet **down** to mount its PVC;
  set `no_scale=true` only if you know the PVC can be mounted concurrently (not typical).
- Prefer modest windows (24–72 hours); large windows increase promtool load and write size.

## Tuning
- Adjust `BACKFILL_MAX_HOURS` in the workflow environment.
- Override Prometheus image/version in `Makefile.backfill.mk` if needed.

