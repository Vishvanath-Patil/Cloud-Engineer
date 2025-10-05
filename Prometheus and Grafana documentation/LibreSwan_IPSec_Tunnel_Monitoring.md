# LibreSwan IPSec Tunnel Monitoring with Prometheus, Grafana, and Teams

## 1. Objective

Monitor multiple **LibreSwan IPSec tunnels** defined under `/etc/ipsec.d/` for connectivity and uptime across multiple EIG/IPSec servers.  
This setup reports:  
- 🟢 Tunnel up (established)  
- 🔴 Tunnel down (inactive or failed)  
- ⚠️ Stale metrics or script failures  

---

## 2. Architecture Overview (Draw.io Style)

```
          ┌────────────────────────────────────────┐
          │        Monitoring Server (AWS EC2)     │
          │  Prometheus + Grafana + Alertmanager   │
          │                                        │
          │  Scrape:                               │
          │   └── /metrics from EIG/IPSec server   │
          └────────────────┬───────────────────────┘
                           │
                 Prometheus scrape (Node Exporter)
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
 ┌──────────────┐                      ┌──────────────┐
 │ EIG Server 1 │                      │ EIG Server 2 │
 │  LibreSwan    │                      │ LibreSwan    │
 │  /etc/ipsec.d │                      │ /etc/ipsec.d │
 │  status →     │                      │ status →     │
 │  node_exporter│                      │ node_exporter│
 └──────┬────────┘                      └──────┬────────┘
        │                                       │
        │ Prometheus scrapes custom metrics     │
        │ (ipsec_tunnel_up, ipsec_tunnel_status)│
        │                                       │
        └───────────────► Alerts → Teams Bot ◄──┘
```

---

## 3. Prerequisites

| Component | Requirement |
|------------|-------------|
| OS | Red Hat / CentOS 8 or 9 |
| IPSec | LibreSwan installed and configured |
| Node Exporter | Installed with `--collector.textfile.directory` enabled |
| Prometheus | Already configured |
| Alertmanager | Configured |
| Grafana | Integrated |
| Teams Webhook | Configured via prom2teams bridge |

---

## 4. Create IPSec Tunnel Status Exporter

### File: `/opt/ipsec_status_exporter/ipsec_tunnel_status.py`
```python
#!/usr/bin/env python3
import subprocess
import os
import re
from datetime import datetime

TEXTFILE_DIR = "/var/lib/node_exporter/textfile_collector"
TMP_FILE = os.path.join(TEXTFILE_DIR, "ipsec_tunnel_status.prom.tmp")
OUT_FILE = os.path.join(TEXTFILE_DIR, "ipsec_tunnel_status.prom")

cmd = ["ipsec", "status"]
try:
    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
except subprocess.CalledProcessError as e:
    output = e.output

tunnels = {}
for line in output.splitlines():
    match = re.search(r'#\d+: "([^"]+)" state (\w+)', line)
    if match:
        name = match.group(1)
        state = match.group(2).lower()
        tunnels[name] = 1 if "established" in state else 0

with open(TMP_FILE, "w") as f:
    f.write("# HELP ipsec_tunnel_up 1 if IPsec tunnel is established, else 0\n")
    f.write("# TYPE ipsec_tunnel_up gauge\n")
    now = int(datetime.utcnow().timestamp())
    for name, status in tunnels.items():
        f.write(f'ipsec_tunnel_up{{tunnel="{name}"}} {status}\n')
    f.write(f'ipsec_status_last_scrape {now}\n')

os.replace(TMP_FILE, OUT_FILE)
```

### Make Executable
```bash
chmod +x /opt/ipsec_status_exporter/ipsec_tunnel_status.py
```

---

## 5. Schedule via Cron (Every 1 Minute)

File: `/etc/cron.d/ipsec_status_exporter`
```
* * * * * root /opt/ipsec_status_exporter/ipsec_tunnel_status.py
```

### Verify Output
```bash
cat /var/lib/node_exporter/textfile_collector/ipsec_tunnel_status.prom
```
Example output:
```
# HELP ipsec_tunnel_up 1 if IPsec tunnel is established, else 0
# TYPE ipsec_tunnel_up gauge
ipsec_tunnel_up{tunnel="partnerA"} 1
ipsec_tunnel_up{tunnel="partnerB"} 0
ipsec_status_last_scrape 1738756123
```

---

## 6. Prometheus Configuration

### Existing Node Exporter Scrape
Ensure Prometheus scrapes your EIG/IPSec nodes:

```yaml
scrape_configs:
  - job_name: 'node-exporter'
    static_configs:
      - targets:
        - 10.10.1.5:9100  # EIG/IPSec Server 1
        - 10.10.1.6:9100  # EIG/IPSec Server 2
```

> The textfile metrics are exposed automatically via Node Exporter.

---

## 7. Prometheus Alert Rules

File: `/etc/prometheus/rules/ipsec_tunnel_alerts.yml`
```yaml
groups:
- name: IPSecTunnelAlerts
  rules:
  - alert: IPsecTunnelDown
    expr: ipsec_tunnel_up == 0
    for: 3m
    labels:
      severity: critical
      team: network
    annotations:
      summary: "IPSec tunnel down: {{ $labels.tunnel }}"
      description: "Tunnel {{ $labels.tunnel }} has been DOWN for 3 minutes. Verify LibreSwan connection or partner endpoint."

  - alert: IPsecNoData
    expr: time() - ipsec_status_last_scrape > 180
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "No recent IPSec metrics"
      description: "ipsec_tunnel_status script may not be running or node exporter collector is stale."
```

Reload Prometheus:
```bash
sudo systemctl reload prometheus
```

---

## 8. Alertmanager Integration (Teams Bot)

Alerts will automatically flow to your existing **Prod Connectivity Bot** (via prom2teams).

Optional route customization:
```yaml
route:
  receiver: teams-prod
  routes:
    - match:
        alertname: IPsecTunnelDown
      receiver: teams-prod
```

---

## 9. Grafana Dashboard

| Panel | PromQL Query | Description |
|--------|---------------|-------------|
| Tunnel Status | `ipsec_tunnel_up` | 1 = Up, 0 = Down |
| Tunnel Count | `sum(ipsec_tunnel_up)` | Total active tunnels |
| Down Tunnel List | `ipsec_tunnel_up == 0` | Show failing tunnels |
| Last Update | `time() - ipsec_status_last_scrape` | Shows metric freshness |

Color thresholds:  
- **Green:** `1` (Up)  
- **Red:** `0` (Down)  
- **Yellow:** if data >3 min old

---

## 10. Testing

### Simulate Tunnel Down
```bash
sudo ipsec down partnerA
```
Wait 3–5 minutes → alert appears in Teams.

### Simulate Tunnel Up
```bash
sudo ipsec up partnerA
```
Alert clears automatically.

---

## 11. Maintenance

| Task | Command |
|------|----------|
| Run test manually | `python3 /opt/ipsec_status_exporter/ipsec_tunnel_status.py` |
| View metrics | `cat /var/lib/node_exporter/textfile_collector/ipsec_tunnel_status.prom` |
| Cron logs | `grep CRON /var/log/cron` |
| Restart Node Exporter | `systemctl restart node_exporter` |
| Reload Prometheus | `systemctl reload prometheus` |

---

**Author:** Vishwa  
**Purpose:** Monitor LibreSwan IPSec tunnel status for multiple partners and send Teams alerts (Prod Connectivity Bot).