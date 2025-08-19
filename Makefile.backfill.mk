# Standalone Makefile for OriginFlow recording-rule backfill.
# Use without modifying your main Makefile:
#   make -f Makefile.backfill.mk backfill-rules \\
#     BACKFILL_START=2025-08-01T00:00:00Z BACKFILL_END=2025-08-19T00:00:00Z

.PHONY: backfill-rules help

# Required:
BACKFILL_START ?=
BACKFILL_END   ?=

# Optional:
BACKFILL_STEP  ?= 30s
NS             ?= monitoring
PROM_QUERY_URL ?= http://prometheus-k8s.monitoring.svc.cluster.local:9090
PROM_PVC       ?= prometheus-prometheus-k8s-db-prometheus-k8s-0
RULES_CM       ?= originflow-recording-rules
RULES_FILE     ?= infra/prometheus/rules/originflow-recording.rules.yml
PROM_STS       ?= prometheus-k8s
IMAGE          ?= prom/prometheus:v2.52.0
KEEP_JOB       ?= 0
NO_SCALE       ?= 0
RELEASE        ?=    # Optional Helm release name for kube-prometheus-stack (e.g., kube-prometheus-stack)

KEEP_JOB_FLAG   := $(if $(filter 1,$(KEEP_JOB)),--keep-job,)
NO_SCALE_FLAG   := $(if $(filter 1,$(NO_SCALE)),--no-scale,)

backfill-rules:
	@if [ -z "$(BACKFILL_START)" ] || [ -z "$(BACKFILL_END)" ]; then \\
	echo "Usage: make -f Makefile.backfill.mk backfill-rules BACKFILL_START=... BACKFILL_END=... [BACKFILL_STEP=...]"; \\
	exit 1; \\
	fi
	./scripts/backfill_rules.sh \\
  --start "$(BACKFILL_START)" \\
  --end   "$(BACKFILL_END)" \\
  --step  "$(BACKFILL_STEP)" \\
  --ns    "$(NS)" \\
  --prom-url "$(PROM_QUERY_URL)" \\
  --pvc   "$(PROM_PVC)" \\
  --rules-cm "$(RULES_CM)" \\
  --rules-file "$(RULES_FILE)" \\
  --prom-sts "$(PROM_STS)" \\
  --image "$(IMAGE)" \\
  $(KEEP_JOB_FLAG) $(NO_SCALE_FLAG)

##
# Auto-detect Prometheus StatefulSet (STS) and its PVC in the given namespace
# and then perform the backfill using those values. If multiple STSs exist, the
# most recently created matching the label selector is chosen.
# You may pass RELEASE=<helm release> to narrow selection:
#   app.kubernetes.io/instance=$(RELEASE)
#
# Usage:
#   make -f Makefile.backfill.mk backfill-rules-auto \
#     BACKFILL_START=2025-08-01T00:00:00Z BACKFILL_END=2025-08-19T00:00:00Z [RELEASE=kube-prometheus-stack]
#
.PHONY: backfill-rules-auto detect-prom-vars
backfill-rules-auto:
	@if [ -z "$(BACKFILL_START)" ] || [ -z "$(BACKFILL_END)" ]; then \
	echo "Usage: make -f Makefile.backfill.mk backfill-rules-auto BACKFILL_START=... BACKFILL_END=... [RELEASE=...]"; \
	exit 1; \
	fi
	@set -euo pipefail; \
	if [ -n "$(RELEASE)" ]; then \
	  LS='app.kubernetes.io/name=prometheus,app.kubernetes.io/instance=$(RELEASE)'; \
	else \
	  LS='app.kubernetes.io/name=prometheus'; \
	fi; \
	echo "Label selector: $$LS"; \
	STS_DET=$$(kubectl -n "$(NS)" get sts -l "$$LS" -o jsonpath='{range .items[*]}{.metadata.creationTimestamp}{"|"}{.metadata.name}{"\n"}{end}' \
	  | sort -r \
	  | head -n1 \
	  | cut -d'|' -f2); \
	if [ -z "$$STS_DET" ]; then \
	  echo "WARN: Could not detect Prometheus STS via labels; falling back to 'prometheus-k8s'"; \
	  STS_DET="prometheus-k8s"; \
	fi; \
	PVC_TMPL=$$(kubectl -n "$(NS)" get sts "$$STS_DET" -o jsonpath='{.spec.volumeClaimTemplates[0].metadata.name}' 2>/dev/null || true); \
	if [ -z "$$PVC_TMPL" ]; then \
	  echo "WARN: Could not read volumeClaimTemplates; falling back to 'prometheus-db'"; \
	  PVC_TMPL="prometheus-db"; \
	fi; \
	PVC_DET="$${PVC_TMPL}-$$STS_DET-0"; \
	echo "Detected STS: $$STS_DET"; \
	echo "Detected PVC: $$PVC_DET"; \
	./scripts/backfill_rules.sh \
	  --start "$(BACKFILL_START)" \
	  --end   "$(BACKFILL_END)" \
	  --step  "$(BACKFILL_STEP)" \
	  --ns    "$(NS)" \
	  --prom-url "$(PROM_QUERY_URL)" \
	  --pvc   "$$PVC_DET" \
	  --rules-cm "$(RULES_CM)" \
	  --rules-file "$(RULES_FILE)" \
	  --prom-sts "$$STS_DET" \
	  --image "$(IMAGE)" \
	  $(KEEP_JOB_FLAG) $(NO_SCALE_FLAG)

# Print detected variables without running the backfill (useful for CI)
detect-prom-vars:
	@set -euo pipefail; \
	if [ -n "$(RELEASE)" ]; then \
	  LS='app.kubernetes.io/name=prometheus,app.kubernetes.io/instance=$(RELEASE)'; \
	else \
	  LS='app.kubernetes.io/name=prometheus'; \
	fi; \
	echo "Label selector: $$LS"; \
	STS_DET=$$(kubectl -n "$(NS)" get sts -l "$$LS" -o jsonpath='{range .items[*]}{.metadata.creationTimestamp}{"|"}{.metadata.name}{"\n"}{end}' \
	  | sort -r \
	  | head -n1 \
	  | cut -d'|' -f2); \
	if [ -z "$$STS_DET" ]; then STS_DET="prometheus-k8s"; fi; \
	PVC_TMPL=$$(kubectl -n "$(NS)" get sts "$$STS_DET" -o jsonpath='{.spec.volumeClaimTemplates[0].metadata.name}' 2>/dev/null || true); \
	if [ -z "$$PVC_TMPL" ]; then PVC_TMPL="prometheus-db"; fi; \
	PVC_DET="$${PVC_TMPL}-$$STS_DET-0"; \
	echo "PROM_STS=$$STS_DET"; \
	echo "PROM_PVC=$$PVC_DET"

help:
	@echo "Backfill recorded series into Prometheus TSDB using a one-liner:"
	@echo "  make -f Makefile.backfill.mk backfill-rules BACKFILL_START=2025-08-01T00:00:00Z BACKFILL_END=2025-08-19T00:00:00Z"
	@echo ""
	@echo "Optional vars:"
	@echo "  BACKFILL_STEP   (default: 30s)"
	@echo "  NS              (default: monitoring)"
	@echo "  PROM_QUERY_URL  (default: http://prometheus-k8s.monitoring.svc.cluster.local:9090)"
	@echo "  PROM_PVC        (default: prometheus-prometheus-k8s-db-prometheus-k8s-0)"
	@echo "  RULES_CM        (default: originflow-recording-rules)"
	@echo "  RULES_FILE      (default: infra/prometheus/rules/originflow-recording.rules.yml)"
	@echo "  PROM_STS        (default: prometheus-k8s)"
	@echo "  IMAGE           (default: prom/prometheus:v2.52.0)"
	@echo "  KEEP_JOB=1      (keep the Job after completion)"
	@echo "  NO_SCALE=1      (do not scale the Prometheus StatefulSet)"
	@echo ""
	@echo "Auto-detect STS/PVC and run backfill:"
	@echo "  make -f Makefile.backfill.mk backfill-rules-auto BACKFILL_START=... BACKFILL_END=... [RELEASE=kube-prometheus-stack]"
	@echo "Detect only (print vars):"
	@echo "  make -f Makefile.backfill.mk detect-prom-vars [RELEASE=kube-prometheus-stack]"
