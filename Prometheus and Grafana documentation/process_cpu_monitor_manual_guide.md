
# Process CPU Monitoring Setup Guide (Sampling-Based via Node Exporter Textfile Collector)

This document provides a **complete manual setup guide** to monitor **per-process CPU usage only** (no memory) on Red Hat servers using a **sampling-based collector** that integrates with **Node Exporter** and **Prometheus**.  
It also includes explanations, prerequisites, verification, troubleshooting, rollback, and a one-shot script for automation.

---

## 🧩 Overview

The setup creates a lightweight collector script that:
- Samples `/proc` twice (1 second apart) to calculate CPU% like the `top` command.
- Aggregates CPU usage per executable name (`comm`).
- Writes metrics to the Node Exporter textfile collector as Prometheus-compatible `.prom` files.

### **Exported Metrics**
| Metric | Description |
|--------|--------------|
| `process_cpu_percent` | Total CPU percent aggregated per process name |
| `process_count` | Number of processes per process name |

### **Key Design**
- CPU% calculation = `(Δ process_jiffies / Δ total_jiffies) × 100 × NCPU`
- Metrics are exposed via Node Exporter → scraped by Prometheus.

---

## ⚙️ Step 0 — Prerequisites & Verification

Run the following as **root** or with **sudo**.

```bash
# 1. Check node_exporter binary path
ls -l /usr/local/bin/node_exporter || which node_exporter

# 2. Ensure node_exporter service exists
systemctl status node_exporter --no-pager || echo "node_exporter service not found!"

# 3. Check if 'marigold' (Node Exporter user) exists
getent passwd marigold || echo "User marigold not found. Update user if needed."

# 4. Verify Node Exporter endpoint
curl -s http://localhost:9100/metrics | head -n 5

# 5. Confirm permission to create textfile directory
touch /var/lib/node_exporter/test && rm -f /var/lib/node_exporter/test
```

---
