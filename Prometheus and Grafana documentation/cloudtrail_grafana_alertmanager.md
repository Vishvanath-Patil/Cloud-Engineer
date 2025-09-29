# Integrating AWS CloudTrail Logs with Grafana and Alertmanager

This guide explains how to integrate AWS CloudTrail logs as a data source in Grafana and configure alerting using Alertmanager.

---

## 1. Prerequisites

- **AWS Account** with CloudTrail enabled.  
- **IAM Role/User** with permissions to access CloudTrail logs (S3, CloudWatch Logs).  
- **Grafana** installed and running (already set up).  
- **Prometheus** installed and running (already set up).  
- **Alertmanager** configured with Prometheus.  
- Network connectivity between Grafana/Prometheus and AWS services.  
- AWS CLI or SDK installed and configured with credentials.  

---

## 2. Adding AWS CloudTrail Logs as a Data Source in Grafana

Grafana doesn’t support CloudTrail directly, so we integrate via **CloudWatch Logs**.

1. In AWS Console, ensure CloudTrail is configured to send logs to **CloudWatch Logs group**.  
2. In Grafana:
   - Go to **Configuration → Data Sources → Add data source**.  
   - Select **CloudWatch**.  
   - Configure the following:  
     - **Name**: AWS CloudWatch  
     - **Auth Provider**: Access & secret key (or IAM Role if running on EC2).  
     - **Default Region**: Select the AWS region where CloudTrail logs are stored.  
   - Click **Save & Test**.  

---

## 3. Fetching and Visualizing Logs in Grafana

1. Go to **Explore** in Grafana.  
2. Select the **CloudWatch data source**.  
3. Choose the CloudTrail log group (e.g., `/aws/cloudtrail/logs`).  
4. Run queries to filter specific events (e.g., `eventName = ConsoleLogin`).  
5. Build dashboards with panels showing login activity, failed attempts, API calls, etc.  

---

## 4. Configuring Alerts with Alertmanager

Grafana alerts cannot directly trigger Alertmanager, so we use Prometheus as a bridge.

### Step 1: Export CloudTrail Metrics
- Use **CloudWatch Metric Filters** to convert important log patterns into metrics.  
- Example: Create a filter for failed logins and export as a custom CloudWatch metric.  
- Scrape these metrics into Prometheus using **YACE (Yet Another CloudWatch Exporter)**.  

### Step 2: Configure Prometheus Alerts
Add rules in Prometheus (`alerting_rules.yml`):

```yaml
groups:
  - name: cloudtrail-alerts
    rules:
      - alert: MultipleFailedConsoleLogins
        expr: aws_cloudwatch_failed_logins > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Multiple failed login attempts detected"
          description: "CloudTrail detected more than 5 failed login attempts in 5 minutes."
```

### Step 3: Configure Alertmanager
Example `alertmanager.yml`:

```yaml
route:
  receiver: email-alerts

receivers:
  - name: email-alerts
    email_configs:
      - to: "security-team@example.com"
        from: "alertmanager@example.com"
        smarthost: "smtp.example.com:587"
        auth_username: "alertmanager@example.com"
        auth_password: "password"
```

### Step 4: Visualize Alerts in Grafana
- Import Prometheus alerts into Grafana dashboards.  
- Enable **Alerting → Notification channels** in Grafana for visibility.  

---

## ✅ Summary

- Enabled CloudTrail logs in CloudWatch.  
- Added CloudWatch as Grafana data source.  
- Queried and visualized CloudTrail logs in Grafana.  
- Exported metrics and set up Prometheus + Alertmanager for alerting.  

This ensures centralized monitoring and alerting for CloudTrail events in Grafana.
