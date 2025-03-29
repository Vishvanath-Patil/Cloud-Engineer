# **High Availability AWS Architecture Implementation Guide**

## **1. Overview**
This document provides a step-by-step guide to deploying a high-availability architecture in AWS with the following components:
- **Multi-AZ Deployment** for improved resilience.
- **Application Load Balancer (ALB)** for traffic distribution.
- **Two EC2 instances in Private Subnets** for hosting the application.
- **MySQL RDS Database (Multi-AZ)** for high availability.
- **NAT Gateway** for outbound internet access from private subnets.
- **Proper Security Groups & Route Tables** for secure communication.

---

## **2. Architecture Setup**
| Component            | AZ-1a                    | AZ-1b                    |
|---------------------|-------------------------|-------------------------|
| Public Subnet      | ALB (PublicSubnet-1a)   | ALB (PublicSubnet-1b)   |
| Private Subnet (App) | EC2-App-1a (PrivateAppSubnet-1a) | EC2-App-1b (PrivateAppSubnet-1b) |
| Private Subnet (DB)  | MySQL RDS Standby (PrivateDBSubnet-1a) | MySQL RDS Primary (PrivateDBSubnet-1b) |

---

## **3. Implementation Steps**

### **Step 1: Create a VPC**
1. Navigate to **VPC** in AWS Console.
2. Click **Create VPC** and specify:
   - **Name**: `MyVPC`
   - **CIDR Block**: `10.10.0.0/16`
   - **Tenancy**: Default

### **Step 2: Create Subnets**
#### **Public Subnets** (For ALB & NAT Gateway)
- **PublicSubnet-1a** (AZ-1a): `10.10.1.0/24`
- **PublicSubnet-1b** (AZ-1b): `10.10.2.0/24`

#### **Private Subnets** (For Application & DB)
- **PrivateAppSubnet-1a** (AZ-1a): `10.10.3.0/24`
- **PrivateAppSubnet-1b** (AZ-1b): `10.10.4.0/24`
- **PrivateDBSubnet-1a** (AZ-1a): `10.10.5.0/24`
- **PrivateDBSubnet-1b** (AZ-1b): `10.10.6.0/24`

### **Step 3: Create an Internet Gateway & NAT Gateway**
1. Create an **Internet Gateway** and attach it to `MyVPC`.
2. Create two **NAT Gateways** in Public Subnets:
   - **NAT-1a** in `PublicSubnet-1a`.
   - **NAT-1b** in `PublicSubnet-1b`.
3. Modify **Private Route Tables**:
   - `0.0.0.0/0` → NAT Gateway (for outbound internet access).

### **Step 4: Configure Route Table Entries**
#### **Public Route Table**
- Associate with `PublicSubnet-1a` and `PublicSubnet-1b`.
- Routes:
  - `0.0.0.0/0` → Internet Gateway (for public internet access).

#### **Private Route Table for Application Subnets**
- Associate with `PrivateAppSubnet-1a` and `PrivateAppSubnet-1b`.
- Routes:
  - `0.0.0.0/0` → NAT Gateway (for outbound internet access).

#### **Private Route Table for Database Subnets**
- Associate with `PrivateDBSubnet-1a` and `PrivateDBSubnet-1b`.
- Routes:
  - No direct internet access (private database setup).
  - Communication allowed only within the VPC.

### **Step 5: Deploy an Application Load Balancer (ALB)**
1. **Create an ALB:**
   - Navigate to **EC2 > Load Balancers** in AWS Console.
   - Click **Create Load Balancer** → Select **Application Load Balancer**.
   - Name: `MyALB`
   - **Scheme**: Internet-facing
   - **Network Mapping**: Place in `PublicSubnet-1a` and `PublicSubnet-1b`.
   - **Security Group**: Create/attach a security group (detailed in Step 6).

2. **Configure Target Groups:**
   - Navigate to **EC2 > Target Groups**.
   - Click **Create Target Group** → Select **Instance**.
   - Name: `MyAppTG`
   - Protocol: HTTP, Port: `80`
   - VPC: `MyVPC`
   - Register **EC2-App-1a & EC2-App-1b** as targets.
   - Click **Create**.

3. **Create a Security Group for ALB:**
   - Navigate to **EC2 > Security Groups**.
   - Click **Create Security Group**.
   - Name: `ALB-SG`
   - Inbound Rules:
     - Allow HTTP (80) and HTTPS (443) from `0.0.0.0/0`.
   - Outbound Rules:
     - Allow all outbound traffic.

### **Step 6: Deploy EC2 Instances for Application**
1. Launch **two EC2 instances**, placing one in each private application subnet.
2. Attach an **IAM role** (if required) to allow S3, RDS, or other AWS services access.
3. Configure **Security Groups**:
   - Allow inbound HTTP traffic from ALB security group.
   - Allow outbound traffic for MySQL (port 3306) to the RDS database.
4. **Install application dependencies** (e.g., Apache, Nginx, or a custom app stack).
5. **Test connectivity**:
   - Ensure EC2 instances can reach the RDS database.
   - Verify inbound traffic from ALB.

### **Step 7: Deploy MySQL RDS (Multi-AZ)**
1. Navigate to **RDS > Databases**.
2. Click **Create Database** and choose:
   - **Engine Type**: MySQL
   - **Multi-AZ Deployment**: Enabled
   - **Instance Type**: db.t3.medium (or as per requirements)
   - **Storage Type**: General Purpose SSD (gp3)
   - **Allocated Storage**: 20GB (or as needed)
3. **Network & Security Settings**:
   - Choose the **VPC** created earlier.
   - Associate with **PrivateDBSubnet-1a & PrivateDBSubnet-1b**.
   - Set security group rules to allow MySQL (3306) traffic from EC2 instances.
4. Click **Create Database** and monitor creation progress.
5. Verify database endpoint and credentials.

### **Step 8: Verify Setup**
1. **ALB Health Checks**:
   - Navigate to **Target Groups > MyAppTG**.
   - Ensure EC2 instances are in **Healthy** state.
2. **Test Application Accessibility**:
   - Copy the ALB **DNS Name**.
   - Open it in a browser and confirm application loads.
3. **Verify Database Connectivity**:
   - SSH into EC2 instances.
   - Use MySQL client (`mysql -h <RDS_Endpoint> -u <user> -p`) to connect.
   - Run a test query (`SHOW DATABASES;`).
4. **Multi-AZ Failover Test**:
   - Reboot the primary RDS instance.
   - Ensure failover to standby works.

---

## **4. Summary**
- **Multi-AZ Deployment** ensures High Availability.
- **ALB distributes traffic** to EC2 instances.
- **RDS (Multi-AZ) ensures failover protection**.
- **Private Subnets & Security Groups enhance security**.

Let me know if you need additional refinements! 🚀

