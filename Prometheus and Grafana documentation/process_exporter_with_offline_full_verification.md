
# 🧩 End-to-End Process Exporter Setup (With & Without Internet) for Prometheus & Grafana

**Last Updated:** 2025-10-11  
**Author:** Vishwa

---

## 🎯 Objective
Deploy **Process Exporter v0.7.6** on target Linux servers (RHEL 8/9, CentOS 7+, Ubuntu/Debian) to collect **per-process CPU, Memory, and Disk I/O metrics**, and integrate it with Prometheus and Grafana.

This guide includes both:
- 🌐 Installation **with Internet access**
- 🚫 Installation **without Internet access (air-gapped)**

---

## ⚙️ 1️⃣ Prerequisites

| Component | Requirement |
|------------|-------------|
| OS | RHEL 8/9, CentOS 7+, Ubuntu/Debian |
| Prometheus | Already installed & running |
| Grafana | Already installed & integrated |
| Permissions | Root/sudo access required |
| Port | TCP 9256 open between Prometheus and target servers |

---

## 🌐 2️⃣ Installation (With Internet Access)

### Step 1: Download and Install Binary
```bash
VERSION="0.7.6"
ARCH=$(uname -m)

cd /tmp
curl -LO "https://github.com/ncabatoff/process-exporter/releases/download/v${VERSION}/process-exporter-${VERSION}.linux-${ARCH}.tar.gz"
tar -xzf process-exporter-${VERSION}.linux-${ARCH}.tar.gz
sudo mv process-exporter-${VERSION}.linux-${ARCH}/process-exporter /usr/local/bin/
sudo chmod 755 /usr/local/bin/process-exporter
```

✅ **Verify binary path and permissions:**
```bash
ls -l /usr/local/bin/process-exporter
which process-exporter
process-exporter --help | head -n 5
```

Expected output:
```
-rwxr-xr-x 1 root root 10M /usr/local/bin/process-exporter
/usr/local/bin/process-exporter
Usage of process-exporter:
  --config.path string
```

---

## 🚫 3️⃣ Installation (Without Internet Access)

### Step 1: Download Binary on Internet Host
On a machine with internet:
```bash
VERSION="0.7.6"
ARCH="amd64"
wget https://github.com/ncabatoff/process-exporter/releases/download/v${VERSION}/process-exporter-${VERSION}.linux-${ARCH}.tar.gz
```

### Step 2: Copy to Target Server (SCP/SFTP)
```bash
scp process-exporter-${VERSION}.linux-${ARCH}.tar.gz user@target:/tmp/
```

### Step 3: Install Manually
```bash
cd /tmp
tar -xzf process-exporter-${VERSION}.linux-${ARCH}.tar.gz
sudo mv process-exporter-${VERSION}.linux-${ARCH}/process-exporter /usr/local/bin/
sudo chmod 755 /usr/local/bin/process-exporter
```

✅ **Verify installation path:**
```bash
file /usr/local/bin/process-exporter
ls -lh /usr/local/bin/process-exporter
```

Expected:
```
/usr/local/bin/process-exporter: ELF 64-bit LSB executable
```

---

## 👤 4️⃣ Create Dedicated User and Permissions

It’s good practice to run Process Exporter as a **non-root user**.

```bash
sudo useradd --no-create-home --shell /sbin/nologin process_exporter || true
sudo chown process_exporter:process_exporter /usr/local/bin/process-exporter
sudo chmod 755 /usr/local/bin/process-exporter
```

✅ **Verify user and ownership:**
```bash
id process_exporter
ls -l /usr/local/bin/process-exporter
```

Expected output:
```
uid=1002(process_exporter) gid=1002(process_exporter)
-rwxr-xr-x 1 process_exporter process_exporter 10M /usr/local/bin/process-exporter
```

---

## ⚙️ 5️⃣ Configuration File Setup

```bash
sudo mkdir -p /etc/process-exporter
sudo tee /etc/process-exporter/process-exporter.yml > /dev/null <<'EOF'
process_names:
  - name: "{{.Comm}}"
    cmdline:
      - .*
EOF
sudo chown -R process_exporter:process_exporter /etc/process-exporter
sudo chmod 644 /etc/process-exporter/process-exporter.yml
```

✅ **Verify config:**
```bash
cat /etc/process-exporter/process-exporter.yml
ls -ld /etc/process-exporter
```

---

## 🧩 6️⃣ Create systemd Service

```bash
sudo tee /etc/systemd/system/process-exporter.service > /dev/null <<'EOF'
[Unit]
Description=Prometheus Process Exporter
After=network.target

[Service]
User=process_exporter
Group=process_exporter
ExecStart=/usr/local/bin/process-exporter   --config.path=/etc/process-exporter/process-exporter.yml   --web.listen-address=0.0.0.0:9256   --log.level=info
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now process-exporter.service
```

✅ **Verify service:**
```bash
systemctl status process-exporter --no-pager
ss -ltnp | grep 9256
```

Expected output:
```
Active: active (running)
LISTEN 0 128 *:9256 process-exporter
```

---

## 🧠 7️⃣ Verify Metrics Output

```bash
curl -s http://localhost:9256/metrics | head -n 20
```

Expected metrics examples:
```
process_cpu_seconds_total{groupname="sshd"} 13.45
process_resident_memory_bytes{groupname="sshd"} 2447360
process_io_read_bytes_total{groupname="sshd"} 102400
process_io_write_bytes_total{groupname="sshd"} 51200
```

---

## 📡 8️⃣ Prometheus Integration

Edit Prometheus config `/etc/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'process_exporter'
    static_configs:
      - targets: ['server1:9256', 'server2:9256']
```

Reload Prometheus without restart:
```bash
curl -X POST http://localhost:9090/-/reload
```

✅ **Verify target in Prometheus:**
Navigate to `http://<prometheus-server>:9090/targets`  
→ Confirm `process_exporter` shows as **UP**.

---

## 📊 9️⃣ Grafana Dashboard Setup

### Step 1: Open Grafana → Create Dashboard → Add New Panel

| Metric | Query | Description |
|--------|--------|-------------|
| 🧠 CPU % | `rate(process_cpu_seconds_total[1m]) * 100` | Per-process CPU usage |
| 💾 Memory (MB) | `process_resident_memory_bytes / 1024 / 1024` | Memory per process |
| 📈 Disk Read/s | `rate(process_io_read_bytes_total[1m])` | Disk read rate |
| 📉 Disk Write/s | `rate(process_io_write_bytes_total[1m])` | Disk write rate |

Add a Grafana variable for **groupname** to filter by process dynamically.

✅ **Verification:** CPU/Memory/I/O graphs visible per process.

---

## 🧪 10️⃣ Final Verification Checklist

| Check | Command | Expected |
|--------|----------|----------|
| Binary Installed | `which process-exporter` | `/usr/local/bin/process-exporter` |
| User Exists | `id process_exporter` | valid UID/GID |
| Config Valid | `cat /etc/process-exporter/process-exporter.yml` | YAML printed |
| Service Running | `systemctl status process-exporter` | Active (running) |
| Port Listening | `ss -ltnp | grep 9256` | Listening on 9256 |
| Metrics | `curl localhost:9256/metrics | head` | Prometheus metrics output |

---

## 🧹 11️⃣ Uninstall

```bash
sudo systemctl disable --now process-exporter.service
sudo rm -f /usr/local/bin/process-exporter
sudo rm -rf /etc/process-exporter
sudo userdel process_exporter
sudo rm -f /etc/systemd/system/process-exporter.service
sudo systemctl daemon-reload
```

✅ **Verify cleanup:**
```bash
which process-exporter || echo "Removed successfully"
```

---

## ✅ Summary

| Component | Port | Path | User | Description |
|------------|------|------|------|-------------|
| Process Exporter | 9256 | /usr/local/bin/process-exporter | process_exporter | Process metrics exporter |
| Config | — | /etc/process-exporter/process-exporter.yml | process_exporter | Process definitions |
| Prometheus | 9090 | /etc/prometheus/prometheus.yml | prometheus | Scrape job config |
| Grafana | 3000 | — | grafana | Visualization |

---

📘 **References:**
- [Process Exporter GitHub](https://github.com/ncabatoff/process-exporter)
- [Prometheus Docs](https://prometheus.io/docs/introduction/overview/)
- [Grafana Docs](https://grafana.com/docs/)

---

**Author:** *Vishwa — Automated Monitoring Setup*  
📦 **Version:** 1.1  
📅 **Date:** 2025-10-11

