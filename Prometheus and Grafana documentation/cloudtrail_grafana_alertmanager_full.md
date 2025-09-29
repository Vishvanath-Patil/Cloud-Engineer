# AWS CloudTrail Logs → Grafana → Prometheus → Alertmanager
**Complete step-by-step guide (ready to upload to repository)**

> Goal: Ingest AWS CloudTrail events into CloudWatch Logs, convert important log patterns to metrics, export those metrics into Prometheus, and use Alertmanager to notify on suspicious events. Also visualize raw logs and metrics in Grafana.

---
## Table of Contents
1. Overview & architecture
2. Prerequisites
3. Required IAM policies & least-privilege examples
4. Configure CloudTrail to send logs to CloudWatch Logs (console + CLI)
5. Create CloudWatch Log Group and retention
6. Create CloudWatch Metric Filters (examples + CLI)
7. Export CloudWatch metrics to Prometheus
   - cloudwatch_exporter (config + run examples)
   - alternative: YACE notes
8. Prometheus configuration (scrape + rule files)
9. Alertmanager configuration (receivers + routing + templates)
10. Grafana setup (CloudWatch + Prometheus data sources)
11. Visualizing logs in Grafana (Logs Insights queries & panels)
12. Dashboard & panel examples (Prometheus queries + panels)
13. Testing the full pipeline (how to generate events & validate)
14. Troubleshooting checklist
15. Security & operational notes
16. Alternatives and tradeoffs
17. Appendix: copy-paste configs and CLI commands

---

## 1. Overview & architecture

We will implement this flow:

```
CloudTrail --> CloudWatch Logs (raw events)
           --> CloudWatch Metric Filters (match patterns) --> CloudWatch Metrics (namespace: CloudTrailMetrics)
CloudWatch Metrics --(cloudwatch_exporter/YACE)--> Prometheus --> Alertmanager --> Notification (email/Slack/webhook)
Grafana --(CloudWatch)--> visualize raw logs and use CloudWatch Logs Insights queries
Grafana --(Prometheus)--> visualize exported metrics and alert status
```

Why both logs + metrics?
- **Raw logs** for forensic and investigation (accessible via CloudWatch Logs Insights inside Grafana).
- **Metrics** for reliable alerting (Prometheus and Alertmanager work best with numeric time-series metrics).

---

## 2. Prerequisites

- AWS account with permissions to create CloudTrail, CloudWatch Log Groups, metric filters, IAM roles/policies.
- CloudTrail service enabled in the target AWS account(s). Multi-region trail recommended for account-wide coverage.
- Grafana, Prometheus and Alertmanager running (we assume these are already up). If they run in EC2 or k8s, prefer using an IAM role/IRSA rather than long-lived keys.
- Network path from Prometheus/cloudwatch_exporter to the internet or appropriate VPC endpoints to reach CloudWatch (if running inside VPC without NAT, create VPC endpoints for CloudWatch/STS).
- Optional: Docker for running cloudwatch_exporter, or a k8s cluster for deploying exporter as a pod.
- AWS CLI configured locally for management and testing.
- Basic knowledge of Prometheus alerting rules and Alertmanager routing.

---

## 3. Required IAM policies & least-privilege examples

**A. Trust & role for CloudTrail to publish logs to CloudWatch Logs**  
CloudTrail needs a role allowing it to write into CloudWatch Logs. The AWS Console can create it automatically, but here is an example trust and policy you can use if creating manually.

**Trust policy (cloudtrail-logs-role-trust.json):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "cloudtrail.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Permissions policy (cloudtrail-logs-role-policy.json):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:CreateLogGroup",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

**B. Minimal policy for cloudwatch_exporter / YACE to read CloudWatch metrics**  
Attach this to the IAM role/user used by the exporter:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudWatchReadMetrics",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricData",
        "cloudwatch:ListMetrics",
        "cloudwatch:GetMetricStatistics"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogsDescribe",
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": "*"
    },
    {
      "Sid": "STSGetCaller",
      "Effect": "Allow",
      "Action": [
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

**C. Minimal policy for Grafana CloudWatch datasource (read-only)**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricData",
        "cloudwatch:ListMetrics",
        "logs:DescribeLogGroups",
        "logs:GetLogEvents",
        "logs:FilterLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

> Note: Use `Resource` restrictions where possible (e.g., limit to specific log group ARNs) for better security. Prefer IAM roles (EC2 instance profile or Kubernetes IRSA) over embedding access keys in config files.

---

## 4. Configure CloudTrail to send logs to CloudWatch Logs

### Console steps (recommended for first time)
1. Open **AWS CloudTrail** console.
2. Choose **Trails** → **Create trail** (or select existing trail).
3. Set **Apply trail to all regions** (recommended) if you want cross-region visibility.
4. Under **Storage location**, skip S3-only; scroll to **CloudWatch Logs** section.
5. Enable **Send to CloudWatch Logs**, pick/create a **Log group** (example: `/aws/cloudtrail/logs`).
6. If prompted, allow CloudTrail to create an IAM role for CloudWatch Logs delivery (simpler). Otherwise, provide the role ARN created from section 3A.
7. Save the trail. CloudTrail will start sending events to CloudWatch Logs (typical delay ≈ few minutes).

### CLI (example creating a trail that delivers to CloudWatch Logs)
**Prerequisite:** you already created a role with trust policy and attached the permissions from section 3A.
```bash
aws cloudtrail create-trail \
  --name "all-region-trail" \
  --s3-bucket-name "my-cloudtrail-bucket-12345" \
  --is-multi-region-trail \
  --include-global-service-events

aws cloudtrail put-event-selectors \
  --trail-name "all-region-trail" \
  --event-selectors '[{"ReadWriteType":"All","IncludeManagementEvents":true,"DataResources":[{"Type":"AWS::S3::Object","Values":["arn:aws:s3:::"]}] }]'
```

To configure CloudWatch Logs integration (attach log group & role):
```bash
aws cloudtrail update-trail \
  --name "all-region-trail" \
  --cloud-watch-logs-log-group-arn arn:aws:logs:ap-south-1:123456789012:log-group:/aws/cloudtrail/logs \
  --cloud-watch-logs-role-arn arn:aws:iam::123456789012:role/CloudTrail_CloudWatchLogs_Role
```

> Replace ARNs, account ID and region accordingly.

---

## 5. Create CloudWatch Log Group and set retention (optional via console/CLI)

**CLI example**:
```bash
aws logs create-log-group --log-group-name /aws/cloudtrail/logs
aws logs put-retention-policy --log-group-name /aws/cloudtrail/logs --retention-in-days 90
```

Retention helps manage cost. Choose retention according to compliance needs (e.g., 90/180/365 days).

---

## 6. Create CloudWatch Metric Filters (convert logs -> metrics)

We create metric filters on the CloudTrail log group to match suspicious patterns and increment a metric. Here are common examples.

### A. AccessDenied events
**Pattern (JSON filter):**
```
{ $.errorCode = "AccessDenied" }
```

**Create via CLI:**
```bash
aws logs put-metric-filter \
  --log-group-name /aws/cloudtrail/logs \
  --filter-name AccessDeniedFilter \
  --filter-pattern '{ $.errorCode = "AccessDenied" }' \
  --metric-transformations metricName=AccessDeniedCount,metricNamespace=CloudTrailMetrics,metricValue=1
```

### B. Failed ConsoleLogin attempts
CloudTrail `ConsoleLogin` events include `additionalEventData` and `errorMessage`. A simple filter to capture failed console logins:

**Pattern:**
```
{ ($.eventName = "ConsoleLogin") && ($.errorMessage = "Failed authentication") }
```

**CLI create:**
```bash
aws logs put-metric-filter \
  --log-group-name /aws/cloudtrail/logs \
  --filter-name ConsoleLoginFailedFilter \
  --filter-pattern '{ ($.eventName = "ConsoleLogin") && ($.errorMessage = "Failed authentication") }' \
  --metric-transformations metricName=ConsoleLoginFailures,metricNamespace=CloudTrailMetrics,metricValue=1
```

### C. API calls from suspicious IP (example pattern)
If CloudTrail stores sourceIPAddress and you have a list of suspicious IPs, you can match:
```
{ $.sourceIPAddress = "1.2.3.4" }
```
or use pattern with wildcard matching on IP ranges. Test patterns using CloudWatch Logs console "Test pattern" before saving.

> After creating metric filters, metrics will appear in CloudWatch Metrics under namespace `CloudTrailMetrics`. There may be a delay (a few minutes) before metrics show up.

---

## 7. Export CloudWatch metrics to Prometheus

Prometheus cannot natively scrape CloudWatch, so we run an exporter. Two common choices:
- **prometheus/cloudwatch-exporter** (Java-based, popular)
- **YACE (Yet Another CloudWatch Exporter)** (Go-based; supports dynamic discovery and AWS tags)

This guide includes a full example for `cloudwatch_exporter` and notes on YACE.

### 7A. cloudwatch_exporter (recommended simple setup)

**cw-config.yml** (example):
```yaml
region: ap-south-1
metrics:
  - aws_namespace: "CloudTrailMetrics"
    aws_metric_name: "AccessDeniedCount"
    aws_dimensions: []
    aws_statistics: [Sum]
    period_seconds: 60
    delay_seconds: 300

  - aws_namespace: "CloudTrailMetrics"
    aws_metric_name: "ConsoleLoginFailures"
    aws_dimensions: []
    aws_statistics: [Sum]
    period_seconds: 60
    delay_seconds: 300
```
**Run via Docker (example using env credentials)**:
```bash
docker run -d --name cloudwatch-exporter \
  -p 9106:9106 \
  -v $(pwd)/cw-config.yml:/config/config.yml:ro \
  -e AWS_ACCESS_KEY_ID=AKIAEXAMPLEKEY \
  -e AWS_SECRET_ACCESS_KEY=EXAMPLESECRET \
  prom/cloudwatch-exporter:latest \
  --config.file=/config/config.yml
```
**Run using instance role (no keys)**: If exporter runs on EC2 with IAM role, unset `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`. The exporter will pick up credentials from the instance metadata.
**Note on `delay_seconds`**: CloudWatch metrics often have ingestion latency; configure delay per your needs to avoid missing recent points.

**Check exporter metrics**:
Visit `http://<exporter-host>:9106/metrics` and look for exported metric names. Example metric name pattern exposed by exporter might look like:
```
aws_cloudwatch_CloudTrailMetrics_AccessDeniedCount_sum{...} <value>
```
> Use the `/metrics` output to identify the exact metric name and labels to use in Prometheus rules and Grafana panels.

### 7B. YACE (Yet Another CloudWatch Exporter) — when you want dynamic discovery
YACE supports dynamic discovery of AWS resources and can be useful if you want to pull many metrics across accounts/regions. See YACE docs for config examples. If you opt for YACE, the rest of the pipeline (Prometheus scrape, alert rules) is similar.

---

## 8. Prometheus configuration

### Scrape cloudwatch_exporter
Add to `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'cloudwatch_exporter'
    static_configs:
      - targets: ['<exporter-host>:9106']    # change exporter-host
```
Reload Prometheus after updating config.

### Alerting rules (example)
Create `cloudtrail_alerts.yml`:

```yaml
groups:
- name: cloudtrail.rules
  rules:
  - alert: AccessDeniedEventsDetected
    # Replace the metric name below with the exact metric printed by the exporter /metrics endpoint
    expr: sum(rate(aws_cloudwatch_CloudTrailMetrics_AccessDeniedCount_sum[5m])) > 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "AccessDenied events detected in CloudTrail"
      description: "There have been {{ $value }} AccessDenied events in the last 5 minutes."
  - alert: MultipleConsoleLoginFailures
    expr: sum(rate(aws_cloudwatch_CloudTrailMetrics_ConsoleLoginFailures_sum[5m])) > 5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Multiple failed console login attempts"
      description: "There have been {{ $value }} failed console logins in the last 5 minutes."
```

Add the rule file to `prometheus.yml`:
```yaml
rule_files:
  - "cloudtrail_alerts.yml"
```

Reload Prometheus and verify under `http://<prometheus-host>:9090/rules` that rules are loaded and either `pending` or `inactive`.

---

## 9. Alertmanager configuration

Create `alertmanager.yml` sample with email and Slack receivers:

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname','severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 3h
  receiver: 'email-team'

receivers:
  - name: 'email-team'
    email_configs:
      - to: 'oncall@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'alertmanager@example.com'
        auth_password: 'EMAIL_PASSWORD'
  - name: 'slack-channel'
    slack_configs:
      - channel: '#security-alerts'
        api_url: 'https://hooks.slack.com/services/XXXXXXXX/XXXXXXXX/XXXXXXXX'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname']
```

**Run Alertmanager (docker example):**
```bash
docker run -d --name alertmanager -p 9093:9093 \
  -v $(pwd)/alertmanager.yml:/etc/alertmanager/alertmanager.yml \
  prom/alertmanager
```

**Verify:** open `http://<alertmanager-host>:9093` and check the "Alerts" and "Status" pages to ensure configuration loaded.

---

## 10. Grafana setup

### Add CloudWatch data source (UI steps)
1. Grafana → Configuration → Data Sources → Add data source → Select **CloudWatch**.
2. Auth: choose one of:
   - **Default** (use environment credentials/EC2 IAM role), or
   - **Access & secret key** (supply values), or
   - **Assume role** (if Grafana must assume a cross-account role — provide role ARN).
3. Specify default region (e.g., `ap-south-1`), click **Save & Test**.

### Provisioning CloudWatch data source (optional)
If you manage Grafana via provisioning, add YAML:
```yaml
apiVersion: 1
datasources:
- name: CloudWatch
  type: cloudwatch
  access: proxy
  jsonData:
    authType: keys
    defaultRegion: ap-south-1
  secureJsonData:
    accessKey: "<AWS_ACCESS_KEY_ID>"
    secretKey: "<AWS_SECRET_ACCESS_KEY>"
```

### Add Prometheus data source (UI / provisioning)
- UI: Configuration → Data Sources → Add → Prometheus → set URL `http://<prometheus-host>:9090` → Save & Test.
- Provisioning YAML (optional):
```yaml
apiVersion: 1
datasources:
- name: Prometheus
  type: prometheus
  access: proxy
  url: http://<prometheus-host>:9090
```

---

## 11. Visualizing logs in Grafana (CloudWatch Logs Insights)

In Grafana **Explore**:
1. Select **CloudWatch** data source.
2. Choose **Logs** mode (CloudWatch Logs Insights).
3. Select log group `/aws/cloudtrail/logs` and use a Logs Insights query.

**Examples**

- AccessDenied events:
```sql
fields @timestamp, @message, eventName, userIdentity.arn, sourceIPAddress, errorCode, errorMessage
| filter errorCode = "AccessDenied"
| sort @timestamp desc
| limit 50
```

- Failed Console Login attempts:
```sql
fields @timestamp, eventName, userIdentity.arn, sourceIPAddress, errorMessage
| filter eventName = "ConsoleLogin" and errorMessage = "Failed authentication"
| sort @timestamp desc
| limit 50
```

Use these queries as panels (Logs panel) in dashboards for SOC visibility. Grafana will render log lines and allow filtering and linking to CloudWatch console.

---

## 12. Dashboard & panel examples (Prometheus metrics)

**Panel 1 — AccessDenied events per minute** (Prometheus query):
```promql
sum(rate(aws_cloudwatch_CloudTrailMetrics_AccessDeniedCount_sum[1m]))
```
**Panel 2 — Console login failures (rolling 5m)**:
```promql
sum(rate(aws_cloudwatch_CloudTrailMetrics_ConsoleLoginFailures_sum[5m]))
```
**Panel 3 — Alerts (Alertmanager status)**: Use Grafana Alertmanager data source or a table panel fed by Prometheus alert count metrics. Alternatively use the Alertmanager API as a datasource for current fired alerts.

> Replace metric names above with the exact metric names returned by your exporter `/metrics` endpoint if they differ.

---

## 13. Testing the full pipeline

1. **Generate test event**: Use a test IAM user with no S3 permissions and run `aws s3 ls`. That should produce an `AccessDenied` CloudTrail event:
```bash
aws s3 ls --profile test-no-s3
```
2. **Verify CloudWatch Logs**: Console → CloudWatch → Log groups → `/aws/cloudtrail/logs` → run Logs Insights query for AccessDenied pattern, or search for the timestamp.
3. **Verify metric filter**: In CloudWatch console, select the log group → Metric filters → Test pattern → ensure sample event matches and metric increments.
4. **Verify exporter metrics**: `curl http://<exporter-host>:9106/metrics` and search for `AccessDeniedCount` metrics exposed.
5. **Verify Prometheus**: `http://<prometheus-host>:9090/targets` → exporter target should be UP. Go to `http://<prometheus-host>:9090/graph` and run the PromQL used in dashboard.
6. **Verify alert**: Force rule to fire by adjusting rule threshold to a low value or generate more events; check Prometheus `Alerts` page; Prometheus should send alert to Alertmanager; check Alertmanager UI and receiver (email/Slack) for notification.

---

## 14. Troubleshooting checklist

- **No logs** in CloudWatch? → Ensure CloudTrail trail has CloudWatch Logs enabled and the role ARN is correct.
- **Metric filters not matching** → Use CloudWatch Logs "Test pattern" with sample event; refine filter pattern JSON path.
- **No metrics in exporter** → Check IAM permissions, region, and that exporter config lists correct namespace and metric name; check `delay_seconds` (avoid capturing very recent points).
- **Prometheus target DOWN** → Check exporter process, firewall/security group, and scrape config host:port.
- **Alert not firing** → Verify Prometheus rule expression and the metric name; use the Prometheus graph to inspect metric values.
- **Notification not received** → Check Alertmanager logs, config, and receiver credentials (SMTP/Slack webhook).

---

## 15. Security & operational notes

- **Avoid storing AWS access keys** in repo. Use IAM roles/IRSA or environment secrets management.
- **Lock down IAM policies** to specific resources (log group ARNs) where possible instead of `Resource: "*"`. Rotate keys frequently if used.
- **CloudWatch costs**: metric filters and Logs Insights queries can incur costs; set an appropriate log retention policy.
- **Alert noise**: set sensible thresholds and `for:` durations to prevent noisy alerts. Consider rate-limiting or grouping in Alertmanager to reduce duplicate notifications.
- **Cross-account**: for central monitoring across multiple AWS accounts, use cross-account roles and assume-role flows for exporter or run exporter in each account with metrics aggregated in Prometheus.

---

## 16. Alternatives & tradeoffs

- **CloudWatch Alarms + SNS**: Use CloudWatch metrics & alarms directly with SNS for notifications (no Prometheus/Alertmanager dependency). Simpler, AWS-native, but less flexible if you already use Prometheus/Alertmanager.
- **Loki**: Instead of storing logs in CloudWatch, forward CloudTrail to Loki for cheaper long-term storage and integrated Grafana log search, but requires building a log ingestion pipeline (S3 -> Lambda -> Loki or Fluentd).
- **S3 + Athena**: For long-term audit and complex queries, archive CloudTrail to S3 and run queries in Athena. Not suitable for real-time alerting but useful for forensic historical analysis.

---

## 17. Appendix — Copy-paste configs & CLI commands

**Create log group & retention**
```bash
aws logs create-log-group --log-group-name /aws/cloudtrail/logs
aws logs put-retention-policy --log-group-name /aws/cloudtrail/logs --retention-in-days 90
```

**Create metric filter — AccessDenied**
```bash
aws logs put-metric-filter \
  --log-group-name /aws/cloudtrail/logs \
  --filter-name AccessDeniedFilter \
  --filter-pattern '{ $.errorCode = "AccessDenied" }' \
  --metric-transformations metricName=AccessDeniedCount,metricNamespace=CloudTrailMetrics,metricValue=1
```

**cloudwatch_exporter config sample (cw-config.yml)**
```yaml
region: ap-south-1
metrics:
  - aws_namespace: "CloudTrailMetrics"
    aws_metric_name: "AccessDeniedCount"
    aws_dimensions: []
    aws_statistics: [Sum]
    period_seconds: 60
    delay_seconds: 300
  - aws_namespace: "CloudTrailMetrics"
    aws_metric_name: "ConsoleLoginFailures"
    aws_dimensions: []
    aws_statistics: [Sum]
    period_seconds: 60
    delay_seconds: 300
```

**Docker run cloudwatch_exporter**
```bash
docker run -d --name cloudwatch-exporter \
  -p 9106:9106 \
  -v $(pwd)/cw-config.yml:/config/config.yml:ro \
  -e AWS_ACCESS_KEY_ID=AKIAEXAMPLE \
  -e AWS_SECRET_ACCESS_KEY=EXAMPLESECRET \
  prom/cloudwatch-exporter:latest \
  --config.file=/config/config.yml
```

**Prometheus scrape config snippet**
```yaml
scrape_configs:
  - job_name: 'cloudwatch_exporter'
    static_configs:
      - targets: ['<exporter-host>:9106']
```

**Prometheus alerts example (cloudtrail_alerts.yml)**
```yaml
groups:
- name: cloudtrail.rules
  rules:
  - alert: AccessDeniedEventsDetected
    expr: sum(rate(aws_cloudwatch_CloudTrailMetrics_AccessDeniedCount_sum[5m])) > 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "AccessDenied events detected in CloudTrail"
      description: "There have been {{ $value }} AccessDenied events in the last 5 minutes."
```

**Alertmanager sample (alertmanager.yml)** (same as section 9)
```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname','severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 3h
  receiver: 'email-team'

receivers:
  - name: 'email-team'
    email_configs:
      - to: 'oncall@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'alertmanager@example.com'
        auth_password: 'EMAIL_PASSWORD'
  - name: 'slack-channel'
    slack_configs:
      - channel: '#security-alerts'
        api_url: 'https://hooks.slack.com/services/XXXXXXXX/XXXXXXXX/XXXXXXXX'
```

---
## Final notes
- Replace placeholders (account IDs, ARNs, hostnames, secrets) with your real values before deploying.
- If you want, I can also:
  - Produce Kubernetes manifests (Deployment/Service) for cloudwatch_exporter and Alertmanager.
  - Produce Grafana dashboard JSON for a sample CloudTrail monitoring dashboard.
  - Produce a CloudFormation/Terraform template to provision CloudTrail + Log group + metric filters + IAM resources.

---
*End of document*
