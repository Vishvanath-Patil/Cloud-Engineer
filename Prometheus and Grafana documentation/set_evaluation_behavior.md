# Set Evaluation Behavior in Grafana Alerting

This section explains how to configure the evaluation behavior for alert rules in Grafana's unified alerting system.

---

## 📁 Folder

Organize alert rules into logical folders for better management.

- **Example**: `Infra Monitoring`
- Use different folders for teams or alert categories (e.g., `Database Alerts`, `Frontend`, etc.)

---

## 👥 Evaluation Group

Groups rules for concurrent evaluation.

- **Why**: Ensures all rules in the same group are evaluated at the same time, improving efficiency and consistency.
- **Default Behavior**: All rules in a group are evaluated every 1 minute.

**Example Group**: `infra-group`

---

## ⏱️ Evaluation Interval

All rules within the group are evaluated at a fixed interval:

- **Default**: Every 1 minute (`1m`)
- Not configured per rule, but by group

---

## ⏳ Pending Period

Sets a grace period before switching from `Pending` to `Firing`.

- **Purpose**: Prevent false positives due to brief spikes
- **Example**: If set to `5m`, the condition must hold for 5 minutes before the alert is triggered.

---

## ⏸️ Pause Evaluation

Temporarily stops evaluation of the alert rule.

- **Use Case**: During system maintenance or deployments.
- **Note**: Keeps the rule config intact without deleting it.

---

## ❓ No Data Handling

Defines what happens when no data is returned.

| Option            | Description                                  |
|------------------|----------------------------------------------|
| Set state to OK  | Assume all is well                           |
| Set state to Alerting | Trigger alert as a precaution           |
| Keep Last State  | Retain the alert’s last known status         |

**Recommendation**: Use `Keep Last State` to avoid false positives unless `Alerting` is critical.

---

## ⚠️ Error Handling

Defines behavior when a query fails.

| Option            | Description                                  |
|------------------|----------------------------------------------|
| Set state to OK  | Suppress alerts on backend issues            |
| Set state to Alerting | Trigger alert when a query fails        |
| Keep Last State  | Maintain previous alert status               |

**Recommendation**: Use `Set state to Alerting` for critical alerts.

---

## ✅ Recommended Configuration Example

```text
Folder:             Infra Monitoring
Evaluation Group:   infra-group
Evaluation Every:   1m
Pending Period:     5m
Pause Evaluation:   No (Unchecked)
No Data Handling:   Keep Last State
Error Handling:     Set state to Alerting
```

---

Created by: DevOps Team  
Date: 2025-05-24