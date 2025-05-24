
# Grafana Alert Labels and Notifications - Complete Guide

This document helps you understand and implement **labels** and **notification policies** effectively in Grafana's alerting system. It's designed for real-world CPU, Memory, and Disk alerting scenarios.

---

## 🏷️ What Are Labels?
Labels are **key-value pairs** used in alert rules. They are critical for:
- **Routing** alerts to the right contact points
- **Grouping** and organizing alerts
- **Filtering** in Grafana dashboards or APIs

### 🔑 Common Label Keys and Values
| Label Key    | Label Value        | Purpose                                      |
|--------------|---------------------|----------------------------------------------|
| `team`       | `devops`, `backend` | Who is responsible for this alert            |
| `severity`   | `warning`, `critical` | How urgent is the alert                   |
| `metric`     | `cpu`, `memory`, `disk` | What metric is being monitored          |
| `environment`| `prod`, `staging`    | Useful for different environments            |
| `region`     | `us-east-1`, `ap-south-1` | For multi-region alerting              |
| `instance`   | Dynamic value (e.g., `ip-10-0-0-1`) | Comes from Prometheus data |

---

## 🛠️ How Labels Help in Backend

### 🔄 Notification Routing
Grafana matches alert labels to Notification Policies:
```yaml
Labels:
  severity: critical
  team: devops
  metric: cpu
```
→ Matched in Notification Policy:
```yaml
Match:
  team = devops
  severity = critical
  metric = cpu
→ Send to: devops-pager
```

### 📊 Grouping
```yaml
Group By: [team, metric]
```
This groups all CPU alerts for the DevOps team into one message, avoiding alert storms.

### 📁 Organizing & Filtering in UI
Labels help users filter alerts by team, severity, or metric for easy visibility and triage.

### 🚨 Escalation Logic
Match `severity` label to determine escalation level:
```yaml
severity = critical → PagerDuty
severity = warning → Email only
```

---

## 📢 Step-by-Step: Configure Notification Policy

### Step 1: Create Contact Point
1. Navigate to **Alerting > Contact Points**
2. Click **New Contact Point**
3. Choose method (Email, Slack, Webhook)
4. For Email:
   - Type: `Email`
   - Address: `devops@example.com`
   - Save

### Step 2: Define Notification Policy
1. Go to **Alerting > Notification Policies**
2. Click **New Nested Policy**
3. Set **matchers**:
```yaml
Match:
  team = devops
  severity = critical
```
4. Assign to a Contact Point (e.g., `DevOps Pager`)
5. Configure grouping:
   - **Group By**: instance, alertname
   - **Group Wait**: 30s
   - **Group Interval**: 5m
   - **Repeat Interval**: 1h

---

## 📦 Example Alert Rule for CPU, Memory, and Disk

### CPU Alert
```yaml
Labels:
  severity: critical
  team: devops
  metric: cpu
```

### Memory Alert
```yaml
Labels:
  severity: warning
  team: backend
  metric: memory
```

### Disk Alert
```yaml
Labels:
  severity: critical
  team: devops
  metric: disk
```

---

## 🧪 Sample Use Case
### Alert Rule:
```yaml
Labels:
  severity: critical
  team: backend
  instance: ip-10-0-0-1
  metric: memory
```

### Notification Policy:
```yaml
Match:
  team = backend
  severity = critical
Contact Point: backend-pager
```

---

## 💡 Best Practices
- Always define `severity`, `team`, and `metric` in every alert rule
- Match those labels in your Notification Policies
- Use consistent naming to prevent misrouting
- Group alerts to prevent notification floods
- Use test alerts to validate contact points

---

## 👷‍♂️ How to Customize Notification Title
To show instance and value in the alert title:

**In the Alert Rule → Custom Message section:**
```
Alert: High CPU Usage on {{ $labels.instance }} (Current: {{ $values.B.Value }}%)
```

---

Created by: DevOps Team
Date: 2025-05-24
