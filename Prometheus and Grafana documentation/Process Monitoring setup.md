Process-wise CPU & Memory Monitoring Setup (Prometheus + Grafana + Alertmanager)

This guide provides an all-in-one implementation to monitor CPU and memory usage per process in Red Hat servers using Prometheus, Node Exporter (textfile collector), Alertmanager, and Grafana.


---

🔧 Overview

Components

Node Exporter (textfile collector enabled)

Custom process monitor script (process_monitor.sh)

Prometheus with process alert rules

Alertmanager with HTML templates

Grafana dashboard for visualization


Key Metrics

Metric	Description

process_cpu_percent{process="<name>"}	CPU usage per process (sum of %CPU of all PIDs with the same name)
process_memory_bytes{process="<name>"}	Total RSS memory (bytes) per process name
process_count{process="<name>"}	Number of processes with that name



---

🚀 Installation Script

> Run this as root on each target Red Hat server.



#!/bin/bash
set -euo pipefail

# --- Variables ---
NODE_USER="marigold"
TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
PROCESS_METRIC_FILE="$TEXTFILE_DIR/process_metrics.prom"
PROCESS_SCRIPT="/usr/local/bin/process_monitor.sh"
NODE_EXPORTER_SYSTEMD="/etc/systemd/system/node_exporter.service"
PROM_RULE_DIR="/etc/prometheus/rules"
PROM_PROCESS_RULE="$PROM_RULE_DIR/process_alerts.yml"
ALERT_TMPL_DIR="/etc/alertmanager/templates"
ALERT_TMPL_FILE="$ALERT_TMPL_DIR/process_alerts.tmpl"
GRAFANA_DASH_JSON="/tmp/grafana-process-dashboard.json"
COLLECT_INTERVAL=30

# --- 1) Textfile Collector Directory ---
mkdir -p "$TEXTFILE_DIR"
chown -R "$NODE_USER":"$NODE_USER" "$TEXTFILE_DIR"
chmod 755 "$TEXTFILE_DIR"

# --- 2) Update node_exporter systemd ---
if ! grep -q -- "--collector.textfile.directory=" "$NODE_EXPORTER_SYSTEMD" 2>/dev/null; then
  sed -i '/ExecStart=/c\\ExecStart=/usr/local/bin/node_exporter --collector.textfile.directory='"$TEXTFILE_DIR" "$NODE_EXPORTER_SYSTEMD"
fi
systemctl daemon-reload
systemctl enable --now node_exporter
systemctl restart node_exporter

# --- 3) Create Process Monitoring Script ---
cat > "$PROCESS_SCRIPT" <<'EOF'
#!/bin/bash
METRIC_FILE="${PROCESS_METRIC_FILE:-/var/lib/node_exporter/textfile_collector/process_metrics.prom}"
TMPFILE="${METRIC_FILE}.tmp.$$"

ps -eo comm,pcpu,rss --no-headers | \
awk '{
  cmd=$1;
  if (cmd ~ /^\[/) next;
  cpu=$2+0; rss=$3+0;
  count[cmd]+=1;
  cpu_sum[cmd]+=cpu;
  rss_sum[cmd]+=rss;
}
END {
  printf "# HELP process_cpu_percent Total CPU percent aggregated per process name\n";
  printf "# TYPE process_cpu_percent gauge\n";
  for (p in cpu_sum) printf "process_cpu_percent{process=\"%s\"} %.3f\n", p, cpu_sum[p];
  printf "\n# HELP process_memory_bytes Total RSS memory (bytes) per process name\n";
  printf "# TYPE process_memory_bytes gauge\n";
  for (p in rss_sum) printf "process_memory_bytes{process=\"%s\"} %.0f\n", p, rss_sum[p]*1024;
  printf "\n# HELP process_count Number of processes per process name\n";
  printf "# TYPE process_count gauge\n";
  for (p in count) printf "process_count{process=\"%s\"} %d\n", p, count[p];
}' > "$TMPFILE"

mv "$TMPFILE" "$METRIC_FILE"
chown marigold:marigold "$METRIC_FILE" 2>/dev/null || true
chmod 644 "$METRIC_FILE"
EOF

chmod +x "$PROCESS_SCRIPT"

# --- 4) Systemd Service + Timer ---
cat > /etc/systemd/system/process_monitor.service <<EOF
[Unit]
Description=Collect process CPU/memory stats for Prometheus
[Service]
Type=oneshot
ExecStart=$PROCESS_SCRIPT
EOF

cat > /etc/systemd/system/process_monitor.timer <<EOF
[Unit]
Description=Run process_monitor every ${COLLECT_INTERVAL}s
[Timer]
OnBootSec=${COLLECT_INTERVAL}s
OnUnitActiveSec=${COLLECT_INTERVAL}s
Unit=process_monitor.service
[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now process_monitor.timer
systemctl start process_monitor.service

# --- 5) Prometheus Alert Rules ---
mkdir -p "$PROM_RULE_DIR"
cat > "$PROM_PROCESS_RULE" <<'YAML'
groups:
  - name: process-alerts
    rules:
      - alert: ProcessHighCPU
        expr: process_cpu_percent > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High process CPU usage: {{ $labels.process }}"
          description: "Process {{ $labels.process }} using {{ printf \"%.2f\" $value }}% CPU on {{ $labels.instance }}"

      - alert: ProcessHighMemory
        expr: process_memory_bytes > 524288000
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "High process memory usage: {{ $labels.process }}"
          description: "Process {{ $labels.process }} using >500MB memory on {{ $labels.instance }}"
YAML

# --- 6) Alertmanager Template ---
mkdir -p "$ALERT_TMPL_DIR"
cat > "$ALERT_TMPL_FILE" <<'EOF'
{{ define "process_alert.tmpl" }}
{{ range .Alerts }}
<html>
<body style="font-family: Arial, sans-serif;">
  <h3>Process Alert: {{ .Labels.alertname }}</h3>
  <p><b>Instance:</b> {{ .Labels.instance }}</p>
  <p><b>Process:</b> {{ .Labels.process }}</p>
  <p><b>Severity:</b> {{ .Labels.severity }}</p>
  <p><b>Details:</b> {{ .Annotations.description }}</p>
  <p><b>Suggested Commands:</b></p>
  <ul>
    <li><code>top -o %CPU</code></li>
    <li><code>ps -eo pid,comm,pcpu,pmem,rss --sort=-pcpu | head -n 10</code></li>
  </ul>
</body>
</html>
{{ end }}
{{ end }}
EOF

# --- 7) Grafana Dashboard JSON ---
cat > "$GRAFANA_DASH_JSON" <<'EOF'
{
  "title": "Process CPU & Memory Usage",
  "panels": [
    { "type": "graph", "title": "Top 10 Processes by CPU", "targets": [{ "expr": "topk(10, process_cpu_percent)", "legendFormat": "{{process}}" }] },
    { "type": "graph", "title": "Top 10 Processes by Memory", "targets": [{ "expr": "topk(10, process_memory_bytes)", "legendFormat": "{{process}}" }] }
  ]
}
EOF

echo "✅ Process monitoring setup complete!"
echo "Prometheus rules: $PROM_PROCESS_RULE"
echo "Alertmanager template: $ALERT_TMPL_FILE"
echo "Grafana dashboard: $GRAFANA_DASH_JSON"


---

⚙️ Prometheus Configuration

Add to /etc/prometheus/prometheus.yml:

rule_files:
  - "/etc/prometheus/rules/*.yml"

Reload Prometheus:

systemctl reload prometheus


---

📧 Alertmanager Configuration

Add to /etc/alertmanager/alertmanager.yml:

templates:
  - '/etc/alertmanager/templates/process_alerts.tmpl'

routes:
  - match_re:
      alertname: ProcessHighCPU
    receiver: email-receiver

  - match_re:
      alertname: ProcessHighMemory
    receiver: email-receiver-memory

Reload Alertmanager:

systemctl reload alertmanager


---

📊 Grafana Setup

1. Go to Grafana → Dashboards → Import


2. Upload /tmp/grafana-process-dashboard.json


3. Select Prometheus as the data source


4. Save and view process metrics in real-time




---

✅ Verification

systemctl status process_monitor.timer
cat /var/lib/node_exporter/textfile_collector/process_metrics.prom

Prometheus Queries:

topk(10, process_cpu_percent)
topk(10, process_memory_bytes)


---

🧩 Notes

Adjust thresholds in /etc/prometheus/rules/process_alerts.yml

Timer frequency matches Prometheus scrape_interval

Works on all Red Hat-compatible systems

Extendable for disk I/O or specific process groups



---

📄 License

Free to use and modify for Prometheus + Grafana environments.

