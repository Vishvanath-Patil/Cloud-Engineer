# 🛰️ Partner Endpoint Connectivity Monitoring — No TMP File Version (Node Exporter Textfile Collector)

This document provides a **complete, ready-to-upload setup** for monitoring partner endpoint connectivity using **Node Exporter’s Textfile Collector**, **Prometheus**, and **Grafana**.

This version writes metrics **directly** to the `.prom` file (no temporary files) and reports **only**:
- `partner_connectivity_up` — `1` if connected, `0` if timeout
- `partner_connectivity_last_check_timestamp_seconds` — unix epoch timestamp of the last check

---

## ⚙️ Overview

Each partner endpoint (IP or hostname with port) is checked via:
```bash
curl -v telnet://<host>:<port>
```
Results are written to:
```
/var/lib/node_exporter/textfile_collector/partner_connectivity.prom
```

These metrics are scraped by Prometheus through Node Exporter and visualized in Grafana.

---

## 🧭 Architecture

```
partners.conf
   ↓
partner_connectivity_check.sh
   ↓
/var/lib/node_exporter/textfile_collector/partner_connectivity.prom
   ↓
Node Exporter (Textfile Collector)
   ↓
Prometheus
   ↓
Grafana Dashboard
```

---

## 🪜 Step-by-Step Setup Guide

### 1️⃣ Prerequisites

- Node Exporter is installed and running as user `node_exporter`.
- Prometheus scrapes Node Exporter metrics.
- `curl` installed with telnet support.
- Root (sudo) access.

---

### 2️⃣ Verify Node Exporter User

```bash
ps -ef | grep '[n]ode_exporter'
systemctl show -p ExecStart --value node_exporter || true
```

If the service runs as a different user, modify the script variable `NODE_EXPORTER_USER` accordingly.

---

### 3️⃣ Create Required Directories and Files

#### Create Textfile Collector Directory

```bash
sudo mkdir -p /var/lib/node_exporter/textfile_collector
sudo chown node_exporter:node_exporter /var/lib/node_exporter/textfile_collector
sudo chmod 755 /var/lib/node_exporter/textfile_collector
```

#### Create Partner Configuration File

```bash
sudo mkdir -p /etc/partner_monitor
sudo tee /etc/partner_monitor/partners.conf > /dev/null <<'EOF'
# partner_name host_or_ip port
partnerA 10.0.0.10 443
partnerB partner.example.com 443
EOF
sudo chown root:node_exporter /etc/partner_monitor/partners.conf
sudo chmod 640 /etc/partner_monitor/partners.conf
```

#### Create Log File

```bash
sudo touch /var/log/partner_connectivity.log
sudo chown node_exporter:node_exporter /var/log/partner_connectivity.log
sudo chmod 640 /var/log/partner_connectivity.log
```

---

### 4️⃣ Enable Node Exporter Textfile Collector (if missing)

```bash
sudo mkdir -p /etc/systemd/system/node_exporter.service.d
sudo tee /etc/systemd/system/node_exporter.service.d/textfile.conf > /dev/null <<'EOF'
[Service]
ExecStart=
ExecStart=/usr/local/bin/node_exporter --web.listen-address=:9100 --collector.textfile.directory=/var/lib/node_exporter/textfile_collector
EOF
sudo systemctl daemon-reload
sudo systemctl restart node_exporter
```

Verify:
```bash
curl -s http://localhost:9100/metrics | grep textfile
```

---

### 5️⃣ Create the Partner Connectivity Checker Script

Save this as `/usr/local/bin/partner_connectivity_check.sh`:

```bash
#!/usr/bin/env bash
# partner_connectivity_check.sh
# Checks connectivity for partners listed in /etc/partner_monitor/partners.conf
# Writes metrics directly to /var/lib/node_exporter/textfile_collector/partner_connectivity.prom
set -euo pipefail
IFS=$'\n'

NODE_EXPORTER_USER="node_exporter"
PARTNER_CONF="/etc/partner_monitor/partners.conf"
TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
OUT_FILE="${TEXTFILE_DIR}/partner_connectivity.prom"
LOG_FILE="/var/log/partner_connectivity.log"
CURL_CONNECT_TIMEOUT=10
CURL_MAX_TIME=20

timestamp() { date '+%Y-%m-%d %H:%M:%S %z'; }

# Write header directly to metrics file
{
  echo "# HELP partner_connectivity_up Partner TCP connect success (1=connected,0=timeout)"
  echo "# TYPE partner_connectivity_up gauge"
  echo "# HELP partner_connectivity_last_check_timestamp_seconds Unix epoch seconds of last check"
  echo "# TYPE partner_connectivity_last_check_timestamp_seconds gauge"
} > "${OUT_FILE}"

now_ts=$(date +%s)

while read -r line || [[ -n "${line}" ]]; do
  [[ -z "${line// }" ]] && continue
  [[ "${line}" =~ ^# ]] && continue

  partner=$(echo "${line}" | awk '{print $1}')
  host=$(echo "${line}" | awk '{print $2}')
  port=$(echo "${line}" | awk '{print $3}')
  [[ -z "${partner}" || -z "${host}" || -z "${port}" ]] && continue

  up=0
  rc=0
  curl -sS --connect-timeout ${CURL_CONNECT_TIMEOUT} -m ${CURL_MAX_TIME} -o /dev/null "telnet://${host}:${port}" 2>/dev/null || rc=$?
  rc=${rc:-0}

  if [[ "${rc}" -eq 0 ]]; then
    up=1
    echo "$(timestamp) INFO: ${partner} ${host}:${port} CONNECTED" >> "${LOG_FILE}" 2>/dev/null || true
  else
    up=0
    echo "$(timestamp) WARN: ${partner} ${host}:${port} CONNECTION_TIMEOUT rc=${rc}" >> "${LOG_FILE}" 2>/dev/null || true
  fi

  printf 'partner_connectivity_up{partner="%s",host="%s",port="%s"} %s\n' "${partner}" "${host}" "${port}" "${up}" >> "${OUT_FILE}"
  printf 'partner_connectivity_last_check_timestamp_seconds{partner="%s",host="%s",port="%s"} %s\n' "${partner}" "${host}" "${port}" "${now_ts}" >> "${OUT_FILE}"

done < "${PARTNER_CONF}"

chown ${NODE_EXPORTER_USER}:${NODE_EXPORTER_USER} "${OUT_FILE}" 2>/dev/null || true
chmod 644 "${OUT_FILE}" 2>/dev/null || true
```

Make executable:
```bash
sudo chmod 750 /usr/local/bin/partner_connectivity_check.sh
sudo chown root:root /usr/local/bin/partner_connectivity_check.sh
```

---

### 6️⃣ Test the Script

Run manually as Node Exporter user:
```bash
sudo -u node_exporter /usr/local/bin/partner_connectivity_check.sh
cat /var/lib/node_exporter/textfile_collector/partner_connectivity.prom
```

Sample output:
```
partner_connectivity_up{partner="partnerA",host="10.0.0.10",port="443"} 1
partner_connectivity_last_check_timestamp_seconds{partner="partnerA",host="10.0.0.10",port="443"} 1733920000
```

---

### 7️⃣ Scheduling Options

You can schedule the script via **cron** or **systemd timer**.

#### 🕒 Option 1 — Cron Job (every 3 minutes)

```bash
sudo tee /etc/cron.d/partner_connectivity >/dev/null <<'EOF'
*/3 * * * * node_exporter /usr/local/bin/partner_connectivity_check.sh >> /var/log/partner_connectivity.log 2>&1
EOF
sudo chmod 644 /etc/cron.d/partner_connectivity
```

#### ⚙️ Option 2 — Systemd Service + Timer

Create service file:
```bash
sudo tee /etc/systemd/system/partner_connectivity.service > /dev/null <<'EOF'
[Unit]
Description=Partner Endpoint Connectivity Check

[Service]
Type=oneshot
User=node_exporter
ExecStart=/usr/local/bin/partner_connectivity_check.sh
EOF
```

Create timer file:
```bash
sudo tee /etc/systemd/system/partner_connectivity.timer > /dev/null <<'EOF'
[Unit]
Description=Run partner connectivity check every 3 minutes

[Timer]
OnCalendar=*:0/3
Persistent=true

[Install]
WantedBy=timers.target
EOF
```

Enable and start timer:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now partner_connectivity.timer
systemctl list-timers | grep partner_connectivity
```

---

### 8️⃣ Verification

Check metrics exposure:
```bash
curl -s http://localhost:9100/metrics | grep partner_connectivity
```

Check logs:
```bash
sudo tail -n 20 /var/log/partner_connectivity.log
```

---

### 9️⃣ Grafana Setup

#### Status Panel (Table or Stat)
Query:
```promql
partner_connectivity_up
```
Value mappings:
| Value | Display | Color |
|--------|----------|--------|
| 1 | ✅ Connected | Green |
| 0 | ❌ Timeout | Red |

#### Last Check Age
```promql
time() - partner_connectivity_last_check_timestamp_seconds
```
Threshold > 240s (3-minute schedule + buffer).

---

### 🔧 Troubleshooting

| Issue | Fix |
|--------|------|
| Metrics missing | Ensure Node Exporter started with `--collector.textfile.directory` |
| File unreadable | `chown node_exporter:node_exporter /var/lib/node_exporter/textfile_collector/*.prom` |
| Cron not running | Check `/var/log/cron` or `systemctl status crond` |
| SELinux denial | Check `audit.log` or run `setenforce 0` for testing |

---

### 🔄 Rollback / Uninstall

```bash
sudo rm -f /usr/local/bin/partner_connectivity_check.sh
sudo rm -f /etc/partner_monitor/partners.conf
sudo rm -f /etc/cron.d/partner_connectivity
sudo rm -f /etc/systemd/system/partner_connectivity.service
sudo rm -f /etc/systemd/system/partner_connectivity.timer
sudo rm -f /var/log/partner_connectivity.log
sudo rm -f /var/lib/node_exporter/textfile_collector/partner_connectivity.prom
sudo systemctl daemon-reload
sudo systemctl restart node_exporter
```

---

### 🪪 License

MIT License — free to use, modify, and share.

---

✅ **End of File — Ready to Upload to GitHub**
