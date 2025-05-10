
# Step 2: Security Group & Network Setup (for Multi-Region, Multi-Account Grafana Monitoring)

## 🎯 Objective

Enable Prometheus (running in **Account 1**, **us-east-1**) to scrape Node Exporter metrics from 360 EC2 instances deployed across:

- Multiple **VPCs**
- Multiple **AWS Regions**
- Two AWS **Accounts**

---

## ✅ 2.1 Identify Accounts and Regions

- **Monitoring Account (Account 1)**:
  - Region: `us-east-1`
  - VPC: `vpc-monitoring`
  - Prometheus instance private IP: `10.0.0.5`

- **Application Servers (Account 1 & Account 2)**:
  - Regions: `us-west-1`, `ap-south-1`, etc.
  - VPCs: `vpc-app-west`, `vpc-app-india`, etc.
  - Node Exporter runs on port `9100`

---

## 🛡️ 2.2 Security Group Rules

### 🔸 On Node Exporter EC2 Instances (Account 1 & 2)

Attach a **Security Group: `SG_Node_Exporter`**

**Inbound Rules:**

| Type         | Protocol | Port Range | Source                        | Region        |
|--------------|----------|------------|-------------------------------|---------------|
| Custom TCP   | TCP      | 9100       | `10.0.0.5/32` (Prometheus IP) | `us-east-1`   |
| (Alt)        | TCP      | 9100       | CIDR of Prometheus subnet     | `us-east-1`   |
| (Preferred)  | TCP      | 9100       | SG ID of Prometheus instance  | via VPC Peering |

**Outbound Rules (default):**

| Type     | Port | Destination | Description         |
|----------|------|-------------|---------------------|
| All      | All  | 0.0.0.0/0   | Allow all outbound  |

---

### 🔹 On Prometheus EC2 Instance (Account 1)

Attach a **Security Group: `SG_Prometheus`**

**Outbound Rules:**

| Type         | Protocol | Port Range | Destination                       | Region      |
|--------------|----------|------------|-----------------------------------|-------------|
| Custom TCP   | TCP      | 9100       | CIDRs of monitored EC2 VPCs       | All Regions |

**Inbound Rules (optional for web UI access):**

| Port | Source              | Description           |
|------|---------------------|------------------------|
| 9090 | `your-office-ip/32` | Prometheus UI          |
| 3000 | `your-office-ip/32` | Grafana UI             |

---

## 🌐 2.3 VPC Peering (for Inter-VPC & Cross-Account Access)

To enable network communication between Prometheus and remote EC2s:

1. **Create VPC Peering** connections:
   - Between `vpc-monitoring` (Account 1) and all VPCs hosting EC2s (Account 1 & 2)
   - For cross-account peering, set permissions in Account 2

2. **Accept Peering Requests** from target accounts

3. **Update Route Tables**:
   - In both VPCs, add routes to each other’s CIDR blocks

   Example (Account 1):
   ```
   Destination CIDR: 172.31.0.0/16 → Target: VPC Peering Connection
   ```

   Example (Account 2):
   ```
   Destination CIDR: 10.0.0.0/16 → Target: VPC Peering Connection
   ```

4. **Enable DNS Hostnames and DNS Resolution** in all VPCs

---

## 🔄 2.4 Optional: Cross-Account Automation with SSM

To deploy Node Exporter using AWS Systems Manager (SSM):

- Attach `AmazonSSMManagedInstanceCore` IAM role to all EC2s
- From Account 1, use **cross-account role access** or SSM document sharing if needed

---

## ✅ Testing Connectivity

From Prometheus instance:

```bash
curl http://<target-ec2-private-ip>:9100/metrics
```

Or use:

```bash
telnet <target-ec2-private-ip> 9100
```

Ensure:
- Security groups allow the traffic
- VPC routes are in place
- No NACL is blocking traffic
