## 🔔 Alertmanager Setup Guide (From Scratch)

This guide walks you through setting up Prometheus Alertmanager from scratch, including configuration for CPU usage alert if it's above 70% for more than 3 minutes.

---

## 📦 Step 1: Download and Install Alertmanager

### 🔴 RedHat/CentOS & 🟢 Ubuntu

```bash
wget https://github.com/prometheus/alertmanager/releases/download/v0.27.0/alertmanager-0.27.0.linux-amd64.tar.gz
tar -xvf alertmanager-0.27.0.linux-amd64.tar.gz
cd alertmanager-0.27.0.linux-amd64
sudo mv alertmanager amtool /usr/local/bin/
sudo mkdir /etc/alertmanager /var/lib/alertmanager
touch /etc/alertmanager/alertmanager.yml
```

---

## 🛠️ Step 2: Configure Alertmanager

Edit `/etc/alertmanager/alertmanager.yml`

```yaml
global:
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alerts@example.com'
  smtp_auth_username: 'alerts@example.com'
  smtp_auth_password: 'your-email-password'

route:
  receiver: 'email-alerts'

receivers:
  - name: 'email-alerts'
    email_configs:
      - to: 'your-destination@example.com'
```

---

## ⚙️ Step 3: Create Alertmanager Systemd Service

```bash
sudo nano /etc/systemd/system/alertmanager.service
```

Add the following:

```ini
[Unit]
Description=Prometheus Alertmanager
Wants=network-online.target
After=network-online.target

[Service]
User=root
ExecStart=/usr/local/bin/alertmanager \
  --config.file=/etc/alertmanager/alertmanager.yml \
  --storage.path=/var/lib/alertmanager

[Install]
WantedBy=multi-user.target
```

Enable and start Alertmanager:

```bash
sudo systemctl daemon-reexec
sudo systemctl enable alertmanager
sudo systemctl start alertmanager
sudo systemctl status alertmanager
```

Access UI:

```
http://<server-ip>:9093
```

---

## 🔄 Step 4: Configure Prometheus to Use Alertmanager

Edit `/etc/prometheus/prometheus.yml`:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - localhost:9093
```

---

## 📏 Step 5: Create Alert Rule for CPU >70% for 3 Minutes

Create a new file `/etc/prometheus/alert.rules.yml`

```yaml
groups:
  - name: node_exporter_alerts
    rules:
      - alert: HighCPUUsage
        expr: avg_over_time(rate(node_cpu_seconds_total{mode="user"}[1m])[3m:]) * 100 > 70
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is above 70% for 3 minutes on {{ $labels.instance }}"
```

Edit `prometheus.yml` to include the rule file:

```yaml
rule_files:
  - /etc/prometheus/alert.rules.yml
```

Reload Prometheus:

```bash
curl -X POST http://localhost:9090/-/reload
```

---

## ✅ Validation

* Access Prometheus Alerts:

  ```
  http://<your-server-ip>:9090/alerts
  ```
* Access Alertmanager UI:

  ```
  http://<your-server-ip>:9093
  ```

---

## 📬 Test Email Delivery

Temporarily lower the alert threshold to test email delivery and ensure SMTP setup is correct.

---

