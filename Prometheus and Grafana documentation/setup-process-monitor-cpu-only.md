# One-shot Setup Script: Process CPU Monitoring (Sampling-based)

This repository file contains a one-shot script that creates a sampling-based process CPU collector and integrates it with Node Exporter's textfile collector.

## How to use

1. Download the installer script `setup-process-monitor-cpu-only.sh`.
2. Inspect it before running.
3. Run as root:

```bash
sudo bash setup-process-monitor-cpu-only.sh
```

## Installer script (also saved as `setup-process-monitor-cpu-only.sh`)
```bash
#!/bin/bash
set -euo pipefail

# One-shot installer: process CPU usage monitoring (sampling) -> Node Exporter textfile collector
# This script will:
#  - create /var/lib/node_exporter/textfile_collector
#  - add a systemd drop-in for node_exporter to enable textfile collector
#  - create a sampling-based collector at /usr/local/bin/process_monitor.sh
#  - install systemd service + timer to run the collector periodically
#
# Inspect this file before running. Run as root: sudo bash /tmp/setup-process-monitor-cpu-only.sh

NODE_USER="marigold"
TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
PROCESS_SCRIPT="/usr/local/bin/process_monitor.sh"
SERVICE_FILE="/etc/systemd/system/process_monitor.service"
TIMER_FILE="/etc/systemd/system/process_monitor.timer"
DROPIN_DIR="/etc/systemd/system/node_exporter.service.d"
DROPIN_FILE="$DROPIN_DIR/10-textfile.conf"
NODE_EXPORTER_BIN="/usr/local/bin/node_exporter"
COLLECT_INTERVAL=30     # frequency the timer triggers the collector (seconds)
SAMPLE_INTERVAL=1       # seconds between /proc samples inside collector (matches top -d 1)

echo "== Process CPU monitor one-shot setup =="
echo "This script will create files and systemd units. Review variables at top if needed."

# 1) Create textfile collector directory
echo "- Creating textfile collector directory: $TEXTFILE_DIR"
mkdir -p "$TEXTFILE_DIR"
chown -R "${NODE_USER}:${NODE_USER}" "$TEXTFILE_DIR" 2>/dev/null || true
chmod 755 "$TEXTFILE_DIR"

# 2) Create systemd drop-in for node_exporter to enable textfile collector
if [ -x "$NODE_EXPORTER_BIN" ]; then
  echo "- Creating systemd drop-in for node_exporter to enable textfile collector"
  mkdir -p "$DROPIN_DIR"
  cat > "$DROPIN_FILE" <<EOF
[Service]
ExecStart=
ExecStart=$NODE_EXPORTER_BIN --collector.textfile.directory=$TEXTFILE_DIR
EOF
  systemctl daemon-reload || true
  systemctl enable --now node_exporter || true
  systemctl restart node_exporter || true
else
  echo "⚠️ Warning: node_exporter binary not found at $NODE_EXPORTER_BIN"
  echo "   Please install node_exporter or update NODE_EXPORTER_BIN and re-run."
fi

# 3) Write the sampling-based collector script (CPU only)
echo "- Writing collector script to $PROCESS_SCRIPT"
cat > "$PROCESS_SCRIPT" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
OUTFILE="$TEXTFILE_DIR/process_cpu_metrics.prom"
TMPOUT="${OUTFILE}.tmp.$$"
SAMPLE_INTERVAL=__SAMPLE_INTERVAL__
NODE_USER="__NODE_USER__"
NCPU=$(nproc 2>/dev/null || echo 1)

read_total_jiffies() {
  awk '/^cpu /{s=0; for(i=2;i<=NF;i++) s+=$i; print s; exit}' /proc/stat
}

snapshot_pids() {
  for pid_dir in /proc/[0-9]*; do
    pid=$(basename "$pid_dir")
    [ -r "$pid_dir/stat" ] || continue
    if [ -r "$pid_dir/comm" ]; then
      comm=$(tr -d '\n' < "$pid_dir/comm" 2>/dev/null || echo "")
    else
      comm=$(awk '{ match($0,/\([^)]*\)/); if (RSTART) print substr($0,RSTART+1,RLENGTH-2)}' "$pid_dir/stat" 2>/dev/null || echo "")
    fi
    cpu_jiffies=$(awk '{print $(14)+$(15)}' "$pid_dir/stat" 2>/dev/null || echo 0)
    [ -n "$comm" ] && printf "%s|%s|%s\n" "$pid" "$comm" "$cpu_jiffies"
  done
}

# sample 1
total1=$(read_total_jiffies)
snap1="/tmp/process_snap_1.$$"; snapshot_pids > "$snap1"

sleep "$SAMPLE_INTERVAL"

# sample 2
total2=$(read_total_jiffies)
snap2="/tmp/process_snap_2.$$"; snapshot_pids > "$snap2"

# aggregate deltas and write metrics
awk -v ncpu="$NCPU" -v tot1="$total1" -v tot2="$total2" -v s1="$snap1" -v s2="$snap2" '
BEGIN { FS="|"; }
{
}
END {
  while ((getline < s1) > 0) { pid=$1; comm=$2; cpu1[pid]=$3; comm_of[pid]=comm; } close(s1);
  while ((getline < s2) > 0) { pid=$1; comm=$2; cpu2=$3;
    if (cpu1[pid] != "") { delta = cpu2 - cpu1[pid]; if (delta < 0) delta = 0; } else { delta = 0; }
    cpu_delta[comm] += delta; proc_count[comm] += 1;
  } close(s2);
  total_delta = tot2 - tot1; if (total_delta <= 0) total_delta = 1;
  print "# HELP process_cpu_percent Total CPU percent aggregated per process name (sampled)";
  print "# TYPE process_cpu_percent gauge";
  for (p in cpu_delta) {
    cpu_pct = (cpu_delta[p] / total_delta) * 100.0 * ncpu;
    if (cpu_pct != cpu_pct) cpu_pct = 0;
    printf "process_cpu_percent{process=\"%s\"} %.3f\n", p, cpu_pct;
  }
  print "";
  print "# HELP process_count Number of processes per process name";
  print "# TYPE process_count gauge";
  for (p in proc_count) {
    printf "process_count{process=\"%s\"} %d\n", p, proc_count[p];
  }
}
' > "$TMPOUT"

mv "$TMPOUT" "$OUTFILE"
chown "$NODE_USER":"$NODE_USER" "$OUTFILE" 2>/dev/null || true
chmod 644 "$OUTFILE"
rm -f "$snap1" "$snap2" 2>/dev/null || true
EOF

# replace placeholders
sed -i "s|__SAMPLE_INTERVAL__|$SAMPLE_INTERVAL|g" "$PROCESS_SCRIPT"
sed -i "s|__NODE_USER__|$NODE_USER|g" "$PROCESS_SCRIPT"

chmod 755 "$PROCESS_SCRIPT"
chown root:root "$PROCESS_SCRIPT" 2>/dev/null || true

# 4) Create systemd service and timer
echo "- Creating systemd service and timer"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Collect process CPU percent (sampling) for Node Exporter
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
systemctl start process_monitor.service || true

echo "== Done =="
echo "Metrics file location: $TEXTFILE_DIR/process_cpu_metrics.prom"
echo "Run 'cat $TEXTFILE_DIR/process_cpu_metrics.prom' to view metrics"
echo "Timer: systemctl status process_monitor.timer"

exit 0

```

---

## What the installer does (summary)

- Creates `/var/lib/node_exporter/textfile_collector` and sets ownership to `marigold` (change inside script if needed).
- Adds a systemd drop-in for Node Exporter to enable textfile collector.
- Writes `/usr/local/bin/process_monitor.sh` which samples `/proc` twice and writes `process_cpu_percent` and `process_count`.
- Adds `process_monitor.service` and `process_monitor.timer` to run the collector every 30s (configurable).
- Starts the timer and runs the collector immediately once.

Inspect and modify variables at top of the script (`NODE_USER`, `NODE_EXPORTER_BIN`, `COLLECT_INTERVAL`, `SAMPLE_INTERVAL`) as needed.

