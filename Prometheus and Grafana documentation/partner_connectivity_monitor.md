
# Partner Connectivity & SSL Expiry Monitoring (Unified Setup)

Monitoring target: **Partner connectivity** using TCP connect test and **SSL certificate expiry** for partners. This guide provides a complete end-to-end setup using a **single unified collector script** integrated with **Node Exporter's textfile collector**, **Prometheus**, and **Grafana**.

It includes:
- Manual setup with detailed explanation
- Full ready-to-run **one-shot installer script**
- Verification, troubleshooting, rollback, and Prometheus + Grafana examples
- Config-driven partners list at `/etc/partner_monitor/partners.conf`

---

## Quick summary of outputs (metrics)

Metrics written to `/var/lib/node_exporter/textfile_collector/partner_connectivity.prom`:

- `partner_connectivity_up{partner="NAME", target="host:port"} 1|0`  
  1 = TCP connect succeeded, 0 = failed
- `partner_ssl_notafter_seconds{partner="NAME", target="host:port"} <unix_epoch_seconds>`  
  epoch seconds of certificate `notAfter` (0 when unknown)
- `partner_ssl_days_left{partner="NAME", target="host:port"} <float_days>`  
  days remaining until expiry (-1 if unknown/failed)
- `partner_check_duration_seconds{partner="NAME", target="host:port", check="connect|ssl"} <seconds>`  
  duration of checks for visibility

Labels: `partner` (friendly name) and `target` (host:port).

---

## Prerequisites & notes

- Node Exporter must be installed and configured to expose a textfile collector directory (`/var/lib/node_exporter/textfile_collector`). See earlier guides if needed.
- Requires `bash`, `openssl`, and `timeout` (coreutils) installed on the host.
- Script runs as root via systemd (so it can reach /dev/tcp and open SSL connections). If you need non-root operation, ensure the service user has network access and permission to write to the textfile directory.
- Respect partner rate limits; default interval is 5 minutes. Coordinate with partners before high-frequency checks.

---

## Manual setup (step-by-step)

### 1) Create configuration directory & partner list
Create `/etc/partner_monitor/partners.conf` with one partner per line using the format:
```
partner_name|host|port|servername_optional
```
`servername_optional` is used for SNI when fetching the cert; leave empty to use the host.

Example:
```bash
sudo mkdir -p /etc/partner_monitor
sudo tee /etc/partner_monitor/partners.conf > /dev/null <<'EOF'
# partner_name|host|port|servername_optional
PartnerA|192.0.2.10|443|
PartnerB|partner.example.com|443|partner.example.com
EOF
sudo chmod 640 /etc/partner_monitor/partners.conf
sudo chown root:root /etc/partner_monitor/partners.conf
```

**Notes:**
- Lines starting with `#` or blank lines are ignored.
- Use `|` as delimiter to avoid conflicts with `:` in IPv6 or ports.

### 2) Create textfile collector directory (if not present)
```bash
sudo mkdir -p /var/lib/node_exporter/textfile_collector
# Adjust owner to the node_exporter user (example: marigold)
sudo chown -R marigold:marigold /var/lib/node_exporter/textfile_collector || true
sudo chmod 755 /var/lib/node_exporter/textfile_collector
```

### 3) Create the collector script (manual)
Create `/usr/local/bin/partner_monitor.sh` (we provide this in the one-shot script too). The script will:
- Read `/etc/partner_monitor/partners.conf`
- For each partner: perform TCP connect test and attempt SSL cert fetch
- Compute epoch notAfter and days left, and measure durations
- Write metrics in Prometheus text format to `/var/lib/node_exporter/textfile_collector/partner_connectivity.prom`

### 4) Create systemd service & timer
Create `/etc/systemd/system/partner_monitor.service`:
```ini
[Unit]
Description=Partner connectivity and SSL expiry monitoring (one-shot)
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/partner_monitor.sh
User=root
Group=root
```

Create `/etc/systemd/system/partner_monitor.timer`:
```ini
[Unit]
Description=Run partner_monitor every 5m

[Timer]
OnBootSec=1min
OnUnitActiveSec=5m
Unit=partner_monitor.service

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now partner_monitor.timer
sudo systemctl start partner_monitor.service
```

---

## One-shot installer script (full, ready-to-run)

Save this as `/tmp/setup-partner-monitor.sh`, inspect variables at top, then run:

```bash
sudo bash /tmp/setup-partner-monitor.sh
```

```bash
#!/bin/bash
set -euo pipefail

# One-shot installer for Partner connectivity & SSL expiry monitoring
# Writes metrics to Node Exporter's textfile collector
# Inspect variables below before running

NODE_USER="marigold"         # owner of textfile dir (adjust to your node_exporter user)
TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
PROCESS_SCRIPT="/usr/local/bin/partner_monitor.sh"
SERVICE_FILE="/etc/systemd/system/partner_monitor.service"
TIMER_FILE="/etc/systemd/system/partner_monitor.timer"
CONFIG_DIR="/etc/partner_monitor"
CONFIG_FILE="$CONFIG_DIR/partners.conf"
COLLECT_INTERVAL="5m"        # systemd timer interval for checks (default 5m)
CONNECT_TIMEOUT=5            # seconds for TCP connect test
SSL_TIMEOUT=10               # seconds for SSL fetching

echo "== Partner monitor installer =="

# 1) create config dir and sample config if missing
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_FILE" ]; then
  cat > "$CONFIG_FILE" <<'EOF'
# partner_name|host|port|servername_optional
PartnerA|192.0.2.10|443|
PartnerB|partner.example.com|443|partner.example.com
EOF
  chmod 640 "$CONFIG_FILE"
  chown root:root "$CONFIG_FILE"
  echo "- Sample config created at $CONFIG_FILE"
else
  echo "- Config exists at $CONFIG_FILE"
fi

# 2) create textfile collector dir
mkdir -p "$TEXTFILE_DIR"
chown -R "${NODE_USER}:${NODE_USER}" "$TEXTFILE_DIR" 2>/dev/null || true
chmod 755 "$TEXTFILE_DIR"
echo "- Textfile collector dir: $TEXTFILE_DIR"

# 3) write the collector script
cat > "$PROCESS_SCRIPT" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

CONFIG_FILE="/etc/partner_monitor/partners.conf"
TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
OUTFILE="$TEXTFILE_DIR/partner_connectivity.prom"
TMPOUT="${OUTFILE}.tmp.$$"
CONNECT_TIMEOUT=${CONNECT_TIMEOUT:-5}
SSL_TIMEOUT=${SSL_TIMEOUT:-10}

timestamp_now() { date +%s; }

# tcp_check host port -> exit 0 if connect ok, 1 otherwise; sets DURATION variable
tcp_check() {
  local host="$1" port="$2" start end rc
  start=$(date +%s.%N)
  if timeout ${CONNECT_TIMEOUT}s bash -c "cat < /dev/null > /dev/tcp/${host}/${port}" >/dev/null 2>&1; then
    rc=0
  else
    rc=1
  fi
  end=$(date +%s.%N)
  DURATION=$(awk "BEGIN { print (${end} - ${start}) }")
  return $rc
}

# ssl_expiry host port servername -> outputs epoch seconds or empty; sets DURATION_SSL
ssl_expiry() {
  local host="$1" port="$2" servername="$3" start end cert_pem notafter epoch
  start=$(date +%s.%N)
  if cert_pem=$(timeout ${SSL_TIMEOUT}s openssl s_client -servername "${servername}" -connect "${host}:${port}" < /dev/null 2>/dev/null | openssl x509 -noout 2>/dev/null); then
    :
  else
    cert_pem=""
  fi
  if [ -n "$cert_pem" ]; then
    notafter=$(echo "$cert_pem" | openssl x509 -noout -enddate 2>/dev/null | sed 's/notAfter=//')
    if [ -n "$notafter" ]; then
      epoch=$(date -d "$notafter" +%s 2>/dev/null || echo "")
    else
      epoch=""
    fi
  else
    epoch=""
  fi
  end=$(date +%s.%N)
  DURATION_SSL=$(awk "BEGIN { print (${end} - ${start}) }")
  echo "$epoch"
}

# Build metrics header
echo "# Generated by partner_monitor.sh on $(date -u --rfc-3339=seconds)" > "$TMPOUT"
echo "# HELP partner_connectivity_up 1 if TCP connect succeeded, 0 otherwise" >> "$TMPOUT"
echo "# TYPE partner_connectivity_up gauge" >> "$TMPOUT"
echo "# HELP partner_ssl_notafter_seconds Certificate notAfter as unix epoch seconds" >> "$TMPOUT"
echo "# TYPE partner_ssl_notafter_seconds gauge" >> "$TMPOUT"
echo "# HELP partner_ssl_days_left Days left until cert expiry" >> "$TMPOUT"
echo "# TYPE partner_ssl_days_left gauge" >> "$TMPOUT"
echo "# HELP partner_check_duration_seconds Duration of the check (seconds)" >> "$TMPOUT"
echo "# TYPE partner_check_duration_seconds gauge" >> "$TMPOUT"

while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in ''|\#*) continue ;; esac
  IFS='|' read -r pname phost pport pservername <<< "$line"
  pname=$(echo "$pname" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  phost=$(echo "$phost" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  pport=$(echo "$pport" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  pservername=$(echo "$pservername" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  [ -z "$pservername" ] && pservername="$phost"
  [ -z "$pport" ] && pport=443
  target="${phost}:${pport}"

  # TCP check
  if tcp_check "$phost" "$pport"; then up=1; else up=0; fi
  printf 'partner_connectivity_up{partner="%s",target="%s"} %d
' "$pname" "$target" "$up" >> "$TMPOUT"
  printf 'partner_check_duration_seconds{partner="%s",target="%s",check="connect"} %.3f
' "$pname" "$target" "$DURATION" >> "$TMPOUT"

  # SSL expiry check
  ssl_epoch=$(ssl_expiry "$phost" "$pport" "$pservername" 2>/dev/null || echo "")
  if [ -n "$ssl_epoch" ]; then
    now=$(date +%s)
    days_left=$(awk "BEGIN { printf "%.3f", ($ssl_epoch - $now) / 86400 }")
    printf 'partner_ssl_notafter_seconds{partner="%s",target="%s"} %s
' "$pname" "$target" "$ssl_epoch" >> "$TMPOUT"
    printf 'partner_ssl_days_left{partner="%s",target="%s"} %.3f
' "$pname" "$target" "$days_left" >> "$TMPOUT"
    printf 'partner_check_duration_seconds{partner="%s",target="%s",check="ssl"} %.3f
' "$pname" "$target" "$DURATION_SSL" >> "$TMPOUT"
  else
    printf 'partner_ssl_notafter_seconds{partner="%s",target="%s"} %d
' "$pname" "$target" 0 >> "$TMPOUT"
    printf 'partner_ssl_days_left{partner="%s",target="%s"} %d
' "$pname" "$target" -1 >> "$TMPOUT"
    printf 'partner_check_duration_seconds{partner="%s",target="%s",check="ssl"} %.3f
' "$pname" "$target" "$DURATION_SSL" >> "$TMPOUT"
  fi
done < "$CONFIG_FILE"

mv "$TMPOUT" "$OUTFILE"
chown root:root "$OUTFILE" 2>/dev/null || true
chmod 644 "$OUTFILE"
EOF

chmod 755 "$PROCESS_SCRIPT"
chown root:root "$PROCESS_SCRIPT"
echo "- Collector script written to $PROCESS_SCRIPT"

# 4) create systemd service and timer
cat > "$SERVICE_FILE" <<'EOF'
[Unit]
Description=Partner connectivity and SSL expiry monitoring (one-shot)
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/partner_monitor.sh
User=root
Group=root
EOF

cat > "$TIMER_FILE" <<'EOF'
[Unit]
Description=Run partner_monitor every ${COLLECT_INTERVAL}

[Timer]
OnBootSec=1min
OnUnitActiveSec=${COLLECT_INTERVAL}
Unit=partner_monitor.service

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now partner_monitor.timer
systemctl start partner_monitor.service || true

echo "== Done. Metrics will be written to $TEXTFILE_DIR/partner_connectivity.prom"
echo "Edit $CONFIG_FILE to add / remove partners. Restart service to re-run immediately:"
echo "  sudo systemctl restart partner_monitor.service"
```

---

## Prometheus rules example (alert on connectivity down or SSL expiring soon)

Save to `/etc/prometheus/rules/partner_monitor.rules.yml` and include in your Prometheus `rule_files`:

```yaml
groups:
  - name: partner_monitor_alerts
    rules:
      - alert: PartnerConnectivityDown
        expr: partner_connectivity_up{target=~".*"} == 0
        for: 2m
        labels:
          severity: page
        annotations:
          summary: "Partner connectivity down for {{ $labels.partner }} ({{ $labels.target }})"
          description: "TCP connection to {{ $labels.target }} failed for more than 2 minutes."

      - alert: PartnerSSLCertificateExpiringSoon
        expr: partner_ssl_days_left < 7 and partner_ssl_days_left >= 0
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "SSL certificate for {{ $labels.partner }} expires in {{ $value }} days"
          description: "Certificate for {{ $labels.partner }} ({{ $labels.target }}) will expire soon."
```

---

## Grafana dashboard examples & panels

1. **Connectivity Status (table or stat)**  
   - Query: `partner_connectivity_up`  
   - Use value mappings: `1 -> Up (green)`, `0 -> Down (red)`
   - Show `partner` and `target` labels

2. **SSL Days Left (table or bar)**  
   - Query: `partner_ssl_days_left`  
   - Unit: `days`  
   - Thresholds: >30 green, 7–30 orange, <7 red

3. **SSL Expiry Timeline**  
   - Query: `partner_ssl_notafter_seconds` → convert epoch to date in table or transform to time series

4. **Check Duration (detect slow partners)**  
   - Query: `partner_check_duration_seconds{check="connect"}` and `partner_check_duration_seconds{check="ssl"}`

---

## Verification & troubleshooting

- Check metrics file exists:
```bash
ls -l /var/lib/node_exporter/textfile_collector/partner_connectivity.prom
cat /var/lib/node_exporter/textfile_collector/partner_connectivity.prom | sed -n '1,200p'
```

- Check Node Exporter metrics include partner metrics:
```bash
curl -s http://localhost:9100/metrics | grep partner_connectivity_up -m 20
```

- Check systemd logs for errors:
```bash
journalctl -u partner_monitor.service -n 200 --no-pager
```

- Debug SSL fetch manually:
```bash
timeout 10 openssl s_client -servername partner.example.com -connect partner.example.com:443 < /dev/null | openssl x509 -noout -enddate
```

---

## Rollback / cleanup

```bash
sudo systemctl disable --now partner_monitor.timer
sudo systemctl stop partner_monitor.service || true
sudo rm -f /etc/systemd/system/partner_monitor.{service,timer}
sudo rm -f /usr/local/bin/partner_monitor.sh
sudo rm -f /var/lib/node_exporter/textfile_collector/partner_connectivity.prom
sudo rm -f /etc/partner_monitor/partners.conf   # optional - backup first if needed
sudo systemctl daemon-reload
```

---

## Security & operational notes

- Frequent SSL probing may trigger partner IDS/IPS; coordinate schedules.  
- Protect `/etc/partner_monitor/partners.conf` as it contains infrastructure endpoints.  
- Consider a pushgateway or remote write if you need counters persisted across reboots.

---

**Author:** DevOps / Monitoring Team  
**Version:** 1.0
