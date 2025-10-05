# CloudTrail → CloudWatch → Prometheus → Alertmanager → Microsoft Teams

**Ready-to-implement guide** (for environments where Prometheus, Grafana and Alertmanager are already running). Includes Draw.io architecture link and step-by-step copy-paste configs. This version adds a Microsoft Teams notification path (recommended: use an adapter `alertmanager-msteams` for robust formatting).

---

## Table of Contents
1. Overview & architecture
2. Quick prerequisites checklist
3. IAM roles & least-privilege policies
4. CloudTrail → CloudWatch Logs configuration (console + CLI)
5. CloudWatch Log Group, retention and sample events
6. Metric filters (log -> metric) — ready-to-run examples
7. Export CloudWatch metrics to Prometheus (cloudwatch_exporter)
8. Prometheus: scrape + alert rules (copy-paste)
9. Alertmanager: route to Microsoft Teams (adapter + direct webhook options)
10. Grafana: add CloudWatch & Prometheus datasources + panels
11. Testing the full pipeline (end-to-end)
12. Troubleshooting checklist & operational notes
13. Alternatives & extras
14. Appendix: all files and commands to copy-paste

---

## 1. Overview & architecture

**Flow:**
```
CloudTrail --> CloudWatch Logs (raw events)
           --> CloudWatch Metric Filters -> CloudWatch Metrics (CloudTrailMetrics)
CloudWatch Metrics --(cloudwatch_exporter)--> Prometheus --> Alertmanager --> Microsoft Teams (via adapter)
Grafana --(CloudWatch)--> logs insights (forensics)
Grafana --(Prometheus)--> metrics dashboards
```

**Draw.io diagram:**
- Importable draw.io XML: create a new diagram in draw.io and paste the following XML into *File → Import From → Device* (XML attached inside repo or in `/diagrams/cloudtrail_pipeline.drawio.xml`).

(If you prefer a hosted link, upload `cloudtrail_pipeline.drawio.xml` to your repo and open it in draw.io online.)

---

## 2. Quick prerequisites checklist
- AWS account(s) with:
  - CloudTrail enabled (multi-region recommended)
  - Permission to create CloudWatch Log Group, Metric Filters, IAM Roles
- Prometheus, Grafana, Alertmanager already running (we assume Prometheus & Grafana are configured and reachable from your workstation)
- A host to run `cloudwatch_exporter` (EC2, container host, or Kubernetes). The host must be able to reach AWS CloudWatch APIs (internet or VPC endpoints).
- An option to run `alertmanager-msteams` adapter (container or binary) reachable by Alertmanager.
- Microsoft Teams channel with **Incoming Webhook** connector created — note the webhook URL (keeps secret).

---

## 3. IAM roles & least-privilege policies

### A. CloudTrail -> CloudWatch delivery role (CloudTrail must assume)
**Trust policy** (cloudtrail-trust.json):
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect":"Allow",
    "Principal": { "Service": "cloudtrail.amazonaws.com" },
    "Action": "sts:AssumeRole"
  }]
}
```

**Permissions policy** (cloudtrail-cloudwatch-policy.json):
```json
{
  "Version":"2012-10-17",
  "Statement":[{
    "Effect":"Allow",
    "Action":[
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams"
    ],
    "Resource":"arn:aws:logs:*:*:*"
  }]
}
```

### B. Exporter role/user (cloudwatch_exporter) — read-only
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudWatchRead",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricData",
        "cloudwatch:ListMetrics",
        "cloudwatch:GetMetricStatistics"
      ],
      "Resource": "*"
    },
    {
      "Sid": "LogsDescribe",
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": "*"
    },
    {
      "Sid":"STS",
      "Effect":"Allow",
      "Action":["sts:GetCallerIdentity"],
      "Resource":"*"
    }
  ]
}
```

> Use instance profile (EC2 IAM role) or IRSA (EKS) for credentials — do not store long-lived keys in repo.

---

## 4. Configure CloudTrail to send logs to CloudWatch Logs

### Console (quick):
1. AWS Console → CloudTrail → Trails → Create trail (or edit existing).
2. Enable **Apply to all regions**.
3. Under *Management events* choose required events (Read/Write/Both).
4. Under *CloudWatch Logs* → Enable → create/select log group e.g. `/aws/cloudtrail/logs`.
5. Allow CloudTrail to create the IAM role automatically or supply the role ARN from Section 3A.

### CLI (example):
```bash
aws cloudtrail create-trail --name all-region-trail --s3-bucket-name my-cloudtrail-bucket-12345 --is-multi-region-trail --include-global-service-events

# provide CloudWatch log group & role
aws cloudtrail update-trail --name all-region-trail \
  --cloud-watch-logs-log-group-arn arn:aws:logs:ap-south-1:123456789012:log-group:/aws/cloudtrail/logs \
  --cloud-watch-logs-role-arn arn:aws:iam::123456789012:role/CloudTrail_CloudWatchLogs_Role
```

---

## 5. Create CloudWatch Log Group and retention

```bash
aws logs create-log-group --log-group-name /aws/cloudtrail/logs
aws logs put-retention-policy --log-group-name /aws/cloudtrail/logs --retention-in-days 90
```

Choose retention according to compliance & cost.

---

## 6. Metric Filters — convert specific log events into CloudWatch metrics

Create metric filters for events you want alerted on. Examples below are copy-paste.

### A. AccessDenied events
```bash
aws logs put-metric-filter \
  --log-group-name /aws/cloudtrail/logs \
  --filter-name AccessDeniedFilter \
  --filter-pattern '{ $.errorCode = "AccessDenied" }' \
  --metric-transformations metricName=AccessDeniedCount,metricNamespace=CloudTrailMetrics,metricValue=1
```

### B. Failed ConsoleLogin attempts
```bash
aws logs put-metric-filter \
  --log-group-name /aws/cloudtrail/logs \
  --filter-name ConsoleLoginFailedFilter \
  --filter-pattern '{ ($.eventName = "ConsoleLogin") && ($.errorMessage = "Failed authentication") }' \
  --metric-transformations metricName=ConsoleLoginFailures,metricNamespace=CloudTrailMetrics,metricValue=1
```

### C. API calls from specific suspicious IP
```bash
aws logs put-metric-filter \
  --log-group-name /aws/cloudtrail/logs \
  --filter-name SuspiciousIPFilter \
  --filter-pattern '{ $.sourceIPAddress = "1.2.3.4" }' \
  --metric-transformations metricName=SuspiciousIPCalls,metricNamespace=CloudTrailMetrics,metricValue=1
```

**Tip:** Use CloudWatch Logs console *Test pattern* to validate filters against sample events before creating.

---

## 7. Export CloudWatch metrics to Prometheus (cloudwatch_exporter)

We recommend `prom/cloudwatch-exporter`. Run it as a container or Kubernetes deployment.

**cw-config.yml** (place next to exporter):
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

  - aws_namespace: "CloudTrailMetrics"
    aws_metric_name: "SuspiciousIPCalls"
    aws_dimensions: []
    aws_statistics: [Sum]
    period_seconds: 60
    delay_seconds: 300
```

**Docker run (using instance role or env keys):**
```bash
docker run -d --name cloudwatch-exporter \
  -p 9106:9106 \
  -v $(pwd)/cw-config.yml:/config/config.yml:ro \
  -e AWS_REGION=ap-south-1 \
  prom/cloudwatch-exporter:latest \
  --config.file=/config/config.yml
```

If running on EC2 with IAM role, do not pass AWS keys; exporter will use instance profile.

**Verify:** `curl http://<exporter-host>:9106/metrics` and search for metrics exported from `CloudTrailMetrics` namespace.

---

## 8. Prometheus: scrape config + alerting rules

### `prometheus.yml` snippet (add to existing config):
```yaml
scrape_configs:
  - job_name: 'cloudwatch_exporter'
    static_configs:
      - targets: ['<exporter-host>:9106']
```

Reload Prometheus after editing.

### Alert rules (cloudtrail_alerts.yml)
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
      description: "{{ $value }} AccessDenied events in last 5m."

  - alert: MultipleConsoleLoginFailures
    expr: sum(rate(aws_cloudwatch_CloudTrailMetrics_ConsoleLoginFailures_sum[5m])) > 5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Multiple failed console login attempts"
      description: "{{ $value }} failed console logins in last 5m."

  - alert: SuspiciousIPActivity
    expr: sum(rate(aws_cloudwatch_CloudTrailMetrics_SuspiciousIPCalls_sum[5m])) > 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "API calls from suspicious IP detected"
      description: "Suspicious IP activity detected: {{ $value }} calls in last 5m."
```

**Note:** Metric names may differ depending on exporter labeling. Use the `/metrics` output to find exact names, then adjust rules accordingly.

---

## 9. Alertmanager → Microsoft Teams

Two approaches:

### A. Recommended: Use `alertmanager-msteams` adapter (official forks exist)
**Why:** Adapter converts Alertmanager JSON into Teams-friendly message cards and supports retry/formatting.

**1) Create an Incoming Webhook in Teams**
- In Teams channel → ••• → Connectors → Incoming Webhook → give it a name (e.g., `Alertmanager`) and upload an icon if you want.
- Copy the generated webhook URL and store in a secrets manager.

**2) Run `alertmanager-msteams` adapter**
We will run a small adapter that accepts Alertmanager webhook and forwards to Teams.

Example using `idealista/alertmanager-msteams` (or use `prometheus/alertmanager-webhook` bridge if preferred):
```bash
docker run -d --name alertmanager-msteams -p 2000:2000 \
  -e TEAMS_WEBHOOK_URL="https://outlook.office.com/webhook/XXXX/IncomingWebhook/YYYY/ZZZZ" \
  idealista/alertmanager-msteams:latest
```
**Note:** Replace `TEAMS_WEBHOOK_URL` with the Teams incoming webhook URL.

**3) Configure Alertmanager to send to adapter**
`alertmanager.yml` example:
```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname','severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 3h
  receiver: 'teams'

receivers:
  - name: 'teams'
    webhook_configs:
      - url: 'http://<adapter-host>:2000/alertmanager'  # adapter endpoint
        send_resolved: true
```

Restart Alertmanager and verify under `http://<alertmanager-host>:9093` that the receiver exists.

**4) Test**
Send a test alert using `amtool` or trigger a rule — confirm you receive a Teams card in the channel.


### B. Direct (less reliable) — Alertmanager `webhook_configs` directly to Teams
- Teams incoming webhook expects a JSON payload like `{"text":"message"}`. Alertmanager posts a different JSON structure. Posting Alertmanager raw payload often results in a large unreadable message in Teams.
- **If** you want to try direct (not recommended), you can define a `webhook_configs` receiver with `http_config` and a small `post` template to map Alertmanager fields to Teams format. Example:

`alertmanager.yml` snippet (direct mapping using `send_resolved: true` and `message` template):
```yaml
receivers:
- name: 'teams-direct'
  webhook_configs:
  - url: 'https://outlook.office.com/webhook/XXXXXXXX/IncomingWebhook/YYYYYYYY/ZZZZZZ'  # Teams webhook
    send_resolved: true
    http_config:
      # optional TLS config
    # use a custom template to make Teams-friendly JSON
    body: |
      { "text": "[{{ .Status | toUpper }}] {{ .CommonLabels.alertname }} - {{ .CommonAnnotations.summary }}\nLabels: {{ range $k, $v := .CommonLabels}} {{ $k }}={{ $v }};{{end}}\nDescription: {{ .CommonAnnotations.description }}" }
```
**Warning:** Some Alertmanager builds do not support `body` field for webhook_configs; formatting behavior varies. The adapter approach is recommended for production.

---

## 10. Grafana: data sources & dashboard tips

### Add CloudWatch datasource (UI)
- Grafana → Configuration → Data sources → CloudWatch → choose credentials (Assume role / Access keys / Default) → default region → Save & Test.

### Add Prometheus datasource (UI)
- URL: `http://<prometheus-host>:9090` → Save & Test.

### Useful dashboard panels
- AccessDenied events per minute (PromQL):
```
sum(rate(aws_cloudwatch_CloudTrailMetrics_AccessDeniedCount_sum[1m]))
```
- Console login failures (5m rolling):
```
sum(rate(aws_cloudwatch_CloudTrailMetrics_ConsoleLoginFailures_sum[5m]))
```
- Alerts fired: use Alertmanager API or Prometheus `ALERTS` metric.

### Logs panel
- Use CloudWatch Logs Insights queries to show latest suspicious events. Example query in Grafana CloudWatch Logs:
```
fields @timestamp, eventName, userIdentity.arn, sourceIPAddress, errorCode, errorMessage
| filter errorCode = "AccessDenied"
| sort @timestamp desc
| limit 50
```

---

## 11. Testing the full pipeline (end-to-end)

1. **Generate an AccessDenied event** (use a restricted test user):
```bash
AWS_PROFILE=test-no-s3 aws s3 ls
```
2. **Verify CloudWatch Logs**: CloudWatch → Log groups → `/aws/cloudtrail/logs` → Inspect latest events.
3. **Verify metric filter**: Log group → Metric filters → Test pattern; check CloudWatch Metrics → CloudTrailMetrics → AccessDeniedCount.
4. **Verify exporter**: `curl http://<exporter-host>:9106/metrics` and search for the CloudTrailMetrics metrics.
5. **Verify Prometheus**: http://<prometheus-host>:9090/targets → `cloudwatch_exporter` should be UP.
6. **Force alert**: change rule threshold low or generate multiple events; check Prometheus Alerts page → should send to Alertmanager.
7. **Verify Teams notification**: check channel for card. If not received, check adapter logs.

---

## 12. Troubleshooting checklist
- No CloudTrail logs: verify trail has CloudWatch Logs enabled and the role ARN is correct.
- Filters not matching: test filter in CloudWatch Logs console with an example event.
- No metrics visible to exporter: check exporter IAM permissions, region, and config namespace/metric name.
- Prometheus target DOWN: check exporter is listening, firewall and security groups, and scrape target.
- Alerts not sent: check Prometheus `alertmanager` section in config, check Alertmanager logs, check adapter logs.
- Teams webhook returns 4xx/5xx: verify webhook URL, proxy, and adapter forwarding.

---

## 13. Alternatives & extras
- Use **CloudWatch Alarms + SNS** for AWS-native alerts (skip Prometheus/Alertmanager).
- Use **Loki** for storing logs instead of CloudWatch (cost tradeoffs).
- Use **Lambda** to transform CloudTrail -> CloudWatch -> custom metrics or direct webhook.

---

## 14. Appendix — copy-paste artifacts
- `cw-config.yml` for cloudwatch_exporter — see Section 7
- `prometheus.yml` snippet — see Section 8
- `cloudtrail_alerts.yml` — see Section 8
- `alertmanager.yml` with adapter receiver (example) — see Section 9

### Example `alertmanager.yml` (adapter)
```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname','severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 3h
  receiver: 'teams'

receivers:
  - name: 'teams'
    webhook_configs:
      - url: 'http://<adapter-host>:2000/alertmanager'
        send_resolved: true

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname']
```

---

## Final notes & next steps
- Replace placeholders (account IDs, ARNs, hostnames, webhook URLs) before deployment.
- Recommended: run adapter & exporter behind a service manager (systemd) or as containers with restart policies.
- If you want, I can produce the following next and add them to the repo:
  - Kubernetes manifests (Deployment + Service) for cloudwatch_exporter & alertmanager-msteams.
  - `cloudtrail_pipeline.drawio.xml` file pre-filled with the diagram XML to import into draw.io.
  - Grafana dashboard JSON export for the panels described.

---

*End of document*
