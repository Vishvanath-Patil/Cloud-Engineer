# 🔒 SSL Certificate Expiry Monitoring with Prometheus, Blackbox Exporter & Alertmanager

## 📌 Overview

This guide explains how to monitor **SSL/TLS certificate expiry** using
**Prometheus**, **Blackbox Exporter**, and **Alertmanager** with
email/Slack/Teams alerts.

------------------------------------------------------------------------

## 🛠 Prerequisites

-   Linux server with Docker or system binaries
-   Prometheus installed and running
-   Alertmanager installed and configured
-   Basic knowledge of Prometheus configuration
-   Email/Slack/Teams webhook credentials for Alertmanager alerts

------------------------------------------------------------------------

## ⚙ Components

1.  **Blackbox Exporter** -- Probes HTTPS endpoints and exposes metrics
2.  **Prometheus** -- Scrapes metrics from Blackbox Exporter
3.  **Alertmanager** -- Sends alerts when certificate expiry is near

------------------------------------------------------------------------

## 1️⃣ Install Blackbox Exporter

### Using Docker

``` bash
docker run -d   --name=blackbox_exporter   -p 9115:9115   prom/blackbox-exporter
```

### Using Binary

``` bash
wget https://github.com/prometheus/blackbox_exporter/releases/latest/download/blackbox_exporter-*.tar.gz
tar xvf blackbox_exporter-*.tar.gz
cd blackbox_exporter-* && ./blackbox_exporter
```

------------------------------------------------------------------------

## 2️⃣ Configure Blackbox Exporter for SSL Checks

Edit `blackbox.yml`:

``` yaml
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      method: GET
      tls_config:
        insecure_skip_verify: false
```

------------------------------------------------------------------------

## 3️⃣ Configure Prometheus to Scrape Blackbox Exporter

Edit `prometheus.yml`:

``` yaml
scrape_configs:
  - job_name: 'blackbox_ssl'
    metrics_path: /probe
    params:
      module: [http_2xx]  # Use the module from blackbox.yml
    static_configs:
      - targets:
          - https://example.com
          - https://myserver.local
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: localhost:9115  # Blackbox Exporter address
```

Restart Prometheus:

``` bash
systemctl restart prometheus
```

------------------------------------------------------------------------

## 4️⃣ Check SSL Expiry Metric

Blackbox Exporter exposes:

    probe_ssl_earliest_cert_expiry

This returns the Unix timestamp when the certificate expires.

You can convert it to days:

``` promql
(probe_ssl_earliest_cert_expiry - time()) / 86400
```

------------------------------------------------------------------------

## 5️⃣ Create Prometheus Alert Rule

Create a file `alert_rules.yml`:

``` yaml
groups:
- name: SSLExpiryAlerts
  rules:
  - alert: SSLCertificateExpiringSoon
    expr: (probe_ssl_earliest_cert_expiry - time()) / 86400 < 15
    for: 1h
    labels:
      severity: warning
    annotations:
      summary: "SSL Certificate for {{ $labels.instance }} is expiring soon"
      description: "The SSL certificate for {{ $labels.instance }} will expire in less than 15 days."
```

Edit `prometheus.yml` to load the rule:

``` yaml
rule_files:
  - "alert_rules.yml"
```

Restart Prometheus:

``` bash
systemctl restart prometheus
```

------------------------------------------------------------------------

## 6️⃣ Configure Alertmanager for Notifications

Example `alertmanager.yml` for email:

``` yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@example.com'
  smtp_auth_username: 'alerts@example.com'
  smtp_auth_password: 'app-password-here'
  smtp_require_tls: true

route:
  receiver: email-alert

receivers:
  - name: email-alert
    email_configs:
      - to: 'team@example.com'
```

For Slack:

``` yaml
receivers:
  - name: slack-alert
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/XXXX/YYYY/ZZZZ'
        channel: '#alerts'
```

For Microsoft Teams: - Use a webhook URL with a Teams connector and
`teams_configs` or via webhook relay.

Restart Alertmanager:

``` bash
systemctl restart alertmanager
```

------------------------------------------------------------------------

## ✅ Testing

1.  Change an endpoint in `prometheus.yml` to one with an expiring cert.
2.  Reload Prometheus.
3.  Verify in **Prometheus UI**: `probe_ssl_earliest_cert_expiry`
4.  Wait until condition matches (or temporarily change `< 15` to a
    higher value for testing).

------------------------------------------------------------------------

## 📌 Important Notes

-   You can monitor multiple domains easily by adding them to `targets`
    in Prometheus config.
-   Keep **Blackbox Exporter** secured (bind to localhost or behind
    firewall).
-   Use **Grafana** to visualize SSL expiry with Prometheus as the data
    source.
