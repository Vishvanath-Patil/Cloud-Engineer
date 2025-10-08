
# Process Exporter Setup & Integration Guide (Prometheus + Grafana)

This document provides a **complete guide** to monitor **process-level CPU and memory usage** on Red Hat servers using **process_exporter**, **Prometheus**, and **Grafana**.

---

## 🧩 Overview

**Process Exporter** collects process-level metrics directly from `/proc` based on configured process names or command-line patterns.

**Key Metrics:**
| Metric | Description |
|--------|-------------|
| `process_resident_memory_bytes` | Resident memory (RAM) used by the process |
| `process_virtual_memory_bytes` | Virtual memory size |
| `process_cpu_seconds_total` | Total CPU seconds consumed |
| `process_num_threads` | Number of threads |

**Default port:** `9256`

---

## 🧰 Step 0 — Prerequisites

Before starting:

```bash
# 1. Ensure basic tools are available
which wget || which curl
which tar

# 2. Check if user for exporter exists (create if not)
getent passwd process-exp || sudo useradd -r -s /sbin/nologin process-exp

# 3. Confirm no port conflict
sudo ss -tnlp | grep 9256 || true

# 4. Ensure Prometheus can access this host on port 9256
```
... (truncated for brevity)
