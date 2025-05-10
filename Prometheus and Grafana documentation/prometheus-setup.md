# Prometheus Installation & Configuration Guide

Supports: **Ubuntu 22.04+, CentOS 7/8, RHEL 8+**

## 1. Create Prometheus User
```bash
sudo useradd --system --no-create-home --shell /bin/false prometheus
```

## 2. Download and Extract Prometheus
```bash
wget https://github.com/prometheus/prometheus/releases/download/v2.47.1/prometheus-2.47.1.linux-amd64.tar.gz
tar -xvf prometheus-2.47.1.linux-amd64.tar.gz
cd prometheus-2.47.1.linux-amd64/
```

## 3. Move Binaries and Setup Directories
```bash
sudo mkdir -p /data /etc/prometheus
sudo mv prometheus promtool /usr/local/bin/
sudo mv consoles/ console_libraries/ /etc/prometheus/
sudo mv prometheus.yml /etc/prometheus/prometheus.yml
```

## 4. Set Ownership
```bash
sudo chown -R prometheus:prometheus /etc/prometheus/ /data/
```

## 5. Create Prometheus Systemd Service
```bash
sudo nano /etc/systemd/system/prometheus.service
```

Paste the following:
```
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
Restart=on-failure
RestartSec=5s
ExecStart=/usr/local/bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/data \
  --web.console.templates=/etc/prometheus/consoles \
  --web.console.libraries=/etc/prometheus/console_libraries \
  --web.listen-address=0.0.0.0:9090 \
  --web.enable-lifecycle

[Install]
WantedBy=multi-user.target
```

## 6. Start and Enable Service
```bash
sudo systemctl daemon-reexec
sudo systemctl enable prometheus
sudo systemctl start prometheus
sudo systemctl status prometheus
```

## 7. Install Node Exporter
```bash
sudo useradd --system --no-create-home --shell /bin/false node_exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
tar -xvf node_exporter-1.6.1.linux-amd64.tar.gz
sudo mv node_exporter-1.6.1.linux-amd64/node_exporter /usr/local/bin/
```

## 8. Create Node Exporter Systemd Service
```bash
sudo nano /etc/systemd/system/node_exporter.service
```

Paste the following:
```
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
Restart=on-failure
RestartSec=5s
ExecStart=/usr/local/bin/node_exporter --collector.logind

[Install]
WantedBy=multi-user.target
```

Enable Node Exporter:
```bash
sudo systemctl daemon-reexec
sudo systemctl enable node_exporter
sudo systemctl start node_exporter
sudo systemctl status node_exporter
```

## 9. Configure Prometheus to Scrape Node Exporter and Jenkins
Edit `/etc/prometheus/prometheus.yml`:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'node_exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'jenkins'
    metrics_path: '/prometheus'
    static_configs:
      - targets: ['<your-jenkins-ip>:<your-jenkins-port>']
```

Check config and reload:
```bash
promtool check config /etc/prometheus/prometheus.yml
curl -X POST http://localhost:9090/-/reload
```

Visit Prometheus:
```
http://<your-server-ip>:9090
```
