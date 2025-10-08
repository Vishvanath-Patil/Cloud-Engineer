
# Process CPU Monitoring Setup Guide (Sampling-Based via Node Exporter Textfile Collector)

This document provides a **complete manual setup guide** to monitor **per-process CPU usage only** (no memory)** on Red Hat servers using a **sampling-based collector** that integrates with **Node Exporter** and **Prometheus**.  
It includes detailed explanations, prerequisites, verification, troubleshooting, rollback, and a one-shot setup script for automation.

---

## 🧩 Overview

The setup creates a lightweight collector script that:
- Samples `/proc` twice (1 second apart) to calculate CPU% like the `top` command.
- Aggregates CPU usage per executable name (`comm`).
- Writes metrics to the Node Exporter textfile collector as Prometheus-compatible `.prom` files.

### **Exported Metrics**
| Metric | Description |
|--------|--------------|
| `process_cpu_percent` | Total CPU percent aggregated per process name |
| `process_count` | Number of processes per process name |

### **Key Design**
- CPU% calculation = `(Δ process_jiffies / Δ total_jiffies) × 100 × NCPU`
- Metrics are exposed via Node Exporter → scraped by Prometheus.

---

## ⚙️ Step 0 — Prerequisites & Verification

Run the following as **root** or with **sudo**.

```bash
# 1. Check node_exporter binary path
ls -l /usr/local/bin/node_exporter || which node_exporter

# 2. Ensure node_exporter service exists
systemctl status node_exporter --no-pager || echo "node_exporter service not found!"

# 3. Check if 'marigold' (Node Exporter user) exists
getent passwd marigold || echo "User marigold not found. Update user if needed."

# 4. Verify Node Exporter endpoint
curl -s http://localhost:9100/metrics | head -n 5

# 5. Confirm permission to create textfile directory
touch /var/lib/node_exporter/test && rm -f /var/lib/node_exporter/test
```

**Why these checks matter:**
- Ensures Node Exporter is installed and reachable.
- Verifies the target directory for textfile collector is writable.
- Confirms your environment matches the expected structure.

---

## 🏗️ Step 1 — Create Textfile Collector Directory

```bash
sudo mkdir -p /var/lib/node_exporter/textfile_collector
sudo chown -R marigold:marigold /var/lib/node_exporter/textfile_collector
sudo chmod 755 /var/lib/node_exporter/textfile_collector
ls -ld /var/lib/node_exporter/textfile_collector
```

**What this does:**  
Creates a directory where our custom script will write `.prom` files that Node Exporter exposes.

**Verification Command:**
```bash
stat -c '%U %G %a %n' /var/lib/node_exporter/textfile_collector
```

---

## ⚙️ Step 2 — Enable Textfile Collector for Node Exporter

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
```

**Why:**  
This creates a safe *systemd drop-in* to enable the textfile collector without overwriting the main unit file.

**Verify:**
```bash
ps aux | grep node_exporter | grep textfile
curl -s http://localhost:9100/metrics | head -n 10
```

---

## 🧮 Step 3 — Create the Process CPU Collector Script

```bash
sudo tee /usr/local/bin/process_monitor.sh > /dev/null <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
OUTFILE="$TEXTFILE_DIR/process_cpu_metrics.prom"
TMPOUT="${OUTFILE}.tmp.$$"
SAMPLE_INTERVAL=1
NODE_USER="marigold"
NCPU=$(nproc 2>/dev/null || echo 1)

read_total_jiffies() {
  awk '/^cpu /{s=0; for(i=2;i<=NF;i++) s+=$i; print s; exit}' /proc/stat
}

snapshot_pids() {
  for pid_dir in /proc/[0-9]*; do
    pid=$(basename "$pid_dir")
    [ -r "$pid_dir/stat" ] || continue
    comm=$(tr -d '\n' < "$pid_dir/comm" 2>/dev/null || awk '{ match($0,/\([^)]*\)/); if (RSTART) print substr($0,RSTART+1,RLENGTH-2)}' "$pid_dir/stat")
    cpu_jiffies=$(awk '{print $(14)+$(15)}' "$pid_dir/stat" 2>/dev/null || echo 0)
    [ -n "$comm" ] && printf "%s|%s|%s\n" "$pid" "$comm" "$cpu_jiffies"
  done
}

total1=$(read_total_jiffies)
snap1="/tmp/process_snap_1.$$"; snapshot_pids > "$snap1"
sleep "$SAMPLE_INTERVAL"
total2=$(read_total_jiffies)
snap2="/tmp/process_snap_2.$$"; snapshot_pids > "$snap2"

awk -v ncpu="$NCPU" -v tot1="$total1" -v tot2="$total2" -v s1="$snap1" -v s2="$snap2" '
BEGIN { FS="|"; }
END {
  while ((getline < s1) > 0) { pid=$1; comm=$2; cpu1[pid]=$3; comm_of[pid]=comm; } close(s1);
  while ((getline < s2) > 0) { pid=$1; comm=$2; cpu2=$3;
    if (cpu1[pid] != "") { delta = cpu2 - cpu1[pid]; if (delta < 0) delta = 0; } else { delta = 0; }
    cpu_delta[comm] += delta; proc_count[comm] += 1;
  } close(s2);
  total_delta = tot2 - tot1; if (total_delta <= 0) total_delta = 1;
  print "# HELP process_cpu_percent CPU percent per process (sampled)";
  print "# TYPE process_cpu_percent gauge";
  for (p in cpu_delta) {
    cpu_pct = (cpu_delta[p] / total_delta) * 100.0 * ncpu;
    printf "process_cpu_percent{process=\"%s\"} %.3f\n", p, cpu_pct;
  }
  print "# HELP process_count Number of processes per process name";
  print "# TYPE process_count gauge";
  for (p in proc_count) printf "process_count{process=\"%s\"} %d\n", p, proc_count[p];
}' > "$TMPOUT"

mv "$TMPOUT" "$OUTFILE"
chown "$NODE_USER":"$NODE_USER" "$OUTFILE" 2>/dev/null || true
chmod 644 "$OUTFILE"
rm -f "$snap1" "$snap2" 2>/dev/null || true
EOF

sudo chmod 755 /usr/local/bin/process_monitor.sh
sudo chown root:root /usr/local/bin/process_monitor.sh
```

**Verify script output manually:**
```bash
sudo /usr/local/bin/process_monitor.sh
cat /var/lib/node_exporter/textfile_collector/process_cpu_metrics.prom | head -n 10
```

Expected Output Example:
```
process_cpu_percent{process="java"} 12.345
process_count{process="java"} 2
```

---

## ⏲️ Step 4 — Create Systemd Service + Timer

```bash
sudo tee /etc/systemd/system/process_monitor.service > /dev/null <<'EOF'
[Unit]
Description=Collect process CPU percent for Node Exporter
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

**Verify:**
```bash
systemctl status process_monitor.timer --no-pager
journalctl -u process_monitor.service -n 20 --no-pager
```

---

## ✅ Step 5 — Validate Metrics

```bash
# Check file directly
cat /var/lib/node_exporter/textfile_collector/process_cpu_metrics.prom | head -n 20

# Check through Node Exporter
curl -s http://localhost:9100/metrics | grep process_cpu_percent -m 10
```

If you see values like:
```
process_cpu_percent{process="java"} 15.233
process_count{process="java"} 2
```
🎉 Setup is successful!

---

## 🔍 Step 6 — How It Works (Deep Dive)

1. **`/proc/stat`**: provides total system jiffies (cumulative CPU time).
2. **`/proc/<pid>/stat`**: provides per-process CPU time.
3. **Sampling**: the script samples both once, waits for 1 second, samples again.
4. **Delta Calculation**: computes `(Δ process_jiffies / Δ total_jiffies)`.
5. **Normalization**: multiplies by `100 * NCPU` so that 100% means one full CPU core.
6. **Aggregation**: sums by process executable (`comm`) to prevent metric explosion.
7. **Output**: metrics written to `.prom` file; Node Exporter reads and exposes them.

---

## 🧰 Step 7 — Troubleshooting

| Problem | Possible Cause | Fix |
|----------|----------------|-----|
| No `.prom` file created | Permission denied or syntax issue | Run `journalctl -u process_monitor.service -n 50` |
| node_exporter not exposing metrics | Textfile flag missing | Check `ps aux | grep node_exporter` |
| CPU values don’t match `top` | Sampling interval mismatch | Ensure `SAMPLE_INTERVAL=1` |
| High load | Too frequent runs | Increase timer interval to 60s |
| SELinux denies writes | Access restricted | Set correct SELinux context or disable enforcing temporarily |

---

## ♻️ Step 8 — Rollback / Cleanup

```bash
sudo systemctl disable --now process_monitor.timer
sudo rm -f /etc/systemd/system/process_monitor.timer /etc/systemd/system/process_monitor.service
sudo systemctl daemon-reload

sudo rm -f /usr/local/bin/process_monitor.sh /var/lib/node_exporter/textfile_collector/process_cpu_metrics.prom

sudo rm -f /etc/systemd/system/node_exporter.service.d/10-textfile.conf
sudo systemctl daemon-reload
sudo systemctl restart node_exporter
```

---

## 🚀 Step 9 — One-Shot Setup Script (Full Automation)

Save and run this script:
```bash
sudo bash /tmp/setup-process-monitor-cpu-only.sh
```

👉 It performs all steps automatically (directory, drop-in, collector, service, and timer).

---

## 🧠 Notes

- Designed for **Red Hat / CentOS / Amazon Linux**.
- Prometheus already scraping Node Exporter automatically collects these metrics.
- Use in Grafana: `topk(10, process_cpu_percent)` to visualize top CPU consumers.

**Maintainer:** DevOps / CloudOps Team  
**Version:** v1.0  
**Purpose:** Sampling-based process CPU monitoring only (no memory)
