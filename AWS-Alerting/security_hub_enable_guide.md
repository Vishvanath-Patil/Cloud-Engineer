# AWS Security Hub – First-Time Enablement Guide  
Home Region: **ap-south-1 (Mumbai)**  
Account Type: **Single AWS Account (No Organizations)**  

## 0. IAM Requirements

### Do you need a new IAM user?
No. If you already have **AdministratorAccess**, that is fully sufficient.  
No new IAM user or role is required.

### Required permissions:
- AdministratorAccess (recommended)  
OR  
- AWSSecurityHubFullAccess  
- AWSConfigUserAccess  
- CloudTrail read access  

---

## 1. Prerequisites

| Requirement | Reason |
|------------|--------|
| AWS Config enabled in all Regions | Security Hub uses Config to evaluate compliance |
| CloudTrail enabled | Generates key security findings |
| Correct IAM permissions | Required for setup |
| Active AWS Regions list | Security Hub is regional |

---

## 2. Enable AWS Config (Mandatory)

AWS Config must be enabled in **every region** where you use Security Hub.  
Start with **ap-south-1 (Mumbai)**.

### 2.1 Enable AWS Config (Mumbai Region)

1. Open **AWS Console → Config**
2. Click **Set up AWS Config**
3. Select:
   - **Record all resources**
   - **Create new S3 bucket** (e.g., `company-config-logs`)
   - Allow AWS to create IAM role (`AWSConfigRole`)
4. Click **Next → Confirm → Start Recording**

### 2.2 Validate AWS Config

Go to **AWS Config → Settings** and verify:

| Setting | Expected |
|---------|----------|
| Configuration Recorder | ON |
| Recording | YES |
| S3 Delivery | Success timestamps |
| IAM Role | AWSConfigRole |

### 2.3 Repeat for Other Regions
For each region:
1. Change region (top right)
2. Open **Config**
3. Enable using the same settings

---

## 3. Validate CloudTrail (Already Enabled)

### 3.1 Validation Steps

Open **CloudTrail → Trails** and check:

| Configuration | Expected |
|---------------|----------|
| Trail exists | Yes |
| Logging | ON |
| Apply to all regions | YES |
| Management events | ON |
| S3 delivery | Working |
| Last event time | Recent |

If "Apply to all regions" = OFF → edit and enable it.

---

## 4. Enable Security Hub (Home Region: Mumbai)

### 4.1 Steps

1. Open **Security Hub**
2. Click **Enable Security Hub**
3. Keep default standards:
   - AWS Foundational Security Best Practices (enabled)
   - CIS (optional)
   - PCI (optional)
4. Click **Enable**

### 4.2 Validate

- Dashboard loads  
- Findings appear (10–60 mins)  
- Standards active  
- Controls evaluating  

---

## 5. Enable Security Hub in All Other Regions

For every other region:

1. Change region  
2. Open **Security Hub**  
3. Click **Enable Security Hub**  

---

## 6. Configure Cross-Region Aggregation

### 6.1 Set Home Region Aggregator

1. Go to **Security Hub → Settings → Regional Settings**
2. Enable **Cross-Region Aggregation**
3. Set:
   - **Home Region = ap-south-1 (Mumbai)**
   - Aggregate from **All regions**

Click **Save**.

### 6.2 Validate Aggregation

Go to **Security Hub → Findings → Filter by Region**  
You should see results from all regions.

---

## 7. Enable Integrations

Enable additional AWS security services:

- **GuardDuty**
- **Inspector**
- **Macie** (optional)
- **IAM Access Analyzer**

For each service:
1. Open the service
2. Click **Enable**
3. Repeat for all needed regions (GuardDuty, Inspector)

---

## 8. Final Validation Checklist

### Home Region (Mumbai)
- Security Hub enabled  
- Dashboard showing data  
- AWS Config recording  
- CloudTrail multi-region enabled  
- Aggregation ON  

### Other Regions
- Security Hub enabled  
- Config enabled  
- Findings generating  

### Aggregation Test
Apply filter "Region" → Should show findings from all enabled regions.

---

## 9. Summary for Documentation / Managers

1. Enable AWS Config in all regions  
2. Validate CloudTrail  
3. Enable Security Hub in Mumbai  
4. Enable Security Hub in all regions  
5. Configure cross-region aggregation  
6. Enable GuardDuty, Inspector, Macie  
7. Validate findings dashboards  

---

**End of Guide**

