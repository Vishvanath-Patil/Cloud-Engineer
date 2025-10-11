# 🛰️ Partner Endpoint Connectivity Monitoring — Simplified (Connected / Connection Timeout Only)

This guide sets up TCP connectivity checks for specific partner endpoints using **Node Exporter’s Textfile Collector** and **Prometheus**.
The checker reports **only** whether each partner is _Connected_ (1) or _Connection Timeout_ (0), plus the last-check timestamp — no extra timing metrics.

## Metrics exported (only these)

- `partner_connectivity_up{partner,host,port}` — `1` = Connected, `0` = Connection Timeout
- `partner_connectivity_last_check_timestamp_seconds{partner,host,port}` — unix epoch of last check

---

## Prerequisites

1. Node Exporter installed and running as user `node_exporter` (or update variable in script).
2. `curl` installed and supports `telnet://`.
3. Prometheus scraping Node Exporter.
4. Root (sudo) access to create files and systemd drop-ins.

---

## Quick architecture

```
partners.conf (list) -> checker script -> /var/lib/node_exporter/textfile_collector/partner_connectivity.prom
-> Node Exporter (textfile collector) -> Prometheus -> Grafana
```

---

## Manual setup (summary)

1. Create textfile directory:

```bash
sudo mkdir -p /var/lib/node_exporter/textfile_collector
sudo chown node_exporter:node_exporter /var/lib/node_exporter/textfile_collector
sudo chmod 755 /var/lib/node_exporter/textfile_collector
```

2. Create partners file:

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

3. Create log file:

```bash
sudo touch /var/log/partner_connectivity.log
sudo chown node_exporter:node_exporter /var/log/partner_connectivity.log
sudo chmod 640 /var/log/partner_connectivity.log
```

4. Ensure Node Exporter has textfile collector enabled. If missing, add systemd drop-in:

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

---

## One-shot installer script (ready-to-run)

Save the content below as `install_partner_connectivity_simple.sh`, make it executable and run it with `sudo`.

```bash
#!/usr/bin/env bash
# install_partner_connectivity_simple.sh
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

echo "Starting installation..."

# validate user
if ! id "${NODE_EXPORTER_USER}" >/dev/null 2>&1; then
  echo "ERROR: user ${NODE_EXPORTER_USER} not found. Aborting."
  exit 1
fi

# create directories and files
mkdir -p "${TEXTFILE_DIR}" "${PARTNER_CONF_DIR}"
chown "${NODE_EXPORTER_USER}:${NODE_EXPORTER_USER}" "${TEXTFILE_DIR}"
chmod 755 "${TEXTFILE_DIR}"

cat > "${PARTNER_CONF}" <<'EOF'
# partner_name host_or_ip port
partnerA 10.0.0.10 443
partnerB partner.example.com 443
EOF
chown root:"${NODE_EXPORTER_USER}" "${PARTNER_CONF}"
chmod 640 "${PARTNER_CONF}"

touch "${LOG_FILE}"
chown "${NODE_EXPORTER_USER}:${NODE_EXPORTER_USER}" "${LOG_FILE}"
chmod 640 "${LOG_FILE}"

# write checker script
cat > "${CHECKER_SCRIPT}" <<'EOF'
#!/usr/bin/env bash
# partner_connectivity_check.sh
# Checks partners listed in /etc/partner_monitor/partners.conf
set -euo pipefail
IFS=$'\n'

PARTNER_CONF="/etc/partner_monitor/partners.conf"
TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
OUT_TMP="${TEXTFILE_DIR}/.partner_connectivity.prom.$$"
OUT_FINAL="${TEXTFILE_DIR}/partner_connectivity.prom"
LOG_FILE="/var/log/partner_connectivity.log"
CURL_CONNECT_TIMEOUT=10
CURL_MAX_TIME=20

# header
{
  echo "# HELP partner_connectivity_up Partner TCP connect success (1=connected,0=timeout)"
  echo "# TYPE partner_connectivity_up gauge"
  echo "# HELP partner_connectivity_last_check_timestamp_seconds Last check unix epoch"
  echo "# TYPE partner_connectivity_last_check_timestamp_seconds gauge"
} > "${OUT_TMP}"

now_ts=$(date +%s)

if [[ ! -f "${PARTNER_CONF}" ]]; then
  echo "ERROR: partner config not found: ${PARTNER_CONF}" >&2
  exit 2
fi

while read -r line || [[ -n "${line}" ]]; do
  [[ -z "${line// }" ]] && continue
  [[ "${line}" =~ ^# ]] && continue

  partner=$(echo "${line}" | awk '{print $1}')
  host=$(echo "${line}" | awk '{print $2}')
  port=$(echo "${line}" | awk '{print $3}')

  if [[ -z "${partner}" || -z "${host}" || -z "${port}" ]]; then
    echo "$(date) WARN: invalid line skipped: ${line}" >> "${LOG_FILE}" 2>/dev/null || true
    continue
  fi

  up=0
  # only check connect success or timeout; ignore timings
  rc=0
  curl -sS --connect-timeout ${CURL_CONNECT_TIMEOUT} -m ${CURL_MAX_TIME} -o /dev/null "telnet://${host}:${port}" 2>/dev/null || rc=$?
  rc=${rc:-0}
  if [[ "${rc}" -eq 0 ]]; then
    up=1
    echo "$(date) INFO: ${partner} ${host}:${port} CONNECTED" >> "${LOG_FILE}" 2>/dev/null || true
  else
    up=0
    echo "$(date) WARN: ${partner} ${host}:${port} CONNECTION_TIMEOUT rc=${rc}" >> "${LOG_FILE}" 2>/dev/null || true
  fi

  printf 'partner_connectivity_up{partner="%s",host="%s",port="%s"} %s\n' "${partner}" "${host}" "${port}" "${up}" >> "${OUT_TMP}"
  printf 'partner_connectivity_last_check_timestamp_seconds{partner="%s",host="%s",port="%s"} %s\n' "${partner}" "${host}" "${port}" "${now_ts}" >> "${OUT_TMP}"

done < "${PARTNER_CONF}"

mv -f "${OUT_TMP}" "${OUT_FINAL}"
chown ${NODE_EXPORTER_USER}:${NODE_EXPORTER_USER} "${OUT_FINAL}" 2>/dev/null || true
chmod 644 "${OUT_FINAL}" 2>/dev/null || true
EOF

chmod 750 "${CHECKER_SCRIPT}"
chown root:root "${CHECKER_SCRIPT}"

# enable textfile collector if missing (systemd drop-in)
if ! ps -ef | grep -q -- "--collector.textfile.directory="; then
  mkdir -p /etc/systemd/system/node_exporter.service.d
  cat > /etc/systemd/system/node_exporter.service.d/textfile.conf <<EOT
[Service]
ExecStart=
ExecStart=/usr/local/bin/node_exporter --web.listen-address=:9100 --collector.textfile.directory=${TEXTFILE_DIR}
EOT
  systemctl daemon-reload
  systemctl restart node_exporter || true
fi

echo "Installation complete. Edit ${PARTNER_CONF} to set partners, then schedule the checker every 3 minutes as node_exporter."
```

## Scheduling instructions (example cron)

Add to system cron (/etc/cron.d):

```bash
sudo tee /etc/cron.d/partner_connectivity >/dev/null <<'EOF'
*/3 * * * * node_exporter /usr/local/bin/partner_connectivity_check.sh >> /var/log/partner_connectivity.log 2>&1
EOF
sudo chmod 644 /etc/cron.d/partner_connectivity
```

## Verification

Run one-off check and inspect metrics:

```bash
sudo -u node_exporter /usr/local/bin/partner_connectivity_check.sh
sudo -u node_exporter cat /var/lib/node_exporter/textfile_collector/partner_connectivity.prom
curl -s http://localhost:9100/metrics | grep partner_connectivity
```

Expected sample:

```
partner_connectivity_up{partner="partnerA",host="10.0.0.10",port="443"} 1
partner_connectivity_last_check_timestamp_seconds{partner="partnerA",host="10.0.0.10",port="443"} 1733920000
```

## Grafana

Query `partner_connectivity_up` and map 1→Connected (green), 0→Timeout (red).

## Troubleshooting & Rollback

Remove installed files:

```bash
sudo rm -f /usr/local/bin/partner_connectivity_check.sh
sudo rm -f /usr/local/bin/install_partner_connectivity_simple.sh
sudo rm -f /etc/partner_monitor/partners.conf
sudo rm -f /etc/cron.d/partner_connectivity
sudo rm -f /var/log/partner_connectivity.log
sudo rm -f /var/lib/node_exporter/textfile_collector/partner_connectivity.prom
sudo rm -f /etc/systemd/system/node_exporter.service.d/textfile.conf
sudo systemctl daemon-reload
sudo systemctl restart node_exporter || true
```

---

License: MIT
