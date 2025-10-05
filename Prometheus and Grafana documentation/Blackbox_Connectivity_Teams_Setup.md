# Prometheus Blackbox Exporter + Teams Alert Setup Guide

## 1. Architecture Overview (Draw.io Diagram)

Below is a high-level architecture to visualize how Prometheus, Blackbox Exporter, Alertmanager, and Microsoft Teams Bot communicate.

![Blackbox Architecture](https://raw.githubusercontent.com/vishwa-monitoring/docs/main/diagrams/blackbox_teams_architecture.png)

> *(You can recreate or edit this diagram using [draw.io](https://app.diagrams.net/). Suggested file name: `blackbox_teams_architecture.drawio`)*

### Suggested Diagram Layout (Draw.io Nodes)
```
+-------------------------+        +---------------------+
|     Prometheus Server   |        | Blackbox Exporter   |
|  (Scrapes /probe data)  | <----> | Probes Endpoints    |
|                         |        | via TCP/HTTPS/SSL   |
+-----------+-------------+        +---------+-----------+
            |                                 |
            |                                 |
            v                                 v
     +-------------+                 +---------------------+
     | Alertmanager| ----> MS Teams  |   Prod Connectivity |
     |  (Routes)   | ---> Webhook -->|        Bot          |
     +-------------+                 +---------------------+

           +---------------------------------------------+
           |                 Grafana                     |
           |  (Dashboards for probe_success, SSL expiry)  |
           +---------------------------------------------+
```

---

## 2. Prerequisites
| Component | Requirement |
|------------|-------------|
| Prometheus | Already running |
| Grafana | Already integrated |
| Alertmanager | Configured |
| Server Access | Internet or internal repo access |
| Ports | Outbound: 80, 443 / Inbound: 9115 |
| User | `prometheus` user |
| Teams | Incoming Webhook URL for Teams Bot |

---

## 3. Blackbox Exporter Setup

### Install
```bash
cd /opt
wget https://github.com/prometheus/blackbox_exporter/releases/download/v0.24.0/blackbox_exporter-0.24.0.linux-amd64.tar.gz
tar xzf blackbox_exporter-0.24.0.linux-amd64.tar.gz
sudo mv blackbox_exporter-0.24.0.linux-amd64 /usr/local/blackbox_exporter
sudo ln -s /usr/local/blackbox_exporter/blackbox_exporter /usr/local/bin/blackbox_exporter
```

### Config Directory
```bash
sudo mkdir -p /etc/blackbox_exporter
```

### Configuration (`/etc/blackbox_exporter/blackbox.yml`)
```yaml
modules:
  http_2xx:
    prober: http
    timeout: 10s
    http:
      valid_http_versions: ["HTTP/1.1", "HTTP/2"]
      method: GET
      fail_if_not_ssl: false
      fail_if_ssl: false
      preferred_ip_protocol: "ip4"

  https_tls:
    prober: http
    timeout: 10s
    http:
      method: GET
      fail_if_not_ssl: true
      tls_config:
        insecure_skip_verify: false
      preferred_ip_protocol: "ip4"

  tcp_connect:
    prober: tcp
    timeout: 5s
    tcp:
      preferred_ip_protocol: "ip4"
```

### Systemd Service
`/etc/systemd/system/blackbox_exporter.service`
```ini
[Unit]
Description=Prometheus Blackbox Exporter
After=network.target

[Service]
User=prometheus
ExecStart=/usr/local/bin/blackbox_exporter --config.file=/etc/blackbox_exporter/blackbox.yml
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now blackbox_exporter
sudo systemctl status blackbox_exporter
```

Test:
```bash
curl http://localhost:9115
```

---

## 4. Prometheus Configuration

### Targets File (`/etc/prometheus/blackbox_targets.yml`)
```yaml
- labels:
    group: partners
    module: tcp_connect
  targets:
    - partner1.example.com:443
    - 10.20.30.40:8443

- labels:
    group: partners
    module: https_tls
  targets:
    - https://api.partner2.com
    - https://billing.partner3.com
```

### Scrape Job (in `/etc/prometheus/prometheus.yml`)
```yaml
scrape_configs:
  - job_name: 'blackbox-probe'
    metrics_path: /probe
    file_sd_configs:
      - files: ['/etc/prometheus/blackbox_targets.yml']
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - source_labels: [__meta_file_sd_label_module]
        target_label: __param_module
      - target_label: __address__
        replacement: 127.0.0.1:9115
```

Reload Prometheus:
```bash
sudo systemctl reload prometheus
```

---

## 5. Prometheus Alerts (`/etc/prometheus/rules/blackbox_alerts.yml`)
```yaml
groups:
- name: BlackboxAlerts
  rules:
  - alert: PartnerConnectivityDown
    expr: probe_success{job="blackbox-probe"} == 0
    for: 2m
    labels:
      severity: critical
      team: network
    annotations:
      summary: "Connectivity Down: {{ $labels.instance }}"
      description: "Probe to {{ $labels.instance }} failed for 2 minutes."

  - alert: PartnerHighLatency
    expr: probe_duration_seconds{job="blackbox-probe"} > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High latency: {{ $labels.instance }}"
      description: "Probe duration > 2s. Current = {{ $value }}s"

  - alert: SSLCertificateExpiringSoon
    expr: (probe_ssl_earliest_cert_expiry - time()) < 86400 * 15
    for: 0m
    labels:
      severity: warning
      team: ssl
    annotations:
      summary: "SSL cert expiring soon: {{ $labels.instance }}"
      description: "Certificate will expire within 15 days."
```

Reload rules:
```bash
sudo systemctl reload prometheus
```

---

## 6. Alertmanager → Teams Integration

### Create Teams Webhook
1. Teams → Channel → **Connectors → Incoming Webhook → Configure**.
2. Name it **Prometheus Alerts**.
3. Copy the **Webhook URL** (e.g. `https://outlook.office.com/webhook/...`).

### Install Prom2Teams
```bash
sudo mkdir -p /opt/prom2teams
cd /opt/prom2teams
sudo yum install -y python3 python3-pip
pip3 install prometheus-msteams
```

### Config `/etc/prom2teams/config.yml`
```yaml
connectors:
  - name: prod-connectivity
    url: "https://outlook.office.com/webhook/<YOUR_WEBHOOK_URL>"
    type: webhook
```

### Service `/etc/systemd/system/prom2teams.service`
```ini
[Unit]
Description=Prometheus to Teams bridge
After=network.target

[Service]
ExecStart=/usr/local/bin/prometheus-msteams -c /etc/prom2teams/config.yml
Restart=always
User=prometheus

[Install]
WantedBy=multi-user.target
```

Start and enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now prom2teams
```

### Alertmanager Config (`/etc/alertmanager/alertmanager.yml`)
```yaml
global:
  resolve_timeout: 5m

route:
  receiver: teams-prod
  group_by: ['alertname','instance','severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 3h

receivers:
  - name: teams-prod
    webhook_configs:
      - url: 'http://localhost:2000/prod-connectivity'
```

Restart Alertmanager:
```bash
sudo systemctl restart alertmanager
```

---

## 7. Testing Alerts

### Connectivity Failure
```bash
sudo iptables -A OUTPUT -p tcp --dport 443 -j DROP
```
Wait 2–3 mins → Teams alert appears:
> **[CRITICAL] PartnerConnectivityDown** — partner1.example.com:443

Undo:
```bash
sudo iptables -D OUTPUT -p tcp --dport 443 -j DROP
```

### SSL Expiry Test
Use:
```
https://expired.badssl.com
```
→ Triggers `SSLCertificateExpiringSoon`.

---

## 8. Grafana Dashboard

Import **Grafana Dashboard ID 7587 (Prometheus Blackbox Exporter)** from grafana.com.

Useful queries:
| Metric | Description | Query |
|--------|--------------|-------|
| Connectivity | Up/Down status | `probe_success{job="blackbox-probe"}` |
| Latency | Response time | `probe_duration_seconds{job="blackbox-probe"}` |
| SSL Expiry (days) | Days to expire | `(probe_ssl_earliest_cert_expiry - time()) / 86400` |

---

## 9. Maintenance
| Task | Command |
|------|----------|
| Check exporter logs | `journalctl -u blackbox_exporter -f` |
| Check prom2teams logs | `journalctl -u prom2teams -f` |
| Add new partner | Edit `/etc/prometheus/blackbox_targets.yml` |
| Reload Prometheus | `systemctl reload prometheus` |
| Restart Alertmanager | `systemctl restart alertmanager` |

---

**Author:** Vishwa  
**Purpose:** Monitor partner connectivity & SSL health, and send alerts to Microsoft Teams (Prod Connectivity Bot).
