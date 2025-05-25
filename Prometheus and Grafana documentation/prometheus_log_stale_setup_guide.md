
# Prometheus Setup Guide to Use `log_stale` Metric

## 🧱 Assumptions
- Monitoring logs per server.
- Detecting if a log file is "stale" (not updated recently).
- A metric `log_stale` is generated per log file, per server.

---

## 🧾 Step-by-Step Setup

### ✅ Step 1: Create `log_stale` Exporter Script

Python script example using Flask:

```python
# log_stale_exporter.py
from flask import Flask, Response
import os
import time

app = Flask(__name__)

LOG_FILES = {
    "/prd/TERRA_CORE/logs/terra_core.log": "terra_server_1",
}
STALE_THRESHOLD_SECONDS = 300  # 5 minutes

@app.route("/metrics")
def metrics():
    output = []
    for path, server in LOG_FILES.items():
        try:
            mtime = os.path.getmtime(path)
            age = time.time() - mtime
            stale = int(age > STALE_THRESHOLD_SECONDS)
            output.append(f'log_stale{{log_file="{path}", server="{server}"}} {stale}')
        except FileNotFoundError:
            output.append(f'log_stale{{log_file="{path}", server="{server}"}} 1')
    return Response("\n".join(output), mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9100)
```

---

### ✅ Step 2: Create a Systemd Service

```ini
# /etc/systemd/system/log_stale_exporter.service
[Unit]
Description=Log Stale Exporter
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/log_stale_exporter.py
Restart=always
User=nobody

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reexec
sudo systemctl enable --now log_stale_exporter
```

---

### ✅ Step 3: Configure Prometheus

Edit `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'log-stale-exporter'
    static_configs:
      - targets:
          - server1.example.com:9100
          - server2.example.com:9100
```

Reload Prometheus:
```bash
curl -X POST http://localhost:9090/-/reload
```

---

### ✅ Step 4: Validate the Metric

```bash
curl http://server1.example.com:9100/metrics | grep log_stale
```

Should return something like:
```
log_stale{log_file="/prd/TERRA_CORE/logs/terra_core.log", server="terra_server_1"} 0
```

---

### ✅ Step 5: Run PromQL Query

```promql
sum by (log_file, server) (
  log_stale{log_file=~"/prd/TERRA_CORE/logs/terra_core\.log"}
)
```

---

### ✅ Step 6: Set Alert (Optional)

```yaml
groups:
- name: log-alerts
  rules:
  - alert: LogFileStale
    expr: log_stale{log_file=~"/prd/TERRA_CORE/logs/terra_core\.log"} == 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Log file stale: {{ $labels.log_file }}"
      description: "Log file has not been updated recently on {{ $labels.server }}"
```

---

### 📊 Optional: Grafana Dashboard

- **Panel Title**: TERRA CORE Log Stale Status
- **Query**:
```promql
log_stale{log_file=~"/prd/TERRA_CORE/logs/terra_core\.log"}
```
- **Visualization**: Stat or Table
- **Thresholds**: 0 (OK), 1 (Stale)

---

### ✅ Output Example

```
log_stale{log_file="/prd/TERRA_CORE/logs/terra_core.log", server="terra_server_1"} 1
```

---

Let me know if you want:
- A Docker-based version
- Systemd `.service` and Prometheus job templates
- Grafana dashboard JSON
