
# AWS Security Hub Setup — With S3 Bucket, IAM Role, and AWS Config (Manual Guide)

This guide explains how to enable **AWS Security Hub** from scratch in a **single AWS account with multiple regions**, using **Mumbai (ap-south-1)** as the home region.  
It includes:

- S3 Bucket creation  
- IAM Role creation  
- IAM Role assignment  
- AWS Config setup  
- Security Hub enablement  
- Validation steps  

---

# ✅ 1. Prerequisites

Before enabling Security Hub:

### ✔ You must already have:
- **AdministratorAccess** (IAM user or IAM role)  
  👉 No need to create a new IAM user.  
- **CloudTrail enabled** (already enabled in your account)  
- **AWS Config not yet enabled OR enabled without issues**

---

# ✅ 2. Create S3 Bucket (For AWS Config + Security Hub Logs)

### Step 1: Open S3 Console  
AWS Console → **S3**

### Step 2: Create Bucket
- **Bucket name:** `securityhub-config-logs-<account-id>`
- **Region:** `ap-south-1 (Mumbai)`
- **Block Public Access:** ON (default)
- **Versioning:** ON
- **Encryption:** SSE-S3 (default)

### Step 3: Add Bucket Policy  
Go to: **Bucket → Permissions → Bucket Policy**

```
{
   "Version": "2012-10-17",
   "Statement": [
      {
         "Sid": "AWSConfigBucketPermissionsCheck",
         "Effect": "Allow",
         "Principal": {
            "Service": "config.amazonaws.com"
         },
         "Action": "s3:GetBucketAcl",
         "Resource": "arn:aws:s3:::securityhub-config-logs-<account-id>"
      },
      {
         "Sid": "AWSConfigBucketDelivery",
         "Effect": "Allow",
         "Principal": {
            "Service": "config.amazonaws.com"
         },
         "Action": "s3:PutObject",
         "Resource": "arn:aws:s3:::securityhub-config-logs-<account-id>/AWSLogs/<account-id>/*",
         "Condition": {
            "StringEquals": {
               "s3:x-amz-acl": "bucket-owner-full-control"
            }
         }
      }
   ]
}
```

Replace `<account-id>` with your actual AWS account number.

---

# ✅ 3. Create IAM Role for AWS Config

Security Hub depends on AWS Config; AWS Config requires an IAM role.

### Step 1: Go to IAM Console  
AWS Console → **IAM → Roles → Create role**

### Step 2: Select Trusted Entity  
- **AWS Service**
- **Use case:** `Config`

### Step 3: Permissions  
This auto-adds:
- **AWSConfigRole**

Add S3 permissions using an inline policy (recommended):

```
{
   "Version": "2012-10-17",
   "Statement": [
      {
         "Effect": "Allow",
         "Action": [
            "s3:PutObject",
            "s3:GetBucketAcl",
            "s3:ListBucket"
         ],
         "Resource": [
            "arn:aws:s3:::securityhub-config-logs-<account-id>",
            "arn:aws:s3:::securityhub-config-logs-<account-id>/*"
         ]
      }
   ]
}
```

### Step 4: Role Name
```
AWSConfigRole-SecurityHub
```

### Step 5: Create Role  
Click **Create role**

---

# ✅ 4. Assign IAM Role to AWS Config

### Step 1: Open AWS Config  
AWS Console → **Config**

### Step 2: If not enabled → click **Set up AWS Config**

### Step 3: Choose IAM Role  
Select:
```
AWSConfigRole-SecurityHub
```

### Step 4: Choose S3 Bucket  
Select:
```
securityhub-config-logs-<account-id>
```

### Step 5: Recording  
- Resource Type: **All Resources**
- Global Resources: **Enabled**
- Recording Frequency: **1 hour**

Click **Save**

AWS Config will start recording your resources.

---

# ✅ 5. Enable Security Hub (Mumbai Home Region)

### Step 1: Open Security Hub  
AWS Console → **Security Hub**

### Step 2: Choose Mumbai as your **home region**

### Step 3: Click **Get Started**

### Step 4: Enable these options:
- ✔ AWS Config integration  
- ✔ Foundational Security Best Practices (FSBP)  
- ✔ CIS Benchmark controls  
- ✔ PCI DSS (optional)

### Step 5: Click **Enable Security Hub**

### Step 6: Enable in all regions you want  
Go to each required region → open Security Hub → click **Enable**

---

# ✅ 6. Validation (Manual Checks)

### ✔ Validate S3 Bucket  
S3 → bucket → look for:
```
AWSLogs/<account-id>/
```
If this folder appears → Config is writing logs.

---

### ✔ Validate IAM Role  
IAM → Roles → `AWSConfigRole-SecurityHub`

Check:
- AWSConfigRole policy attached
- Inline S3 policy added
- Trust relationship includes:

```
"Service": "config.amazonaws.com"
```

---

### ✔ Validate AWS Config  
AWS Config → Dashboard  
Check:
- **Recording: ON**
- **Resource Count > 0**

---

### ✔ Validate Security Hub  
Security Hub → Dashboard  
Look for:
- Findings appearing
- Controls enabled
- No integration errors

---

# 🎯 Final Notes

- No need for a new IAM user; existing **AdministratorAccess is enough**
- Mumbai region should be used as **home region**
- AWS Config MUST be enabled before Security Hub works fully
- CloudTrail is already enabled (as required)
- S3 bucket must be private and versioned

---

# Done ✅
Your Security Hub setup is now complete across multiple regions.
