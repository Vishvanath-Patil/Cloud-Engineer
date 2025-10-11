# 🛰️ Partner Endpoint Connectivity Monitoring — Complete Setup Guide (Node Exporter Textfile Collector)

This document provides a **complete, end-to-end setup** for monitoring multiple partner endpoints' connectivity using **Node Exporter’s Textfile Collector**, **Prometheus**, and **Grafana**.

The setup continuously checks TCP connectivity using:
```bash
curl -v telnet://<host>:<port>
```
and exports Prometheus metrics:
- `partner_connectivity_up`
- `partner_connectivity_connect_time_seconds`
- `partner_connectivity_last_check_timestamp_seconds`

This guide is fully self-contained — no cross-references required.

---

## ⚙️ Prerequisites

Before beginning, ensure:
1. Node Exporter is installed and running.
2. Node Exporter runs as `node_exporter` user.
3. `curl` (with `telnet://` support) is installed.
4. Prometheus is scraping Node Exporter metrics.
5. You have root (sudo) access to create directories and systemd overrides.

---

## 🧭 Architecture Overview

```
Partner endpoints (IP/DNS:Port)
        ↓
curl telnet://host:port
        ↓
Script → Prometheus metrics file (.prom)
        ↓
Node Exporter (textfile collector)
        ↓
Prometheus scrapes metrics
        ↓
Grafana dashboard visualization
```

---

## 🪜 Step-by-Step Setup

### Step 1 — Verify Node Exporter User

Run:
```bash
ps -ef | grep '[n]ode_exporter'
systemctl show -p ExecStart --value node_exporter || true
```
> Confirm Node Exporter runs as user `node_exporter`.  
> If it runs as a different user, update the `NODE_EXPORTER_USER` variable later.

---

### Step 2 — Create Textfile Collector Directory

```bash
sudo mkdir -p /var/lib/node_exporter/textfile_collector
sudo chown node_exporter:node_exporter /var/lib/node_exporter/textfile_collector
sudo chmod 755 /var/lib/node_exporter/textfile_collector
```

**Why:**  
Node Exporter reads `.prom` metric files from this directory when started with the flag:
```
--collector.textfile.directory=/var/lib/node_exporter/textfile_collector
```

---

### Step 3 — Enable Node Exporter Textfile Collector (if not already)

**Check existing startup flags:**
```bash
ps -ef | grep '[n]ode_exporter' -o
systemctl show -p ExecStart --value node_exporter || true
```
If you **don’t see** `--collector.textfile.directory` in output, enable it:

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
**Verification:**
```bash
curl -s http://localhost:9100/metrics | grep node_textfile
```

---

### Step 4 — Create Partner Configuration File

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

**Explanation:**  
This file lists all partners to be checked. You can add/remove endpoints anytime.

---

### Step 5 — Create Log File

```bash
sudo touch /var/log/partner_connectivity.log
sudo chown node_exporter:node_exporter /var/log/partner_connectivity.log
sudo chmod 640 /var/log/partner_connectivity.log
```

**Why:**  
The script logs each run’s results, errors, and connection times.

---

### Step 6 — Deploy One-Shot Installer Script

Save the following content as `/usr/local/bin/install_partner_connectivity.sh`:

```bash
#!/usr/bin/env bash
# install_partner_connectivity.sh — One-shot full installer for Partner Endpoint Connectivity Monitoring

set -euo pipefail

NODE_EXPORTER_USER="node_exporter"
TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
PARTNER_CONF_DIR="/etc/partner_monitor"
PARTNER_CONF="${PARTNER_CONF_DIR}/partners.conf"
CHECKER_SCRIPT="/usr/local/bin/partner_connectivity_check.sh"
METRICS_FILE="${TEXTFILE_DIR}/partner_connectivity.prom"
LOG_FILE="/var/log/partner_connectivity.log"
CURL_CONNECT_TIMEOUT=10
CURL_MAX_TIME=20

echo "=== Partner Connectivity Monitor Installation Starting ==="

# Ensure node_exporter user exists
id "${NODE_EXPORTER_USER}" >/dev/null 2>&1 || { echo "node_exporter user missing"; exit 1; }

# Directories
mkdir -p "${TEXTFILE_DIR}" "${PARTNER_CONF_DIR}"
chown "${NODE_EXPORTER_USER}:${NODE_EXPORTER_USER}" "${TEXTFILE_DIR}"
chmod 755 "${TEXTFILE_DIR}"

# Sample partner config
cat > "${PARTNER_CONF}" <<'EOF'
# partner_name host_or_ip port
partnerA 10.0.0.10 443
partnerB partner.example.com 443
EOF
chown root:"${NODE_EXPORTER_USER}" "${PARTNER_CONF}"
chmod 640 "${PARTNER_CONF}"

# Log file
touch "${LOG_FILE}"
chown "${NODE_EXPORTER_USER}:${NODE_EXPORTER_USER}" "${LOG_FILE}"
chmod 640 "${LOG_FILE}"

# Connectivity check script
cat > "${CHECKER_SCRIPT}" <<EOF
#!/usr/bin/env bash
# partner_connectivity_check.sh — Checks all partner endpoints
set -euo pipefail
IFS=\$'\n'
PARTNER_CONF="${PARTNER_CONF}"
TEXTFILE_DIR="${TEXTFILE_DIR}"
TMP_FILE="\${TEXTFILE_DIR}/.partner_connectivity.prom.\$\$"
OUT_FILE="${METRICS_FILE}"
CURL_CONNECT_TIMEOUT=${CURL_CONNECT_TIMEOUT}
CURL_MAX_TIME=${CURL_MAX_TIME}
LOG_FILE="${LOG_FILE}"

{
  echo "# HELP partner_connectivity_up Partner TCP connect success (1=up,0=down)"
  echo "# TYPE partner_connectivity_up gauge"
  echo "# HELP partner_connectivity_connect_time_seconds TCP connect time in seconds"
  echo "# TYPE partner_connectivity_connect_time_seconds gauge"
  echo "# HELP partner_connectivity_last_check_timestamp_seconds Last check timestamp"
  echo "# TYPE partner_connectivity_last_check_timestamp_seconds gauge"
} > "\${TMP_FILE}"

now=\$(date +%s)

while read -r line || [[ -n "\${line}" ]]; do
  [[ -z "\${line// }" ]] && continue
  [[ "\${line}" =~ ^# ]] && continue

  partner=\$(echo "\${line}" | awk '{print \$1}')
  host=\$(echo "\${line}" | awk '{print \$2}')
  port=\$(echo "\${line}" | awk '{print \$3}')
  up=0
  conn="0"

  result=\$(curl -sS --connect-timeout \${CURL_CONNECT_TIMEOUT} -m \${CURL_MAX_TIME} -o /dev/null -w '%{time_connect}' "telnet://\${host}:\${port}" 2>/dev/null) || rc=\$?
  rc=\${rc:-0}
  if [[ "\${rc}" -eq 0 ]]; then
    up=1
    conn=\${result:-0}
    echo "[\$(date)] OK \${partner} (\${host}:\${port}) connect_time=\${conn}" >> "\${LOG_FILE}"
  else
    up=0
    echo "[\$(date)] FAIL \${partner} (\${host}:\${port}) unreachable" >> "\${LOG_FILE}"
  fi

  printf 'partner_connectivity_up{partner="%s",host="%s",port="%s"} %s\n' "\${partner}" "\${host}" "\${port}" "\${up}" >> "\${TMP_FILE}"
  printf 'partner_connectivity_connect_time_seconds{partner="%s",host="%s",port="%s"} %s\n' "\${partner}" "\${host}" "\${port}" "\${conn}" >> "\${TMP_FILE}"
  printf 'partner_connectivity_last_check_timestamp_seconds{partner="%s",host="%s",port="%s"} %s\n' "\${partner}" "\${host}" "\${port}" "\${now}" >> "\${TMP_FILE}"
done < "\${PARTNER_CONF}"

mv -f "\${TMP_FILE}" "\${OUT_FILE}"
chown ${NODE_EXPORTER_USER}:${NODE_EXPORTER_USER} "\${OUT_FILE}" || true
chmod 644 "\${OUT_FILE}" || true
EOF

chmod 750 "${CHECKER_SCRIPT}"
echo "Checker script created: ${CHECKER_SCRIPT}"

# Enable textfile collector if missing
if ! ps -ef | grep -q -- "--collector.textfile.directory="; then
  echo "Adding textfile collector flag to Node Exporter systemd unit..."
  mkdir -p /etc/systemd/system/node_exporter.service.d
  tee /etc/systemd/system/node_exporter.service.d/textfile.conf > /dev/null <<'EOF'
[Service]
ExecStart=
ExecStart=/usr/local/bin/node_exporter --web.listen-address=:9100 --collector.textfile.directory=/var/lib/node_exporter/textfile_collector
EOF
  systemctl daemon-reload
  systemctl restart node_exporter || true
fi

echo "=== Installation Complete ==="
echo "Partners file: ${PARTNER_CONF}"
echo "Metrics file: ${METRICS_FILE}"
echo "Log file: ${LOG_FILE}"
echo "To schedule checks, see section 'Scheduling the Script' below."
```

Make executable:
```bash
sudo chmod +x /usr/local/bin/install_partner_connectivity.sh
sudo bash /usr/local/bin/install_partner_connectivity.sh
```

---

### Step 7 — Scheduling the Script

> Cron is already installed, so we’ll just add a schedule.

#### Option 1: Add to `/etc/cron.d`
```bash
sudo tee /etc/cron.d/partner_connectivity >/dev/null <<'EOF'
*/3 * * * * node_exporter /usr/local/bin/partner_connectivity_check.sh >> /var/log/partner_connectivity.log 2>&1
EOF
sudo chmod 644 /etc/cron.d/partner_connectivity
```

#### Option 2: Add to `node_exporter` user crontab
```bash
sudo crontab -u node_exporter -l 2>/dev/null | { cat; echo "*/3 * * * * /usr/local/bin/partner_connectivity_check.sh >> /var/log/partner_connectivity.log 2>&1"; } | sudo crontab -u node_exporter -
```

---

## 🔍 Verification Steps

```bash
sudo -u node_exporter /usr/local/bin/partner_connectivity_check.sh
sudo -u node_exporter cat /var/lib/node_exporter/textfile_collector/partner_connectivity.prom
curl -s http://localhost:9100/metrics | grep partner_connectivity
```

Expected output sample:
```
partner_connectivity_up{partner="partnerA",host="10.0.0.10",port="443"} 1
partner_connectivity_connect_time_seconds{partner="partnerA",host="10.0.0.10",port="443"} 0.045
partner_connectivity_last_check_timestamp_seconds{partner="partnerA",host="10.0.0.10",port="443"} 1733920000
```

---

## 🧩 Grafana Setup

**Panel 1:** Partner Status Table
```promql
partner_connectivity_up
```
Map values:
| Value | Label | Color |
|--------|--------|--------|
| 1 | ✅ Connected | Green |
| 0 | ❌ Timeout | Red |

**Panel 2:** Connection Time
```promql
partner_connectivity_connect_time_seconds{partner="$partner"}
```

**Panel 3:** Last Check Age
```promql
time() - partner_connectivity_last_check_timestamp_seconds{partner="$partner"}
```

Set threshold > 240s for stale checks.

---

## 🧰 Troubleshooting

| Problem | Resolution |
|----------|-------------|
| Metrics missing | Ensure Node Exporter started with textfile collector flag |
| File unreadable | `chown node_exporter:node_exporter /var/lib/node_exporter/textfile_collector/*.prom` |
| Cron not executing | Check `/var/log/cron` or run `systemctl status cron` |
| Permission denied | Ensure script and log are readable/writable by node_exporter |
| SELinux issues | Run `ausearch -m avc` or `setenforce 0` temporarily for debugging |

---

## 🔄 Rollback / Uninstall

```bash
sudo rm -f /usr/local/bin/partner_connectivity_check.sh
sudo rm -f /usr/local/bin/install_partner_connectivity.sh
sudo rm -f /etc/partner_monitor/partners.conf
sudo rm -f /etc/cron.d/partner_connectivity
sudo rm -f /var/log/partner_connectivity.log
sudo rm -f /var/lib/node_exporter/textfile_collector/partner_connectivity.prom
sudo rm -f /etc/systemd/system/node_exporter.service.d/textfile.conf
sudo systemctl daemon-reload
sudo systemctl restart node_exporter
```

---

## 🪪 License
MIT License — free to use, modify, and distribute.

---
✅ **End of Guide**
