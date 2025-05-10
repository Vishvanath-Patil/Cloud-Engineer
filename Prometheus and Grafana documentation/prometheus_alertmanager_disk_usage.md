
# Prometheus Alertmanager Configuration for Disk Usage Alert

## Step 3: Alert Rule in Prometheus for Disk Usage

Create a file `disk_alert.yml` and reference it in your Prometheus config:

```yaml
groups:
  - name: disk_alerts
    rules:
      - alert: DiskUsageHigh
        expr: (node_filesystem_avail_bytes{mountpoint="/",fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{mountpoint="/",fstype!~"tmpfs|overlay"}) < 0.10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk usage above 90% on {{ $labels.instance }}"
          description: "Disk usage is above 90% ({{ $value | humanizePercentage }}) on {{ $labels.instance }}"
```

In `prometheus.yml`, link the rule file and Alertmanager:

```yaml
rule_files:
  - "disk_alert.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets: ["localhost:9093"]
```

## Step 4: Configure Alertmanager to Send Email

Create `alertmanager.yml` with the following content:

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'your-email@gmail.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'
  smtp_require_tls: true

route:
  receiver: 'email-alert'
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 30m  # Resend every 30 minutes until resolved

receivers:
  - name: 'email-alert'
    email_configs:
      - to: 'recipient@example.com'
        send_resolved: true
```

> 💡 **Use Gmail App Passwords** if using a Gmail account. Enable "Less secure apps" if needed or use OAuth if required.

## Step 5: Start All Services

Ensure the following services are running:

- `node_exporter` on all target machines
- `prometheus` with updated config
- `alertmanager` with email setup

## ✅ Testing Disk Usage Alert

To simulate a full disk for testing:

```bash
fallocate -l 9G /bigfile  # Fill up disk to test alert
```

To clean up:

```bash
rm /bigfile
```
