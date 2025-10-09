
# Process-wise CPU, Memory, and Disk I/O Monitoring (Unified Setup)

This document provides a **complete end-to-end guide** to monitor **CPU**, **Memory**, and **Disk I/O** usage per process using a single unified collector script integrated with **Node Exporter**, **Prometheus**, and **Grafana**.  

It includes:  
- Manual step-by-step setup  
- One-shot installer script  
- Verification & troubleshooting  
- Rollback procedure  
- Grafana queries & units

---

## 🧩 Overview

### Features
- Monitors per-process **CPU%**, **RSS Memory**, **Disk Read/Write throughput (bytes/sec)**.
- Aggregates metrics by process executable (`comm`) to reduce cardinality.
- Outputs Prometheus-compatible `.prom` file to Node Exporter’s textfile collector.
- Single systemd service + timer manage the script.

### Exported Metrics

| Metric | Description |
|--------|--------------|
| `process_cpu_percent` | CPU usage % (sampled like `top`) |
| `process_memory_bytes` | Resident memory (bytes) |
| `process_io_read_bytes_per_second` | Disk read bytes/sec |
| `process_io_write_bytes_per_second` | Disk write bytes/sec |
| `process_count` | Number of process instances |

---

## ⚙️ Step 0 — Prerequisites

Run as **root** or **sudo**.

```bash
ls -l /usr/local/bin/node_exporter || which node_exporter
systemctl status node_exporter --no-pager || echo "node_exporter not running"
getent passwd marigold || echo "User marigold not found (update script variable NODE_USER)"
curl -s http://localhost:9100/metrics | head -n 3 || echo "Node exporter not reachable"
touch /var/lib/node_exporter/test && rm -f /var/lib/node_exporter/test || echo "Permission issue"
```

---

## 🏗️ Step 1 — Create Textfile Collector Directory

```bash
sudo mkdir -p /var/lib/node_exporter/textfile_collector
sudo chown -R marigold:marigold /var/lib/node_exporter/textfile_collector
sudo chmod 755 /var/lib/node_exporter/textfile_collector
```

---

## ⚙️ Step 2 — Enable Textfile Collector (Node Exporter)

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

Verify:
```bash
ps aux | grep node_exporter | grep textfile
curl -s http://localhost:9100/metrics | head -n 5
```

---

## 🧮 Step 3 — Unified Collector Script

Create `/usr/local/bin/process_monitor_all.sh`:

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
      rchar=$(awk '/^rchar:/ {print $2; exit}' "$iof" 2>/dev/null || echo 0)
      wchar=$(awk '/^wchar:/ {print $2; exit}' "$iof" 2>/dev/null || echo 0)
      read_bytes=$(awk '/^read_bytes:/ {print $2; exit}' "$iof" 2>/dev/null || echo 0)
      write_bytes=$(awk '/^write_bytes:/ {print $2; exit}' "$iof" 2>/dev/null || echo 0)
    else
      rchar=0; wchar=0; read_bytes=0; write_bytes=0
    fi
    printf "%s|%s|%s|%s|%s|%s|%s|%s\n" "$pid" "$comm" "$cpu_jiffies" "$rss_kb" "$rchar" "$wchar" "$read_bytes" "$write_bytes"
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
  while ((getline < s1) > 0) { pid=$1; comm=$2; cpu1[pid]=$3; rss1[pid]=$4; rchar1[pid]=$5; wchar1[pid]=$6; read1[pid]=$7; write1[pid]=$8; }
  close(s1);
  while ((getline < s2) > 0) {
    pid=$1; comm=$2; cpu2=$3; rss2=$4; rchar2=$5; wchar2=$6; read2=$7; write2=$8;
    if (cpu1[pid] != "") { dcpu = cpu2 - cpu1[pid]; if (dcpu < 0) dcpu = 0; } else { dcpu = 0; }
    cpu_delta[comm] += dcpu;
    mem_sum[comm] += rss2;
    r_delta=(rchar2 - (rchar1[pid]+0)); if (r_delta < 0) r_delta=0;
    w_delta=(wchar2 - (wchar1[pid]+0)); if (w_delta < 0) w_delta=0;
    read_delta=(read2 - (read1[pid]+0)); if (read_delta < 0) read_delta=0;
    write_delta=(write2 - (write1[pid]+0)); if (write_delta < 0) write_delta=0;
    r_rate[comm]+=r_delta/interval; w_rate[comm]+=w_delta/interval;
    read_rate[comm]+=read_delta/interval; write_rate[comm]+=write_delta/interval;
    count[comm]+=1;
  }
  close(s2);
  total_delta=tot2-tot1; if(total_delta<=0) total_delta=1;

  print "# HELP process_cpu_percent Total CPU percent aggregated per process name";
  print "# TYPE process_cpu_percent gauge";
  for(p in cpu_delta){cpu_pct=(cpu_delta[p]/total_delta)*100.0*ncpu; printf "process_cpu_percent{process=\"%s\"} %.3f\n",p,cpu_pct;}
  print "# HELP process_memory_bytes Total RSS memory (bytes) per process name";
  print "# TYPE process_memory_bytes gauge";
  for(p in mem_sum){printf "process_memory_bytes{process=\"%s\"} %.0f\n",p,mem_sum[p]*1024;}
  print "# HELP process_io_read_bytes_per_second read_bytes per second (actual disk reads)";
  print "# TYPE process_io_read_bytes_per_second gauge";
  for(p in read_rate){printf "process_io_read_bytes_per_second{process=\"%s\"} %.3f\n",p,read_rate[p];}
  print "# HELP process_io_write_bytes_per_second write_bytes per second (actual disk writes)";
  print "# TYPE process_io_write_bytes_per_second gauge";
  for(p in write_rate){printf "process_io_write_bytes_per_second{process=\"%s\"} %.3f\n",p,write_rate[p];}
  print "# HELP process_count Number of processes per process name";
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

## 🕐 Step 4 — Create Systemd Service + Timer

Create `/etc/systemd/system/process_monitor.service`:
```ini
[Unit]
Description=Collect process CPU, memory and IO metrics for Node Exporter
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/process_monitor_all.sh
User=root
Group=root
```

Create `/etc/systemd/system/process_monitor.timer`:
```ini
[Unit]
Description=Run process_monitor every 30s

[Timer]
OnBootSec=30s
OnUnitActiveSec=30s
Unit=process_monitor.service

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now process_monitor.timer
sudo systemctl start process_monitor.service
```

---

## ✅ Step 5 — Verify Metrics

```bash
cat /var/lib/node_exporter/textfile_collector/process_metrics.prom | head -n 20
curl -s http://localhost:9100/metrics | grep process_cpu_percent -m 10
```

Expected Output Example:
```
process_cpu_percent{process="java"} 15.20
process_memory_bytes{process="java"} 5238784
process_io_read_bytes_per_second{process="java"} 512.00
process_io_write_bytes_per_second{process="java"} 1024.00
process_count{process="java"} 2
```

---

## 🚀 One-Shot Setup Script

Save this to `/tmp/setup-process-monitor-all.sh` and run:

```bash
sudo bash /tmp/setup-process-monitor-all.sh
```

👉 It performs all steps automatically.

[The full one-shot script is embedded in the code section above in your setup history.]

---

## 📊 Grafana Queries

| Panel | Query | Unit |
|--------|--------|--------|
| Top CPU | `topk(10, process_cpu_percent)` | Percent (0–100) |
| Top Memory | `topk(10, process_memory_bytes / 1024 / 1024)` | MB |
| Top Disk Read | `topk(10, process_io_read_bytes_per_second)` | bytes/sec |
| Top Disk Write | `topk(10, process_io_write_bytes_per_second)` | bytes/sec |

---

## 🧰 Troubleshooting

| Problem | Command / Fix |
|----------|----------------|
| `.prom` file missing | `journalctl -u process_monitor.service -n 50` |
| Node Exporter missing textfile | `ps aux | grep node_exporter | grep textfile` |
| CPU mismatch vs `top` | Ensure `SAMPLE_INTERVAL=1` |
| IO zeros | Some `/proc/<pid>/io` files not readable |
| High load | Increase `COLLECT_INTERVAL` to 60s |

---

## ♻️ Rollback / Cleanup

```bash
sudo systemctl disable --now process_monitor.timer
sudo rm -f /etc/systemd/system/process_monitor.timer /etc/systemd/system/process_monitor.service
sudo systemctl daemon-reload

sudo rm -f /usr/local/bin/process_monitor_all.sh
sudo rm -f /var/lib/node_exporter/textfile_collector/process_metrics.prom

sudo rm -f /etc/systemd/system/node_exporter.service.d/10-textfile.conf
sudo systemctl daemon-reload
sudo systemctl restart node_exporter
```

---

**Maintainer:** DevOps / CloudOps Team  
**Version:** v2.0 (Unified CPU, Memory, Disk I/O Collector)  
**Compatibility:** RHEL 8+, CentOS 8+, Amazon Linux 2+

