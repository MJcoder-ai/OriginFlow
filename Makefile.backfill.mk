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
