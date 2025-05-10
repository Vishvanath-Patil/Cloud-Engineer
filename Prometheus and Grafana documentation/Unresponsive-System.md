
# Unresponsive System Alert Setup Guide

This guide walks you through the steps of configuring Prometheus and Alertmanager to send continuous email alerts if a system becomes unresponsive, and stop once the issue is resolved.

---

## 📦 Step 1: Define "Unresponsive System" Alert Rule

The system is considered unresponsive if it doesn't respond to the `node_exporter` scrape or another service for more than 5 minutes. Here's how to create an alert rule for that:

1. **Create a new alert rule file** `/etc/prometheus/alert.rules.yml`:

```yaml
groups:
  - name: system_alerts
    rules:
      - alert: UnresponsiveSystem
        expr: absent(node_exporter_up{job="node"}) == 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "System is unresponsive"
          description: "No response from the node_exporter for the last 5 minutes on {{ $labels.instance }}"
```

Explanation:
- `absent(node_exporter_up{job="node"}) == 1`: Checks if the `node_exporter_up` metric is absent, indicating the system is unresponsive.
- `for: 5m`: Ensures that the condition persists for 5 minutes before firing the alert.

2. **Edit `prometheus.yml`** to include the alert rule file:

```yaml
rule_files:
  - /etc/prometheus/alert.rules.yml
```

3. **Reload Prometheus** to apply changes:

```bash
curl -X POST http://localhost:9090/-/reload
```

---

## 📧 Step 2: Configure Alertmanager for Continuous Email Alerts

Modify the Alertmanager configuration to continuously notify you until the alert is resolved.

1. **Edit Alertmanager configuration** `/etc/alertmanager/alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alerts@example.com'
  smtp_auth_username: 'alerts@example.com'
  smtp_auth_password: 'your-email-password'

route:
  receiver: 'email-alerts'
  repeat_interval: 1h   # Repeats the alert every hour until resolved

receivers:
  - name: 'email-alerts'
    email_configs:
      - to: 'your-destination@example.com'
        send_resolved: true  # Sends a resolution notification when the alert is resolved
```

Explanation:
- `repeat_interval: 1h`: Repeats the alert every hour until the system becomes responsive again.
- `send_resolved: true`: Sends an email when the alert is resolved, notifying that the system is now responsive.

---

## ⚙️ Step 3: Create Systemd Service (If Not Done Already)

Ensure that Alertmanager runs on boot and manages the service automatically:

1. **Create the systemd service** `/etc/systemd/system/alertmanager.service`:

```ini
[Unit]
Description=Prometheus Alertmanager
Wants=network-online.target
After=network-online.target

[Service]
User=root
ExecStart=/usr/local/bin/alertmanager   --config.file=/etc/alertmanager/alertmanager.yml   --storage.path=/var/lib/alertmanager

[Install]
WantedBy=multi-user.target
```

2. Enable and start Alertmanager:

```bash
sudo systemctl daemon-reexec
sudo systemctl enable alertmanager
sudo systemctl start alertmanager
sudo systemctl status alertmanager
```

---

## 🧪 Step 4: Test the Alert

1. Temporarily stop `node_exporter` or simulate an unresponsive node.
2. Wait for 5 minutes and check that the alert triggers and you receive an email.
3. Resolve the issue (restart the service or bring the node back online).
4. Check that the resolution email is sent.

---

## 🔄 Final Configuration Recap

- **Prometheus alert rule**: Triggers when a system is unresponsive due to missing `node_exporter` data for 5 minutes.
- **Alertmanager configuration**: Sends recurring email alerts every hour until the alert is resolved.

