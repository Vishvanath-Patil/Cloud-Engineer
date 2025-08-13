# MY_APP Deployment Guide – Fintech Production

This guide explains how to deploy the `MY_APP` service located at `/prd/MY_APP/webapps` in a **safe, zero-downtime** manner using AWS Target Group deregistration.

---

## **1️⃣ Pre-Deployment Checklist**
Before starting:

| Check Item | Why It Matters |
|------------|---------------|
| Confirm maintenance window or change approval | Mandatory in fintech due to high transaction sensitivity |
| Get WAR/JAR file from build pipeline (Jenkins, GitLab CI, etc.) | Deployment artifact |
| Verify correct environment build (UAT, Prod) | Avoid wrong environment deploy |
| Ensure SSH access to the instance | Prevent delays |
| Check free disk space in `/prd/MY_APP/webapps` | Avoid failed deployment |
| Note the **current WAR version** | For rollback |
| Inform NOC/monitoring team | Avoid false downtime alerts |

---

## **2️⃣ Deployment Steps**

### **Step 1: Deregister Instance from Target Group**
```bash
aws elbv2 deregister-targets \
    --target-group-arn <TARGET_GROUP_ARN> \
    --targets Id=<INSTANCE_ID>

aws elbv2 describe-target-health \
    --target-group-arn <TARGET_GROUP_ARN>
```
Wait until TargetState = "draining" or "unused".

### **Step 2: Stop EIG_OUT Tomcat Service**
```bash
cd /prd/EIG_OUT/bin
./stop.sh
ps -ef | grep -i tomcat | grep EIG_OUT
```
Output should be empty.

### **Step 3: Backup Current WAR**
```bash
cd /prd/EIG_OUT/webapps
cp EIG_OUT.war /backup/EIG_OUT.war_$(date +%F_%T)
```
### **Step 4: Deploy New WAR**
```bash
cd /prd/EIG_OUT/webapps
rm -rf EIG_OUT   # Remove old exploded folder
cp /deployments/EIG_OUT.war ./EIG_OUT.war
```
### **Step 5: Start Tomcat**
```bash
cd /prd/EIG_OUT/bin
./start.sh
```
### **Step 6: Verify Startup Logs**
```bash
tail -f /prd/EIG_OUT/logs/catalina.out
```
Look for:

Server startup in XXXX ms

No stack traces or errors

## **3️⃣ Post-Deployment Verification**
Check /health or /status endpoint:

```bash
curl -k https://eig-out.example.com/health
```
Perform a sandbox test transaction if available.

### Monitor logs:
```bash
grep -i "ERROR" /prd/EIG_OUT/logs/catalina.out
```
### **Verify AWS Target Group health:**

```bash
aws elbv2 register-targets \
    --target-group-arn <TARGET_GROUP_ARN> \
    --targets Id=<INSTANCE_ID>

aws elbv2 describe-target-health \
    --target-group-arn <TARGET_GROUP_ARN>
```
Wait until "healthy".

## **4️⃣ Rollback Procedure (If Deployment Fails)**
Stop EIG_OUT service:

```bash
cd /prd/EIG_OUT/bin
./stop.sh
```
Restore previous WAR:

```bash
cd /prd/EIG_OUT/webapps
rm -rf EIG_OUT
cp /backup/EIG_OUT.war_<DATE_TIME> ./EIG_OUT.war
```
Start service:
```bash
cd /prd/EIG_OUT/bin
./start.sh
```
Verify logs:
```bash
tail -f /prd/EIG_OUT/logs/catalina.out
Register instance back to Target Group:
```
```bash
aws elbv2 register-targets \
    --target-group-arn <TARGET_GROUP_ARN> \
    --targets Id=<INSTANCE_ID>
```
   ## **5️⃣ Final Checklist**
### ✅ New WAR deployed to /prd/EIG_OUT/webapps
### ✅ Service restarted without errors
### ✅ /health API returns 200 OK
### ✅ No ERROR or SEVERE logs after 10 minutes of traffic
### ✅ AWS Target Group shows "healthy" status
### ✅ NOC confirms no downtime alerts
