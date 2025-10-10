
# Libreswan IPsec Tunnel Monitoring (Phase 1, Phase 2, and ED IP Reachability) — Node Exporter Integration

This document provides a **complete end-to-end setup** for monitoring **Libreswan IPsec VPN tunnels** on Linux servers using the **Node Exporter textfile collector**.  

It detects the **status of each tunnel**, including:
- Phase 1 (IKE SA)
- Phase 2 (IPsec SA)
- Per-endpoint (ED IP) reachability

Metrics are scraped by **Prometheus** and visualized in **Grafana**, with optional **email alerts** via Alertmanager.

---

## 🔍 Overview

| Metric | Description |
|---------|--------------|
| `ipsec_tunnel_p1_up` | Phase 1 (IKE) established status |
| `ipsec_tunnel_p2_up` | Phase 2 (IPsec) established status |
| `ipsec_tunnel_remote_reachable` | ED IP reachability check via ping/tcp |
| `ipsec_tunnel_check_duration_seconds` | Duration of each tunnel check |

All metrics are labeled with `tunnel`, `remote`, and (for Phase 2) `p2name`.

---

## ⚙️ Prerequisites

- **Libreswan** installed and operational (`ipsec` command available).
- **Node Exporter** installed with `--collector.textfile.directory=/var/lib/node_exporter/textfile_collector`.
- Tools: `bash`, `awk`, `grep`, `timeout`, `ping`, `nc`.
- Sudo/root privileges to access `/etc/ipsec.d` and run `ipsec status`.

---

## 📁 File structure created

| File | Purpose |
|------|----------|
| `/usr/local/bin/ipsec_tunnel_monitor.sh` | Main collector script |
| `/etc/cron.d/ipsec_tunnel_monitor` | Cron job to run every 5 minutes |
| `/var/lib/node_exporter/textfile_collector/ipsec_tunnels.prom` | Output metrics file |

---

## 🧱 Installation (One-shot Setup Script)

Save this as `/tmp/setup-ipsec-tunnel-monitor.sh` and run:

```bash
sudo bash /tmp/setup-ipsec-tunnel-monitor.sh
```

### Script contents

```bash
#!/bin/bash
set -euo pipefail

NODE_USER="marigold"
TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
SCRIPT_PATH="/usr/local/bin/ipsec_tunnel_monitor.sh"
CRON_FILE="/etc/cron.d/ipsec_tunnel_monitor"
CRON_SPEC="*/5 * * * *"
IPSEC_BIN="$(command -v ipsec || echo /sbin/ipsec)"

mkdir -p "$TEXTFILE_DIR"
chown -R "${NODE_USER}:${NODE_USER}" "$TEXTFILE_DIR" || true
chmod 755 "$TEXTFILE_DIR"

cat > "$SCRIPT_PATH" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
OUTFILE="$TEXTFILE_DIR/ipsec_tunnels.prom"
TMPOUT="${OUTFILE}.tmp.$$"
IPSEC_BIN="$(command -v ipsec || echo /sbin/ipsec)"
PING_TIMEOUT=2
NC_TIMEOUT=2

write_header() {
  echo "# HELP ipsec_tunnel_p1_up Phase 1 IKE status" > "$TMPOUT"
  echo "# TYPE ipsec_tunnel_p1_up gauge" >> "$TMPOUT"
  echo "# HELP ipsec_tunnel_p2_up Phase 2 IPsec status" >> "$TMPOUT"
  echo "# TYPE ipsec_tunnel_p2_up gauge" >> "$TMPOUT"
  echo "# HELP ipsec_tunnel_remote_reachable Endpoint reachability" >> "$TMPOUT"
  echo "# TYPE ipsec_tunnel_remote_reachable gauge" >> "$TMPOUT"
}

discover_conns() {
  grep -h "conn " /etc/ipsec.d/*.conf /etc/ipsec.conf 2>/dev/null | awk '{print $2}' | sort -u
}

check_reach() {
  local ip="$1"
  ping -c1 -W $PING_TIMEOUT "$ip" >/dev/null 2>&1 && echo 1 && return
  timeout $NC_TIMEOUT bash -c "</dev/tcp/$ip/500" >/dev/null 2>&1 && echo 1 && return
  echo 0
}

write_header

mapfile -t conns < <(discover_conns)

for c in "${conns[@]}"; do
  # detect remote IP
  remote=$(grep -A3 "conn $c" /etc/ipsec.d/*.conf /etc/ipsec.conf 2>/dev/null | grep "right=" | head -1 | awk -F= '{print $2}' | xargs)
  [ -z "$remote" ] && continue

  reach=$(check_reach "$remote")
  echo "ipsec_tunnel_remote_reachable{tunnel="$c",remote="$remote"} $reach" >> "$TMPOUT"

  # check ipsec status
  if $IPSEC_BIN status "$c" 2>/dev/null | grep -q "ESTABLISHED"; then
    echo "ipsec_tunnel_p1_up{tunnel="$c",remote="$remote"} 1" >> "$TMPOUT"
  else
    echo "ipsec_tunnel_p1_up{tunnel="$c",remote="$remote"} 0" >> "$TMPOUT"
  fi

  if $IPSEC_BIN status "$c" 2>/dev/null | grep -q "INSTALLED"; then
    echo "ipsec_tunnel_p2_up{tunnel="$c",remote="$remote"} 1" >> "$TMPOUT"
  else
    echo "ipsec_tunnel_p2_up{tunnel="$c",remote="$remote"} 0" >> "$TMPOUT"
  fi
done

mv "$TMPOUT" "$OUTFILE"
chown "$NODE_USER:$NODE_USER" "$OUTFILE" 2>/dev/null || true
chmod 644 "$OUTFILE"
EOF

chmod +x "$SCRIPT_PATH"

# cron job
echo "$CRON_SPEC root $SCRIPT_PATH >/dev/null 2>&1" > "$CRON_FILE"
chmod 644 "$CRON_FILE"

echo "✅ Installed: $SCRIPT_PATH and $CRON_FILE"
echo "Run manually to verify: sudo $SCRIPT_PATH"
```

---

## 🧾 Prometheus Alert Rules Example

Save as `/etc/prometheus/rules/ipsec_tunnel.rules.yml`:

```yaml
groups:
  - name: ipsec_tunnel_alerts
    rules:
      - alert: IPSecPhase1Down
        expr: ipsec_tunnel_p1_up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Phase 1 Down for {{ $labels.tunnel }}"
          description: "Phase 1 IKE SA not established for {{ $labels.remote }}"

      - alert: IPSecPhase2Down
        expr: ipsec_tunnel_p2_up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Phase 2 Down for {{ $labels.tunnel }}"
          description: "Phase 2 IPsec SA missing for {{ $labels.remote }}"

      - alert: EndpointUnreachable
        expr: ipsec_tunnel_remote_reachable == 0
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "Endpoint {{ $labels.remote }} Unreachable"
          description: "No ICMP/TCP connectivity to {{ $labels.remote }}"
```

---

## 📊 Grafana Dashboard Panels

| Panel | Query | Visualization | Unit |
|--------|--------|---------------|------|
| Tunnel Phase 1 | `ipsec_tunnel_p1_up` | Table | 0/1 |
| Tunnel Phase 2 | `ipsec_tunnel_p2_up` | Table | 0/1 |
| Endpoint Reachability | `ipsec_tunnel_remote_reachable` | Table | 0/1 |
| Tunnel Health Trend | `sum by(tunnel) (ipsec_tunnel_p2_up)` | Time series | Status |

**Recommended panel mappings:**
- 1 → Green ("Up")
- 0 → Red ("Down")

---

## 🔍 Verification

Run once manually:
```bash
sudo /usr/local/bin/ipsec_tunnel_monitor.sh
cat /var/lib/node_exporter/textfile_collector/ipsec_tunnels.prom
```

Check Node Exporter metrics:
```bash
curl -s http://localhost:9100/metrics | grep ipsec_tunnel_
```

---

## 🧰 Troubleshooting

| Issue | Check |
|--------|-------|
| No tunnels detected | Ensure `.conf` files exist in `/etc/ipsec.d/` and contain `conn` entries |
| Metrics not updating | Check cron logs: `grep CRON /var/log/syslog` |
| ipsec command fails | Run `sudo ipsec status` manually |
| Prometheus not scraping | Verify target in Prometheus config |

---

## ♻️ Rollback

```bash
sudo rm -f /etc/cron.d/ipsec_tunnel_monitor
sudo rm -f /usr/local/bin/ipsec_tunnel_monitor.sh
sudo rm -f /var/lib/node_exporter/textfile_collector/ipsec_tunnels.prom
sudo systemctl restart node_exporter
```

---

**Author:** DevOps / CloudOps Team  
**Version:** v1.0 (Libreswan Tunnel Monitoring)
