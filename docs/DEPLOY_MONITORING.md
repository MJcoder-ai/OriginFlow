# Deploying Observability on Kubernetes (Prometheus Operator + Grafana)

This guide wires OriginFlow metrics into **Prometheus Operator** and auto-imports dashboards into **Grafana**.

## Prereqs
- Prometheus Operator installed (e.g., kube-prometheus-stack)
- Grafana with the **sidecar** that watches ConfigMaps labeled `grafana_dashboard: "1"` and `grafana_datasource: "1"`
- Your backend Service exposes `/metrics` on the selected port.

## 1) ServiceMonitor
Edit `infra/k8s/monitoring/servicemonitor-originflow-backend.yaml` if needed:
- `metadata.labels.release` must match your Prometheus’ `serviceMonitorSelector` labels.
- `selector.matchLabels` must match the **Service** that fronts the OriginFlow backend.
- Ensure the Service exposes a port named `http` (or change the endpoint to `targetPort: 8000`).

Apply:
```bash
kubectl apply -f infra/k8s/monitoring/servicemonitor-originflow-backend.yaml
```

## 2) Prometheus alerts
Apply:
```bash
kubectl apply -f infra/k8s/monitoring/prometheusrule-originflow.yaml
```

## 3) Grafana datasource (Prometheus)
Set an environment variable on Grafana: `PROMETHEUS_URL` (e.g., `http://prometheus-operated:9090`).
Then apply:
```bash
kubectl apply -f infra/k8s/monitoring/grafana-datasource-prometheus.yaml
```

If you do **not** use env expansion in provisioning, edit the YAML to put a literal URL in `url:`.

## 4) Grafana dashboards
Sidecar-friendly approach (recommended):
```bash
kubectl -n monitoring create configmap grafana-dashboard-originflow-policy-approvals \
  --from-file=originflow-policy-approvals.json=infra/grafana/dashboards/originflow-policy-approvals.json \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n monitoring create configmap grafana-dashboard-originflow-slo \
  --from-file=originflow-slo.json=infra/grafana/dashboards/originflow-slo.json \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n monitoring create configmap grafana-dashboard-originflow-http \
  --from-file=originflow-http.json=infra/grafana/dashboards/originflow-http.json \
  --dry-run=client -o yaml | kubectl apply -f -
```
The sidecar will auto-import them within ~30s.

For **file provisioning** instead of sidecar:
1. `kubectl apply -f infra/k8s/monitoring/grafana-dashboards-provider.yaml`
2. Create a ConfigMap from the dashboards and mount it at `/var/lib/grafana/dashboards/originflow`.

## 5) Verify
Prometheus target:
- In Prometheus UI, check **Status → Targets** for the ServiceMonitor and confirm `up == 1`.

Grafana:
- Check **Dashboards → Browse** for the *OriginFlow* folder and open **OriginFlow • Policy & Approvals** and **OriginFlow • Service SLO**.

Alerts:
- In Alertmanager (or Prometheus UI), confirm alert rules load; provoke a test (e.g., disable redis temporarily) to see cache miss alert.
