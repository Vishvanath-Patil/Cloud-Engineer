
# 🧩 End-to-End Per-Process Monitoring using Process Exporter, Prometheus & Grafana

**Last Updated:** 2025-10-11

---

## 🎯 Objective
Set up end-to-end **process-wise CPU, memory, and disk I/O monitoring** on Linux servers using Process Exporter, Prometheus, and Grafana.

We will install **Process Exporter (v0.7.6)** on all target servers, integrate it with **Prometheus**, and visualize metrics in **Grafana**.

---

## ⚙️ Step-by-Step Setup Guide

### 1️⃣ Prerequisites
| Component | Requirement |
|------------|-------------|
| OS | RHEL 8/9, CentOS 7+, Ubuntu/Debian |
| Prometheus | Already installed & running |
| Grafana | Already installed & integrated |
| Permissions | Root/sudo privileges |
| Port | 9256/tcp open for Prometheus |

---

### 2️⃣ Manual Installation on Target Server

```bash
VERSION="0.7.6"
ARCH=$(uname -m)

cd /tmp
curl -LO "https://github.com/ncabatoff/process-exporter/releases/download/v${VERSION}/process-exporter-${VERSION}.linux-${ARCH}.tar.gz"
tar -xzf process-exporter-${VERSION}.linux-${ARCH}.tar.gz
sudo mv process-exporter-${VERSION}.linux-${ARCH}/process-exporter /usr/local/bin/
sudo chmod 755 /usr/local/bin/process-exporter
```

Create configuration:
```bash
sudo mkdir -p /etc/process-exporter
sudo tee /etc/process-exporter/process-exporter.yml > /dev/null <<'EOF'
process_names:
  - name: "{{.Comm}}"
    cmdline:
      - .*
EOF
```

Create systemd service:
```bash
sudo tee /etc/systemd/system/process-exporter.service > /dev/null <<'EOF'
[Unit]
Description=Prometheus Process Exporter
After=network.target

[Service]
User=nobody
Group=nobody
ExecStart=/usr/local/bin/process-exporter   --config.path=/etc/process-exporter/process-exporter.yml   --web.listen-address=0.0.0.0:9256   --log.level=info
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now process-exporter.service
```

Verify metrics:
```bash
curl -s http://localhost:9256/metrics | head
```

---

### 3️⃣ One-Shot Auto Setup Script

Save the following as `install_process_exporter.sh`:

```bash
#!/bin/bash
set -euo pipefail
VERSION="0.7.6"
ARCH=$(uname -m)

cd /tmp
curl -LO "https://github.com/ncabatoff/process-exporter/releases/download/v${VERSION}/process-exporter-${VERSION}.linux-${ARCH}.tar.gz"
tar -xzf process-exporter-${VERSION}.linux-${ARCH}.tar.gz
sudo mv process-exporter-${VERSION}.linux-${ARCH}/process-exporter /usr/local/bin/
sudo chmod 755 /usr/local/bin/process-exporter

sudo mkdir -p /etc/process-exporter
sudo tee /etc/process-exporter/process-exporter.yml > /dev/null <<'EOF'
process_names:
  - name: "{{.Comm}}"
    cmdline:
      - .*
EOF

sudo tee /etc/systemd/system/process-exporter.service > /dev/null <<'EOF'
[Unit]
Description=Prometheus Process Exporter
After=network.target

[Service]
User=nobody
Group=nobody
ExecStart=/usr/local/bin/process-exporter   --config.path=/etc/process-exporter/process-exporter.yml   --web.listen-address=0.0.0.0:9256   --log.level=info
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now process-exporter.service
echo "✅ Process Exporter installation complete!"
```

Run it:
```bash
sudo bash install_process_exporter.sh
```

---

### 4️⃣ Prometheus Integration

Add to `/etc/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'process_exporter'
    static_configs:
      - targets: ['server1:9256', 'server2:9256']
```

Reload Prometheus:
```bash
curl -X POST http://localhost:9090/-/reload
```

---

### 5️⃣ Grafana Dashboard Setup

Create new dashboard → Add panels with below queries.

| Metric | Query | Description |
|--------|--------|-------------|
| CPU % | `rate(process_cpu_seconds_total[1m]) * 100` | CPU usage per process |
| Memory (MB) | `process_resident_memory_bytes / 1024 / 1024` | Memory usage |
| Disk Read/s | `rate(process_io_read_bytes_total[1m])` | Disk read rate |
| Disk Write/s | `rate(process_io_write_bytes_total[1m])` | Disk write rate |

Add a variable `groupname` to filter by process.

---

### 6️⃣ Verification

```bash
systemctl status process-exporter
curl -s http://localhost:9256/metrics | grep process_
```

Prometheus → **Status → Targets** → check `process_exporter` UP  
Grafana → view dashboard with process-level CPU, Memory, I/O charts.

---

### 7️⃣ Uninstall

```bash
sudo systemctl disable --now process-exporter.service
sudo rm -f /usr/local/bin/process-exporter
sudo rm -rf /etc/process-exporter
sudo rm -f /etc/systemd/system/process-exporter.service
sudo systemctl daemon-reload
```

---

### ✅ Summary

| Component | Port | Path | Description |
|------------|------|------|-------------|
| Process Exporter | 9256 | /usr/local/bin/process-exporter | Process metrics |
| Config | — | /etc/process-exporter/ | Config file |
| Prometheus | 9090 | /etc/prometheus/prometheus.yml | Scrape config |
| Grafana | 3000 | — | Visualization |

---

### 📅 Author Info

**Author:** Vishwa  
**Version:** 1.0  
**Date:** 2025-10-11

