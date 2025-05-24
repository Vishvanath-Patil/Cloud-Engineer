# Grafana Alert Setup Guide: CPU Usage > 70%

This guide walks through the complete process of setting up an alert in Grafana when CPU usage exceeds 70%. It includes panel creation, alert rules, contact point configuration, and notification policy setup.

---

## 📌 Prerequisites

- Grafana (v8 or later) installed and accessible
- Prometheus configured as a data source in Grafana
- Node Exporter installed on target servers (for Linux metrics)
- SMTP credentials for email notification setup

---

## 📊 Step 1: Create CPU Usage Panel

1. Go to your Grafana dashboard.
2. Click **+** → **Create** → **Dashboard**.
3. Click **Add new panel**.
4. In the query editor, select **Prometheus** as the data source.
5. Enter the following PromQL query:
   ```promql
   100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
   ```
6. Set the visualization to **Time series**.
7. Click **Apply** and save the panel.

---

## 🚨 Step 2: Create an Alert Rule

1. In the panel, click the **Alert** tab.
2. Click **Create alert rule**.
3. Name the rule: `CPU_Usage_Above_70`.
4. Set **Evaluate every** to `1m` and **For** to `5m`.
5. In the condition, set:
   - **Query (A)**: Use the above PromQL query.
   - **Condition**: IS ABOVE `70`
6. Under **Alert Details**, add a message (optional):
   ```text
   CPU usage exceeded 70% on { $labels.instance }. Current: { $values.A }
   ```
7. Click **Save**.

---

## 📬 Step 3: Configure Contact Point (Email)

1. Go to **Alerting** → **Contact points** → **New contact point**.
2. Name it: `Email_Alerts`.
3. Select **Email** as the type.
4. Fill in the fields:
   - **Addresses**: e.g., `admin@example.com`
   - **Single Email**: Enabled
5. Click **Save contact point**.

To configure SMTP for the first time:

- Go to **Administration** → **Settings** → **Email** (or edit `grafana.ini`):
```ini
[smtp]
enabled = true
host = smtp.example.com:587
user = your_user@example.com
password = your_password
from_address = grafana@example.com
from_name = Grafana Alerts
```
- Restart Grafana after editing the config file.

---

## 🧭 Step 4: Set Notification Policy

1. Go to **Alerting** → **Notification policies**.
2. Click **New policy**.
3. Match **All conditions** or specify label matchers (e.g., `alertname="CPU_Usage_Above_70"`).
4. Set **Contact point** to `Email_Alerts`.
5. Click **Save policy**.

---

## 🧪 Step 5: Test the Alert

1. Simulate high CPU load on a test server.
2. Wait 5 minutes (if "For" duration is set to 5m).
3. Check email inbox for alert.
4. Optionally check the alert rule under **Alerting** → **Alert rules**.

---

## 🛠 Troubleshooting

- **No email received**: Check SMTP config and contact point settings.
- **Query returns no data**: Verify Prometheus target status and query.
- **Alert not firing**: Check evaluation interval and “For” duration.

---

## 📎 References

- [Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/)
- [Prometheus Node Exporter](https://github.com/prometheus/node_exporter)
- [Grafana Email Setup](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/#smtp)

---

## 🖊 Author

Vishwa - May 24, 2025
