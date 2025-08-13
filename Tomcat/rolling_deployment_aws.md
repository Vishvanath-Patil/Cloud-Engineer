# Rolling Deployment with Deregister/Register in AWS Target Groups

## 1️⃣ Type of Deployment
This process is a **Rolling Deployment** (or **Blue-Green style** if using separate environments).

- **Rolling** → You update instances one by one while others keep serving traffic.
- **Drain-and-Deploy** → Specifically, you “drain” traffic from one instance (deregister from the target group), deploy the new app version, test, and then register it back.

---

## 2️⃣ Why We Do This

| Reason                | Explanation |
|-----------------------|-------------|
| **Avoid downtime**    | If you deploy directly on a live instance in the target group, users could hit errors during restart. Deregistering first ensures no user requests go to that instance while it’s being updated. |
| **Safe rollback**     | If something breaks after deployment, you can simply keep the updated instance deregistered or revert changes without affecting active users. |
| **Better user experience** | Eliminates half-loaded pages, connection resets, and HTTP 5xx errors during Tomcat restarts. |
| **Load balancing health** | ALB/NLB health checks won’t fail during deployment because the instance is intentionally removed from the target group before downtime happens. |

---

## 3️⃣ Step-by-Step Flow

1. **Deregister** instance from Target Group in AWS (via Console, CLI, or automation).
2. **ALB stops sending new requests** to it.
3. Ongoing connections are allowed to finish (**draining**).
4. **Stop Tomcat** on that instance.
5. **Deploy** WAR/JAR into `/prd/EIG_OUT/webapps/`.
6. **Start Tomcat** again and verify logs (`catalina.out`, app logs).
7. Perform **smoke tests** (basic functional checks).
8. **Register** instance back to the Target Group.
9. Repeat for other instances until all are updated.

---

## 4️⃣ Why Not Deploy Without Deregistering?

- Users hitting the instance during deployment may see **HTTP 502/503 errors**.
- Tomcat restart or WAR unpacking may cause **partial resource availability**.
- Could fail **ALB health checks** → ALB might temporarily remove it anyway, but **after serving some bad requests**.

---

✅ **Best Practice:** Always deregister from Target Group before restarting Tomcat or deploying to avoid serving bad traffic.
