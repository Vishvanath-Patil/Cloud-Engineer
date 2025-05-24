# Grafana Alert Setup Guide: CPU Usage > 70%

This guide walks through the complete process of setting up an alert in Grafana when CPU usage exceeds 70%. It includes panel creation, alert rules, contact point configuration, notification policy setup, and how to target specific jobs or all targets.

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
5. Enter the following PromQL query to monitor all targets:
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
   - **Condition**: IS ABOVE `70` **Select B as input in the dropdown**
6. Under **Alert Details**, add a message (optional):
   ```text
   CPU usage exceeded 70% on { $labels.instance }. Current: { $values.A }
   ```
7. Click **Save**.

---

## 🎯 Target Specific Jobs or All Targets

### ✅ For All Targets
Use the default query:
```promql
100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

### 🎯 For Specific Job (e.g., web-servers)
If Prometheus has a job like:
```yaml
- job_name: "web-servers"
  static_configs:
    - targets: ["192.168.1.10:9100", "192.168.1.11:9100"]
```

Use this PromQL in alert rule:
```promql
100 - (avg by(instance) (rate(node_cpu_seconds_total{job="web-servers", mode="idle"}[5m])) * 100)
```

Label your alert rule:
```yaml
job = "web-servers"
```

Route using notification policies accordingly.

---

## 📬 Step 3: Configure Contact Point (Email)

1. Go to **Alerting** → **Contact points** → **New contact point**.
2. Name it: `Email_Alerts`.
3. Select **Email** as the type.
4. Fill in the fields:
   - **Addresses**: e.g., `admin@example.com`
   - **Single Email**: Enabled
5. Click **Save contact point**.

To configure SMTP:

- Edit `grafana.ini` or environment variables:
```ini
[smtp]
enabled = true
host = smtp.example.com:587
user = your_user@example.com
password = your_password
from_address = grafana@example.com
from_name = Grafana Alerts
```
- Restart Grafana.

---

## 🧭 Step 4: Set Notification Policy

1. Go to **Alerting** → **Notification policies**.
2. Click **New policy**.
3. Set **Matching labels**:
   ```yaml
   job = "web-servers"
   ```
4. Set **Contact point**: `Email_Alerts`
5. Click **Save policy**.

---

## 🧪 Step 5: Test the Alert

1. Simulate high CPU usage on a target server.
2. Wait for alert evaluation period.
3. Check email inbox for alert.
4. Validate in **Alerting → Alert rules** and **Alerting → Alert instances**.

---

## 🛠 Troubleshooting

- **No email**: Check SMTP and contact point settings.
- **Query shows no data**: Validate Prometheus targets.
- **Alert not triggering**: Check time window and "For" duration.

---

## 📎 References

- [Grafana Alerting Docs](https://grafana.com/docs/grafana/latest/alerting/)
- [Prometheus Node Exporter](https://github.com/prometheus/node_exporter)
- [Grafana Email Setup](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/#smtp)

---

## 🖊 Author

Vishwa - May 24, 2025


---

## 🧠 Memory Usage Alert (Above 80%)

### PromQL Query

```promql
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

### Alert Setup

- **Threshold**: 80%
- **Condition**: IS ABOVE 80
- **For**: 5m
- **Labels** (optional):
  ```yaml
  alertname = "Memory_Usage_Above_80"
  severity = "warning"
  ```
- **Message**:
  ```text
  Memory usage on {{ $labels.instance }} is above 80%. Current: {{ $values.A }}
  ```

---

## 💽 Disk Usage Alert (Above 85%)

### PromQL Query

```promql
(node_filesystem_size_bytes{mountpoint="/",fstype!~"tmpfs|fuse.lxcfs"} - node_filesystem_avail_bytes{mountpoint="/",fstype!~"tmpfs|fuse.lxcfs"}) 
/ node_filesystem_size_bytes{mountpoint="/",fstype!~"tmpfs|fuse.lxcfs"} * 100
```

### Alert Setup

- **Threshold**: 85%
- **Condition**: IS ABOVE 85
- **For**: 5m
- **Labels** (optional):
  ```yaml
  alertname = "Disk_Usage_Above_85"
  severity = "critical"
  ```
- **Message**:
  ```text
  Disk usage on {{ $labels.instance }} is above 85%. Current: {{ $values.A }}
  ```

---

## 🛡 Apply to Specific Job (Example: storage-servers)

Add `job="storage-servers"` in PromQL:
```promql
(1 - (node_memory_MemAvailable_bytes{job="storage-servers"} / node_memory_MemTotal_bytes{job="storage-servers"})) * 100
```

```promql
(node_filesystem_size_bytes{{job="storage-servers",mountpoint="/",fstype!~"tmpfs|fuse.lxcfs"}} - node_filesystem_avail_bytes{{job="storage-servers",mountpoint="/",fstype!~"tmpfs|fuse.lxcfs"}}) 
/ node_filesystem_size_bytes{{job="storage-servers",mountpoint="/",fstype!~"tmpfs|fuse.lxcfs"}} * 100
```

---

## 📬 Notification Routing

Add corresponding label matches in **Notification Policies** to route alerts based on `alertname` or `job` label.

Example:
```yaml
alertname = "Disk_Usage_Above_85"
```

---

## ✅ Summary of Thresholds

| Metric       | Threshold | For Duration | Severity  |
|--------------|-----------|---------------|-----------|
| CPU Usage    | > 70%     | 5m            | warning   |
| Memory Usage | > 80%     | 5m            | warning   |
| Disk Usage   | > 85%     | 5m            | critical  |

