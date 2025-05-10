# Grafana Installation & Setup Guide

Supports: **Ubuntu 22.04+, CentOS 7/8, RHEL 8+**

## 1. Install Dependencies (Ubuntu)
```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https software-properties-common
```

## 2. Add GPG Key & Repository
```bash
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
```

_For RHEL/CentOS use yum repo from: https://grafana.com/grafana/download_

## 3. Install Grafana
```bash
sudo apt-get update
sudo apt-get -y install grafana
```

## 4. Enable and Start Grafana
```bash
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
sudo systemctl status grafana-server
```

## 5. Access Grafana Web UI
```
http://<your-server-ip>:3000
```

Default credentials:
- Username: `admin`
- Password: `admin` (prompt to change on first login)

## 6. Add Prometheus as Data Source
- Navigate to ⚙️ > Data Sources > Add data source
- Choose **Prometheus**
- Set URL: `http://localhost:9090`
- Click **Save & Test**

## 7. Import Dashboard
- Click ➕ > Import
- Use ID `1860` (or other)
- Select Prometheus as the data source
- Click **Import**
