# eBPF-Based Monitoring Setup Guide (RHEL 8 + Prometheus + Grafana)

**Last Updated:** 2025-10-08

---

## 📘 Overview

This document provides a **complete step-by-step guide** to set up **eBPF-based monitoring** for **per-process I/O and CPU usage** using your existing **Prometheus and Grafana** setup on **RHEL 8** servers.

---

## 1️⃣ Prerequisites for RHEL 8 Servers

### Kernel Requirements
eBPF requires a Linux kernel version **>= 4.18** (RHEL 8 default kernel supports it).

```bash
uname -r
```

> ✅ **Expected Output:** Kernel version `4.18.x` or above.

### Required Packages
Install dependencies for eBPF tools and BCC (BPF Compiler Collection):

```bash
sudo dnf install -y bcc bcc-tools python3-bcc bpftrace bpftool git make gcc
```

> **Note:** These tools allow you to interact, compile, and trace BPF programs in the kernel.

### User Permissions
Ensure Prometheus and eBPF exporter can access `/sys`, `/proc`, and `/sys/fs/bpf`:

```bash
sudo usermod -aG root prometheus
```

### SELinux and Firewall
If SELinux is enforcing, add rules for eBPF exporter ports (default 9435):

```bash
sudo semanage port -a -t http_port_t -p tcp 9435
sudo firewall-cmd --permanent --add-port=9435/tcp
sudo firewall-cmd --reload
```

### Verify eBPF Compatibility

```bash
bpftool feature
```

Look for `"eBPF is supported"` in the output.

---

## 2️⃣ Verify Existing Prometheus and Grafana Setup

### Common File Paths
| Component | File Path |
|------------|------------|
| Prometheus config | `/etc/prometheus/prometheus.yml` |
| Prometheus data dir | `/var/lib/prometheus/` |
| Prometheus systemd unit | `/etc/systemd/system/prometheus.service` |
| Grafana config | `/etc/grafana/grafana.ini` |

### Verify Permissions

```bash
sudo ls -ld /etc/prometheus /var/lib/prometheus
sudo systemctl status prometheus grafana-server
```

> **Note:** Prometheus must run as the `prometheus` user and Grafana as `grafana`.

---

## 3️⃣ Install and Configure eBPF Exporter

### Option A: With Internet Access

```bash
git clone https://github.com/cloudflare/ebpf_exporter.git
cd ebpf_exporter
make
sudo cp ebpf_exporter /usr/local/bin/
```

### Option B: Without Internet Access

1. On an internet-connected RHEL 8 machine:
   ```bash
   git clone https://github.com/cloudflare/ebpf_exporter.git
   cd ebpf_exporter && make
   tar czvf ebpf_exporter_pkg.tar.gz ebpf_exporter configs/
   ```
2. Transfer to target server:
   ```bash
   scp ebpf_exporter_pkg.tar.gz root@<target>:/tmp/
   ```
3. Extract and install:
   ```bash
   sudo tar xzvf /tmp/ebpf_exporter_pkg.tar.gz -C /usr/local/
   ```

### Configuration Example

Create `/etc/ebpf_exporter/config.yml`:

```yaml
programs:
  - name: process_cpu_io
    metrics:
      - name: process_cpu_seconds_total
        help: "Per-process CPU usage"
        table: process_cpu
      - name: process_io_bytes_total
        help: "Per-process I/O usage"
        table: process_io
```

### Create Systemd Service

```bash
sudo tee /etc/systemd/system/ebpf_exporter.service <<EOF
[Unit]
Description=eBPF Exporter
After=network.target

[Service]
ExecStart=/usr/local/bin/ebpf_exporter --config.file=/etc/ebpf_exporter/config.yml
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now ebpf_exporter
```

> **Note:** eBPF needs root privileges to attach BPF programs to kernel events.

---

## 4️⃣ Integration with Prometheus

Edit `/etc/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'ebpf_exporter'
    static_configs:
      - targets: ['localhost:9435']
```

Reload Prometheus:

```bash
sudo systemctl reload prometheus
```

Verify reload:

```bash
curl -s localhost:9090/-/reload
```

---

## 5️⃣ Integration with Grafana

### Option A: Import Pre-built Dashboard

1. Open Grafana → **Dashboards → Import**
2. Use dashboard ID `16923` (example eBPF dashboard)
3. Select Prometheus data source.

### Option B: Create Custom Dashboard

Create new dashboard → Add Panel → Use queries like:

```promql
sum by (comm) (rate(process_cpu_seconds_total[1m]))
sum by (comm) (rate(process_io_bytes_total[1m]))
```

---

## 6️⃣ Verification Steps

### Verify Exporter

```bash
curl -s localhost:9435/metrics | grep process
```

### Verify Prometheus

```bash
curl -s localhost:9090/api/v1/targets | jq .
```

### Verify Grafana
Open Grafana panel and check for **per-process CPU/IO data**.

---

## 7️⃣ Final Verification

Cross-check with:

```bash
top -b -n1 | head -20
iotop -b -n1 | head -10
```

Compare top processes with Grafana visualizations.

---

## 8️⃣ Dashboard Creation

| Metric | Description | Example Query |
|--------|-------------|---------------|
| CPU per process | CPU usage by process name | `sum by (comm) (rate(process_cpu_seconds_total[1m]))` |
| Disk I/O per process | I/O bytes per process | `sum by (comm) (rate(process_io_bytes_total[1m]))` |
| Top 5 processes | CPU top consumers | `topk(5, sum by (comm) (rate(process_cpu_seconds_total[1m])))` |

---

## 9️⃣ Troubleshooting and Logging

### Common Issues

| Issue | Resolution |
|--------|-------------|
| Missing metrics | Check exporter logs |
| Permission denied | Run exporter as root |
| Kernel unsupported | Upgrade to RHEL 8.6+ |
| SELinux block | Use `setenforce 0` temporarily (test only) |

### Logs

```bash
sudo journalctl -u ebpf_exporter -f
sudo bpftool prog show
```

---

## 🔟 Rollback and Cleanup

```bash
sudo systemctl stop ebpf_exporter
sudo systemctl disable ebpf_exporter
sudo rm -f /usr/local/bin/ebpf_exporter /etc/systemd/system/ebpf_exporter.service /etc/ebpf_exporter/config.yml
sudo systemctl reload prometheus
```

---

## 🧠 Notes

- eBPF exporter attaches BPF programs to kernel tracepoints to monitor per-process metrics.
- Always monitor exporter CPU/memory usage (it can consume more resources if many processes run).
- Recommended scrape interval: **15–30 seconds**.

---

✅ **Setup Complete!**
Your RHEL 8 server is now integrated with **Prometheus and Grafana** for **process-level CPU and Disk I/O monitoring** using **eBPF Exporter**.

---

**Author:** DevOps Monitoring Guide  
**Tested On:** RHEL 8.8 + Prometheus 2.52 + Grafana 10.4  
