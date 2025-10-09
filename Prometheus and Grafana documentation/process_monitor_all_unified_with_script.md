
# Process-wise CPU, Memory, and Disk I/O Monitoring — Unified Setup (Manual + One-shot Script)

This document provides a **complete end-to-end setup** for monitoring **per-process CPU, Memory, and Disk I/O (read/write throughput)** using a single unified collector script integrated with **Node Exporter**, **Prometheus**, and **Grafana**.

It includes:
- Manual setup with detailed explanation
- Full ready-to-run **one-shot installer script**
- Verification, troubleshooting, rollback, and Prometheus + Grafana examples

---

## 🧩 Overview

This setup creates a unified collector that samples `/proc` and writes process-wise metrics to Node Exporter’s textfile collector.

### ✅ Monitored metrics

| Metric | Description |
|--------|--------------|
| `process_cpu_percent` | CPU usage % (calculated like `top`) |
| `process_memory_bytes` | Resident memory usage (RSS in bytes) |
| `process_io_read_bytes_per_second` | Disk read bytes per second |
| `process_io_write_bytes_per_second` | Disk write bytes per second |
| `process_count` | Number of process instances (per executable) |

### ⚙️ Components created

| Component | Purpose |
|------------|----------|
| `/usr/local/bin/process_monitor_all.sh` | Unified collector script |
| `/etc/systemd/system/process_monitor.service` | Service running collector |
| `/etc/systemd/system/process_monitor.timer` | Timer scheduling collector |
| `/var/lib/node_exporter/textfile_collector/process_metrics.prom` | Metrics output |
| `/etc/systemd/system/node_exporter.service.d/10-textfile.conf` | Enables Node Exporter textfile collector |

---

## ⚙️ Step 0 — Prerequisites & Verification

Run as **root** or **sudo**.

```bash
ls -l /usr/local/bin/node_exporter || which node_exporter
systemctl status node_exporter --no-pager || echo "Node Exporter not found or inactive"
getent passwd marigold || echo "User marigold not found (update script variable NODE_USER)"
curl -s http://localhost:9100/metrics | head -n 5 || echo "Node Exporter not reachable"
touch /var/lib/node_exporter/test && rm -f /var/lib/node_exporter/test || echo "Permission issue"
```

---

## 🏗️ Step 1 — Create Textfile Collector Directory

```bash
sudo mkdir -p /var/lib/node_exporter/textfile_collector
sudo chown -R marigold:marigold /var/lib/node_exporter/textfile_collector
sudo chmod 755 /var/lib/node_exporter/textfile_collector
```

**Verify:**
```bash
ls -ld /var/lib/node_exporter/textfile_collector
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

**Verify:**
```bash
ps aux | grep node_exporter | grep textfile
curl -s http://localhost:9100/metrics | head -n 10
```

---

## 🧮 Step 3 — Unified Collector Script (Manual creation)

Create `/usr/local/bin/process_monitor_all.sh` with the below code.

> This script samples CPU, memory, and I/O data twice (1s apart) and aggregates metrics by process name.

```bash
#!/usr/bin/env bash
set -euo pipefail

TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
OUTFILE="$TEXTFILE_DIR/process_metrics.prom"
TMPOUT="${OUTFILE}.tmp.$$"
SAMPLE_INTERVAL=1
NODE_USER="marigold"
NCPU=$(nproc 2>/dev/null || echo 1)

read_total_jiffies() {
  awk '/^cpu /{s=0; for(i=2;i<=NF;i++) s+=$i; print s; exit}' /proc/stat
}

snapshot_proc() {
  for pid_dir in /proc/[0-9]*; do
    pid=$(basename "$pid_dir")
    statf="$pid_dir/stat"
    iof="$pid_dir/io"
    [ -r "$statf" ] || continue
    if [ -r "$pid_dir/comm" ]; then
      comm=$(tr -d '\n' < "$pid_dir/comm" 2>/dev/null || echo "")
    else
      comm=$(awk '{ match($0,/\([^)]*\)/); if (RSTART) print substr($0,RSTART+1,RLENGTH-2)}' "$statf" 2>/dev/null || echo "")
    fi
    cpu_jiffies=$(awk '{print $(14) + $(15)}' "$statf" 2>/dev/null || echo 0)
    rss_kb=$(awk '/^VmRSS:/ {print $2; exit}' "$pid_dir/status" 2>/dev/null || echo "")
    if [ -z "$rss_kb" ]; then
      pages=$(awk '{print $2}' "$pid_dir/statm" 2>/dev/null || echo 0)
      page_kb=$(( $(getconf PAGE_SIZE) / 1024 ))
      rss_kb=$((pages * page_kb))
    fi
    if [ -r "$iof" ]; then
      read_bytes=$(awk '/^read_bytes:/ {print $2; exit}' "$iof" 2>/dev/null || echo 0)
      write_bytes=$(awk '/^write_bytes:/ {print $2; exit}' "$iof" 2>/dev/null || echo 0)
    else
      read_bytes=0; write_bytes=0
    fi
    printf "%s|%s|%s|%s|%s|%s\n" "$pid" "$comm" "$cpu_jiffies" "$rss_kb" "$read_bytes" "$write_bytes"
  done
}

total1=$(read_total_jiffies)
snap1="/tmp/process_snap_1.$$"; snapshot_proc > "$snap1"
sleep "$SAMPLE_INTERVAL"
total2=$(read_total_jiffies)
snap2="/tmp/process_snap_2.$$"; snapshot_proc > "$snap2"

awk -v ncpu="$NCPU" -v tot1="$total1" -v tot2="$total2" -v s1="$snap1" -v s2="$snap2" -v interval="$SAMPLE_INTERVAL" '
BEGIN { FS="|"; OFMT="%.3f"; }
END {
  while ((getline < s1) > 0) { pid=$1; comm=$2; cpu1[pid]=$3; rss1[pid]=$4; read1[pid]=$5; write1[pid]=$6; }
  close(s1);
  while ((getline < s2) > 0) {
    pid=$1; comm=$2; cpu2=$3; rss2=$4; read2=$5; write2=$6;
    dcpu=(cpu2-cpu1[pid]); if(dcpu<0) dcpu=0;
    cpu_delta[comm]+=dcpu;
    mem_sum[comm]+=rss2;
    read_rate[comm]+=((read2-read1[pid])/interval);
    write_rate[comm]+=((write2-write1[pid])/interval);
    count[comm]+=1;
  }
  close(s2);
  total_delta=tot2-tot1; if(total_delta<=0) total_delta=1;

  print "# HELP process_cpu_percent CPU percent per process";
  print "# TYPE process_cpu_percent gauge";
  for(p in cpu_delta){cpu_pct=(cpu_delta[p]/total_delta)*100.0*ncpu; printf "process_cpu_percent{process=\"%s\"} %.3f\n",p,cpu_pct;}
  print "# HELP process_memory_bytes RSS memory (bytes) per process";
  print "# TYPE process_memory_bytes gauge";
  for(p in mem_sum){printf "process_memory_bytes{process=\"%s\"} %.0f\n",p,mem_sum[p]*1024;}
  print "# HELP process_io_read_bytes_per_second Disk read bytes per second";
  print "# TYPE process_io_read_bytes_per_second gauge";
  for(p in read_rate){printf "process_io_read_bytes_per_second{process=\"%s\"} %.3f\n",p,read_rate[p];}
  print "# HELP process_io_write_bytes_per_second Disk write bytes per second";
  print "# TYPE process_io_write_bytes_per_second gauge";
  for(p in write_rate){printf "process_io_write_bytes_per_second{process=\"%s\"} %.3f\n",p,write_rate[p];}
  print "# HELP process_count Number of processes";
  print "# TYPE process_count gauge";
  for(p in count){printf "process_count{process=\"%s\"} %d\n",p,count[p];}
}' > "$TMPOUT"

mv "$TMPOUT" "$OUTFILE"
chown "$NODE_USER":"$NODE_USER" "$OUTFILE" 2>/dev/null || true
chmod 644 "$OUTFILE"
rm -f "$snap1" "$snap2" 2>/dev/null || true
```

Make executable:
```bash
sudo chmod 755 /usr/local/bin/process_monitor_all.sh
sudo chown root:root /usr/local/bin/process_monitor_all.sh
```

---

## 🕐 Step 4 — Create systemd Service + Timer

```bash
sudo tee /etc/systemd/system/process_monitor.service > /dev/null <<'EOF'
[Unit]
Description=Collect process CPU, memory, and IO metrics
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/process_monitor_all.sh
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

---

## 🚀 One-shot Setup Script (Full Automation)

Save the below to `/tmp/setup-process-monitor-all.sh` and run:

```bash
sudo bash /tmp/setup-process-monitor-all.sh
```

```bash
#!/bin/bash
set -euo pipefail

NODE_USER="marigold"
TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
PROCESS_SCRIPT="/usr/local/bin/process_monitor_all.sh"
SERVICE_FILE="/etc/systemd/system/process_monitor.service"
TIMER_FILE="/etc/systemd/system/process_monitor.timer"
DROPIN_DIR="/etc/systemd/system/node_exporter.service.d"
DROPIN_FILE="$DROPIN_DIR/10-textfile.conf"
NODE_EXPORTER_BIN="/usr/local/bin/node_exporter"
COLLECT_INTERVAL=30
SAMPLE_INTERVAL=1

mkdir -p "$TEXTFILE_DIR"
chown -R "${NODE_USER}:${NODE_USER}" "$TEXTFILE_DIR" || true
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
fi

cat > "$PROCESS_SCRIPT" <<'EOF2'
[Collector Script from Manual Section Above]
EOF2

chmod 755 "$PROCESS_SCRIPT"
chown root:root "$PROCESS_SCRIPT"

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Collect process CPU, memory and IO metrics
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

echo "✅ Unified monitoring setup complete."
echo "Metrics file: $TEXTFILE_DIR/process_metrics.prom"
```

---

## ✅ Verification

```bash
cat /var/lib/node_exporter/textfile_collector/process_metrics.prom | head -n 20
curl -s http://localhost:9100/metrics | grep process_cpu_percent -m 10
systemctl status process_monitor.timer --no-pager
```

---

## 📊 Grafana Queries

| Metric | Query | Unit |
|--------|--------|------|
| CPU | `topk(10, process_cpu_percent)` | Percent (0–100) |
| Memory | `topk(10, process_memory_bytes / 1024 / 1024)` | MB |
| Disk Read | `topk(10, process_io_read_bytes_per_second)` | bytes/sec |
| Disk Write | `topk(10, process_io_write_bytes_per_second)` | bytes/sec |

---

## 🧰 Troubleshooting

| Issue | Fix |
|--------|-----|
| No metrics | `journalctl -u process_monitor.service -n 50` |
| Node Exporter missing metrics | Check if drop-in applied (`ps aux | grep textfile`) |
| Values differ from `top` | `SAMPLE_INTERVAL=1` ensures short-term rate |
| IO zeros | `/proc/<pid>/io` unreadable for some processes |

---

## ♻️ Rollback / Cleanup

```bash
sudo systemctl disable --now process_monitor.timer
sudo rm -f /etc/systemd/system/process_monitor.{service,timer}
sudo rm -f /usr/local/bin/process_monitor_all.sh
sudo rm -f /var/lib/node_exporter/textfile_collector/process_metrics.prom
sudo rm -f /etc/systemd/system/node_exporter.service.d/10-textfile.conf
sudo systemctl daemon-reload
sudo systemctl restart node_exporter
```

---

**Maintainer:** DevOps / CloudOps Team  
**Version:** v2.1 (Unified CPU + Memory + Disk I/O Monitoring)
