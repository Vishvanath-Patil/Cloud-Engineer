
# Process-wise CPU & Memory Monitoring Setup (Prometheus + Node Exporter + Grafana)

This guide provides a **manual + script-based implementation** to monitor **process-wise CPU and memory usage** on Red Hat servers using **Prometheus**, **Node Exporter (textfile collector)**, and **Grafana**.

> ⚠️ This document excludes Prometheus and Alertmanager configuration changes (as requested). You will add rules and templates manually later.

---

## 🧩 Prerequisites

Before starting, verify your environment:

```bash
# 1. Check node_exporter binary path
ls -l /usr/local/bin/node_exporter

# 2. Check systemd unit file location
ls -l /etc/systemd/system/node_exporter.service || ls -l /lib/systemd/system/node_exporter.service

# 3. Verify node_exporter user (replace 'marigold' if different)
getent passwd marigold

# 4. Check Node Exporter metrics endpoint
curl -s http://localhost:9100/metrics | head -n 5
```

**Notes:**
- Update paths and usernames in the script to match your setup.
- Ensure Prometheus already scrapes Node Exporter (port 9100) for this server.
- Run all steps as `root` or with `sudo` privileges.

---

## Step 1️⃣ — Create the textfile collector directory

```bash
sudo mkdir -p /var/lib/node_exporter/textfile_collector
sudo chown -R marigold:marigold /var/lib/node_exporter/textfile_collector
sudo chmod 755 /var/lib/node_exporter/textfile_collector
ls -ld /var/lib/node_exporter/textfile_collector
```

**Notes:**
- Node Exporter’s textfile collector reads `.prom` files here.
- Directory must be readable by Node Exporter’s user.

If SELinux is enforcing:
```bash
sudo semanage fcontext -a -t var_run_t "/var/lib/node_exporter/textfile_collector(/.*)?"
sudo restorecon -Rv /var/lib/node_exporter/textfile_collector
```

---

## Step 2️⃣ — Enable the textfile collector in Node Exporter

```bash
sudo mkdir -p /etc/systemd/system/node_exporter.service.d
sudo tee /etc/systemd/system/node_exporter.service.d/10-textfile.conf > /dev/null <<'EOF'
[Service]
ExecStart=
ExecStart=/usr/local/bin/node_exporter --collector.textfile.directory=/var/lib/node_exporter/textfile_collector
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now node_exporter
sudo systemctl restart node_exporter
sudo systemctl status node_exporter --no-pager
ps aux | grep node_exporter | grep -v grep
```

**Notes:**
- Using a drop-in config ensures upgrades don’t overwrite your changes.
- Check `ps` output to confirm the `--collector.textfile.directory` flag.

---

## Step 3️⃣ — Create the process monitoring script

Create `/usr/local/bin/process_monitor.sh`:

```bash
sudo tee /usr/local/bin/process_monitor.sh > /dev/null <<'EOF'
#!/bin/bash
# process_monitor.sh - aggregate CPU, RSS memory, and process count by executable name
METRIC_FILE="/var/lib/node_exporter/textfile_collector/process_metrics.prom"
TMPFILE="${METRIC_FILE}.tmp.$$"

ps -eo comm,pcpu,rss --no-headers | awk '{
  cmd=$1;
  if (cmd ~ /^\[/) next;   # skip kernel threads
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

sudo chmod 755 /usr/local/bin/process_monitor.sh
sudo chown root:root /usr/local/bin/process_monitor.sh
```

**Notes:**
- `ps` collects CPU% and RSS (KB); `awk` aggregates by executable name.
- The metric file is atomically updated to prevent partial reads.
- File ownership is set to Node Exporter’s user.

---

## Step 4️⃣ — Create systemd service and timer

```bash
sudo tee /etc/systemd/system/process_monitor.service > /dev/null <<'EOF'
[Unit]
Description=Collect process CPU/memory stats for Node Exporter
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/process_monitor.sh
User=root
Group=root
EOF

sudo tee /etc/systemd/system/process_monitor.timer > /dev/null <<'EOF'
[Unit]
Description=Run process_monitor every 30s

[Timer]
OnBootSec=30s
OnUnitActiveSec=30s
Unit=process_monitor.service

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now process_monitor.timer
sudo systemctl start process_monitor.service
```

**Notes:**
- The timer runs every 30 seconds, aligned with Prometheus’ scrape interval.
- If Prometheus scrapes faster (e.g., 15s), reduce `OnUnitActiveSec` accordingly.

Verification:
```bash
systemctl status process_monitor.timer --no-pager
journalctl -u process_monitor.service -n 20 --no-pager
```

---

## Step 5️⃣ — Verify metrics are collected

```bash
/usr/local/bin/process_monitor.sh
ls -l /var/lib/node_exporter/textfile_collector
head -n 30 /var/lib/node_exporter/textfile_collector/process_metrics.prom
curl -s http://localhost:9100/metrics | grep process_cpu_percent -m 5
```

Expected sample:
```
process_cpu_percent{process="sshd"} 0.00
process_cpu_percent{process="java"} 32.11
process_memory_bytes{process="java"} 123456789
process_count{process="java"} 2
```

**Notes:**
- If file is empty, ensure `ps` command works and script permissions are correct.
- Node Exporter must be running with the textfile collector flag.

---

## Step 6️⃣ — Manual Grafana dashboard creation

1. **Go to Grafana → Dashboards → New → Import**  
2. Click **“New Panel”** and select your **Prometheus datasource**.
3. Add the following PromQL queries:

### Panel 1 — Top 10 Processes by CPU Usage
```promql
topk(10, process_cpu_percent)
```
- Visualization: Graph or Time series
- Legend: `{{process}}`
- Units: Percent (0–100)

### Panel 2 — Top 10 Processes by Memory Usage (MB)
```promql
topk(10, process_memory_bytes / 1024 / 1024)
```
- Visualization: Bar chart or Time series
- Units: Megabytes (MB)

### Panel 3 — Process Count
```promql
topk(15, process_count)
```
- Visualization: Table or Gauge

4. Adjust refresh rate (e.g., 30s or 1m).
5. Save dashboard as `Process CPU & Memory Monitoring`.

---

## Step 7️⃣ — One-shot setup script (excluding Prometheus & Alertmanager)

Save as `/tmp/setup-process-monitor.sh`:

```bash
#!/bin/bash
set -euo pipefail

NODE_USER="marigold"
TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
PROCESS_SCRIPT="/usr/local/bin/process_monitor.sh"
SERVICE_FILE="/etc/systemd/system/process_monitor.service"
TIMER_FILE="/etc/systemd/system/process_monitor.timer"
DROPIN_DIR="/etc/systemd/system/node_exporter.service.d"
DROPIN_FILE="$DROPIN_DIR/10-textfile.conf"
NODE_EXPORTER_BIN="/usr/local/bin/node_exporter"
COLLECT_INTERVAL=30

mkdir -p "$TEXTFILE_DIR"
chown -R "$NODE_USER":"$NODE_USER" "$TEXTFILE_DIR"
chmod 755 "$TEXTFILE_DIR"

if [ -x "$NODE_EXPORTER_BIN" ]; then
  mkdir -p "$DROPIN_DIR"
  cat > "$DROPIN_FILE" <<EOF
[Service]
ExecStart=
ExecStart=$NODE_EXPORTER_BIN --collector.textfile.directory=$TEXTFILE_DIR
EOF
  systemctl daemon-reload
  systemctl enable --now node_exporter
  systemctl restart node_exporter
else
  echo "⚠️ node_exporter not found at $NODE_EXPORTER_BIN"
fi

cat > "$PROCESS_SCRIPT" <<'EOF'
#!/bin/bash
METRIC_FILE="/var/lib/node_exporter/textfile_collector/process_metrics.prom"
TMPFILE="${METRIC_FILE}.tmp.$$"

ps -eo comm,pcpu,rss --no-headers | awk '{
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
chown "$NODE_USER":"$NODE_USER" "$METRIC_FILE" 2>/dev/null || true
chmod 644 "$METRIC_FILE"
EOF

chmod 755 "$PROCESS_SCRIPT"

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Collect process CPU/memory stats for Node Exporter
After=network-online.target
[Service]
Type=oneshot
ExecStart=$PROCESS_SCRIPT
User=root
Group=root
EOF

cat > "$TIMER_FILE" <<EOF
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

cat <<INFO
✅ Process Monitoring Setup Complete
- Metrics path: $TEXTFILE_DIR/process_metrics.prom
- Verify: curl -s http://localhost:9100/metrics | grep process_cpu_percent -m 5
- Import Grafana panels manually (see Step 6)
INFO
```

Run it:
```bash
sudo bash /tmp/setup-process-monitor.sh
```

---

## ✅ Summary
- Textfile collector enabled in Node Exporter.
- Systemd service + timer collect process stats every 30s.
- Grafana dashboard manually created.
- No Prometheus or Alertmanager modifications included.

---

## 📄 License
Free to use and modify for internal monitoring setups.
