
# Libreswan IPSec VPN Setup on AWS EC2 (Red Hat)

This guide walks through setting up an IPSec VPN tunnel between two EC2 instances using Libreswan on Red Hat. It includes installation, configuration, iptables setup, and troubleshooting.

---

## 🧱 Prerequisites

- Two EC2 instances (RHEL 8 or 9) with Elastic IPs
- Open ports UDP 500 and 4500
- ICMP (ping) enabled
- Source/Destination check disabled on both instances

---

## 🛠️ Step 1: Install Libreswan

```bash
sudo dnf install -y libreswan
```

---

## 📁 Directory Setup & Files

### Create VPN config directory

```bash
mkdir -p /root/vpnsetup
cd /root/vpnsetup
```

### Create `/root/vpnsetup/setupiptable.sh`

```bash
#!/bin/bash
echo "Setting up iptables for IPSec"

# Allow necessary ports
firewall-cmd --permanent --add-port=500/udp
firewall-cmd --permanent --add-port=4500/udp
firewall-cmd --permanent --add-masquerade
firewall-cmd --reload

# Enable IP forwarding
echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.conf
sysctl -p
```

Make it executable:

```bash
chmod +x /root/vpnsetup/setupiptable.sh
```

Run it:

```bash
/root/vpnsetup/setupiptable.sh
```

---

## 🔧 VPN Configuration

### `/etc/ipsec.conf`

```conf
config setup
  uniqueids=no

include /etc/ipsec.d/*.conf
```

### `/etc/ipsec.d/vpn.conf` (Example for Server A)

```conf
conn myvpn
    left=1.1.1.1
    leftid=1.1.1.1
    leftsubnet=10.0.0.0/24
    right=2.2.2.2
    rightid=2.2.2.2
    rightsubnet=10.0.1.0/24
    authby=secret
    auto=start
    ike=aes256-sha2;modp1024
    phase2alg=aes256-sha2
    type=tunnel
    keyexchange=ike
```

### `/etc/ipsec.secrets`

```conf
1.1.1.1 2.2.2.2 : PSK "YourStrongPSK"
```

---

## 🚀 Start Services

```bash
sudo systemctl enable ipsec
sudo systemctl start ipsec
```

---

## 🧪 Testing the VPN

- From Server A:
  ```bash
  ping 10.0.1.1
  ```
- From Server B:
  ```bash
  ping 10.0.0.1
  ```

---

## 🛠️ Troubleshooting

```bash
ipsec verify
ipsec status
ipsec auto --status
journalctl -u ipsec
ipsec trafficstatus
```
Use `tcpdump` to trace traffic:

```bash
tcpdump -n -i eth0 udp port 500 or udp port 4500
```

---

## 📌 Notes

- Replace IPs and subnets accordingly.
- Ensure security groups and routing tables allow traffic.
- Use Elastic IPs for stable configuration.

---

**Author: AWS VPN Setup Guide with Libreswan for RHEL EC2 Instances**
