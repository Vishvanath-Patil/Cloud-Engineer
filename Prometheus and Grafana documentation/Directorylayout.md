
# 📁 Prometheus & Alertmanager Directory Structure

This document outlines the recommended directory structure for deploying Prometheus and Alertmanager on a Linux server, based on the setup instructions in `prometheus-setup.md` and `alertmanager-setup.md`.

---

## 📂 Directory Layout

```bash
/prometheus-server/
├── etc/
│   ├── prometheus/
│   │   ├── prometheus.yml              # Main Prometheus config
│   │   ├── alert.rules.yml             # CPU >70% alert rule config
│   │   ├── consoles/                   # Default web UI templates
│   │   └── console_libraries/          # Template library
│   └── alertmanager/
│       └── alertmanager.yml            # Alertmanager configuration
├── var/
│   ├── lib/
│   │   └── alertmanager/               # Alertmanager's internal data
│   └── prometheus/                     # Prometheus TSDB (can be /data)
│       └── ...                         # Time-series storage files
├── usr/
│   └── local/
│       └── bin/
│           ├── prometheus              # Prometheus binary
│           ├── promtool                # Prometheus config checker
│           ├── alertmanager            # Alertmanager binary
│           └── amtool                  # Alertmanager CLI
└── systemd/
    ├── prometheus.service             # Systemd unit file for Prometheus
    └── alertmanager.service           # Systemd unit file for Alertmanager
```

---

## 📝 Notes

- **Config Files**

  - Prometheus config: `/etc/prometheus/prometheus.yml`
  - Alert rules: `/etc/prometheus/alert.rules.yml`
  - Alertmanager config: `/etc/alertmanager/alertmanager.yml`

- **Storage**

  - Prometheus time series data: `/data` or `/var/prometheus`
  - Alertmanager state and silences: `/var/lib/alertmanager`

- **Executables**

  - Binaries should be stored in `/usr/local/bin/`

- **Systemd Service Files**

  - Located in `/etc/systemd/system/`

---

## 📬 Example Integration

This structure ensures clean separation of configuration, data, binaries, and service files—ideal for automation, backup, or version control (e.g., Git).

Add this file to your Git repository alongside:

- `prometheus-setup.md`
- `grafana-setup.md`
- `alertmanager-setup.md`

---

✅ You are now ready to manage your observability stack with best practices in structure and configuration.
