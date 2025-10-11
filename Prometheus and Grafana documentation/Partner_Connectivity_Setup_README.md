# 🛰️ Partner Endpoint Connectivity Monitoring — Node Exporter Textfile Collector Integration

This guide sets up continuous TCP connectivity monitoring for partner endpoints using **Node Exporter’s textfile collector** and **Prometheus**.

It checks endpoints (like `partner.example.com:443`) using `curl -v telnet://host:port`, measures connection time, and exports Prometheus metrics:
- `partner_connectivity_up`
- `partner_connectivity_connect_time_seconds`
- `partner_connectivity_last_check_timestamp_seconds`

---

## 🔧 Overview

This setup will:
- Read partner list from `/etc/partner_monitor/partners.conf`  
- Run TCP connectivity checks using `curl`
- Write metrics into `/var/lib/node_exporter/textfile_collector/partner_connectivity.prom`
- Ensure Node Exporter reads the textfile directory (enable if missing)
- Include one-shot installer and optional scheduling commands (cron/systemd timer)
- Allow Grafana visualization of connectivity status per partner

---

## 🧭 Table of Contents
1. Manual Steps
2. One-Shot Installer Script
3. Scheduling Commands
4. Verification & Troubleshooting
5. Rollback / Uninstall
6. Grafana Visualization
7. License

---

## 1️⃣ Full Manual Setup (Step-by-Step)

### Step 1 — Verify Node Exporter
```bash
ps -ef | grep '[n]ode_exporter'
systemctl show -p ExecStart --value node_exporter || true
```
> Ensure Node Exporter runs as the user `node_exporter`.  
> If not, update the installer variable `NODE_EXPORTER_USER` before running it.

### Step 2 — Create Textfile Collector Directory
```bash
sudo mkdir -p /var/lib/node_exporter/textfile_collector
sudo chown node_exporter:node_exporter /var/lib/node_exporter/textfile_collector
sudo chmod 755 /var/lib/node_exporter/textfile_collector
```
> Node Exporter reads `.prom` files from this directory if started with  
> `--collector.textfile.directory=/var/lib/node_exporter/textfile_collector`.

### Step 3 — Verify Textfile Collector Enabled
Check:
```bash
ps -ef | grep '[n]ode_exporter' -o
systemctl show -p ExecStart --value node_exporter || true
```
If **you do not see `--collector.textfile.directory=...`**, enable it:
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

### Step 4 — Create Log File
```bash
sudo touch /var/log/partner_connectivity.log
sudo chown node_exporter:node_exporter /var/log/partner_connectivity.log
sudo chmod 640 /var/log/partner_connectivity.log
```

### Step 5 — Create Partner Config File
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

### Step 6 — Install the One-Shot Script
See the full script in section 2.  
It will create directories, config, metrics, and enable Node Exporter’s textfile collector if not active.

---

## 2️⃣ One-Shot Installer Script

Save as `install_partner_connectivity.sh` and run:
```bash
sudo bash install_partner_connectivity.sh
```

(Refer to the full script in previous response)

---

## 3️⃣ Scheduling Command Options

We don’t install cron automatically; here are your ready-to-run options.

### Option 1 — Add to `/etc/cron.d`
```bash
sudo tee /etc/cron.d/partner_connectivity >/dev/null <<'EOF'
*/3 * * * * node_exporter /usr/local/bin/partner_connectivity_check.sh >> /var/log/partner_connectivity.log 2>&1
EOF
sudo chmod 644 /etc/cron.d/partner_connectivity
```

### Option 2 — Add to node_exporter user’s crontab
```bash
sudo crontab -u node_exporter -l 2>/dev/null | { cat; echo "*/3 * * * * /usr/local/bin/partner_connectivity_check.sh >> /var/log/partner_connectivity.log 2>&1"; } | sudo crontab -u node_exporter -
```

### Option 3 — Systemd timer
```bash
sudo tee /etc/systemd/system/partner_connectivity.service > /dev/null <<'EOF'
[Unit]
Description=Partner Connectivity Check
[Service]
Type=oneshot
User=node_exporter
ExecStart=/usr/local/bin/partner_connectivity_check.sh
EOF

sudo tee /etc/systemd/system/partner_connectivity.timer > /dev/null <<'EOF'
[Unit]
Description=Run partner connectivity check every 3 minutes
[Timer]
OnCalendar=*:0/3
Persistent=true
[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now partner_connectivity.timer
```

---

## 4️⃣ Verification & Troubleshooting

### Verify Metrics
```bash
sudo -u node_exporter /usr/local/bin/partner_connectivity_check.sh
sudo -u node_exporter cat /var/lib/node_exporter/textfile_collector/partner_connectivity.prom
```

### Prometheus Query
```promql
partner_connectivity_up
```

### Grafana
- Query: `partner_connectivity_up`
- Value Mappings:
  - 1 → ✅ Connected (green)
  - 0 → ❌ Timeout (red)

### Troubleshooting
| Issue | Resolution |
|-------|-------------|
| Metrics missing | Check Node Exporter `--collector.textfile.directory` flag |
| File unreadable | `chown node_exporter:node_exporter /var/lib/node_exporter/textfile_collector/*.prom` |
| Cron not running | `systemctl status cron` or `systemctl status crond` |
| SELinux blocking | check `ausearch -m avc` |

---

## 5️⃣ Rollback / Uninstall

```bash
sudo rm -f /usr/local/bin/partner_connectivity_check.sh
sudo rm -f /etc/partner_monitor/partners.conf
sudo rm -f /var/log/partner_connectivity.log
sudo rm -f /var/lib/node_exporter/textfile_collector/partner_connectivity.prom
sudo rm -f /etc/systemd/system/partner_connectivity.timer
sudo rm -f /etc/systemd/system/partner_connectivity.service
sudo rm -f /etc/cron.d/partner_connectivity
sudo rm -f /etc/systemd/system/node_exporter.service.d/textfile.conf
sudo systemctl daemon-reload
sudo systemctl restart node_exporter || true
```

---

## 6️⃣ Grafana Dashboard

**Panel 1:** Partner Status  
Query:
```promql
partner_connectivity_up
```
Format: Table or Stat  
Value mappings:
| Value | Display | Color |
|--------|----------|--------|
| 1 | Connected | Green |
| 0 | Timeout | Red |

**Panel 2:** Connection Time  
Query:
```promql
partner_connectivity_connect_time_seconds{partner="$partner"}
```

**Panel 3:** Last Check Age  
Query:
```promql
time() - partner_connectivity_last_check_timestamp_seconds{partner="$partner"}
```
Threshold: > 240s (3m check interval + buffer)

---

## 7️⃣ License

MIT License — free to use, modify, and share.

---

✅ **End of file**
