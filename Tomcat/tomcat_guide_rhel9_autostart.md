# Apache Tomcat Deployment & Management Guide (RHEL 9)

This guide covers **deployment**, **log management**, **SSL setup**, and **important commands** for Apache Tomcat, customized for the environment where:
- **Tomcat service path:** `/prd/EIG_OUT`
- **Webapps directory:** `/prd/EIG_OUT/webapps`
- **OS:** RHEL 9

---

## 1️⃣ Tomcat Directory Structure

| Path | Description |
|------|-------------|
| `/prd/EIG_OUT/bin` | Startup and shutdown scripts (`startup.sh`, `shutdown.sh`) |
| `/prd/EIG_OUT/conf` | Configuration files (`server.xml`, `web.xml`, `tomcat-users.xml`) |
| `/prd/EIG_OUT/lib` | Java libraries required by Tomcat |
| `/prd/EIG_OUT/logs` | All Tomcat logs |
| `/prd/EIG_OUT/temp` | Temporary working directory |
| `/prd/EIG_OUT/webapps` | Deployment folder for `.war` applications |
| `/prd/EIG_OUT/work` | Compiled JSPs and temporary files |

---

## 2️⃣ Deploying Applications

### Deploy WAR File
1. Copy your `.war` file to:
   ```bash
   cp myapp.war /prd/EIG_OUT/webapps/
   ```
2. Tomcat automatically extracts and deploys it.

### Deploy JAR File (Spring Boot / Standalone)
1. Place the `.jar` file in a custom directory (not webapps).
2. Run:
   ```bash
   java -jar myapp.jar &
   ```
   > **Note:** Tomcat does not run `.jar` files directly — they must be standalone Java apps.

---

## 3️⃣ Tomcat Log Files

| Log File | Location | Purpose |
|----------|----------|---------|
| `catalina.out` | `/prd/EIG_OUT/logs/catalina.out` | Main Tomcat console output (startup, shutdown, errors) |
| `localhost.log` | `/prd/EIG_OUT/logs/localhost.<date>.log` | Logs for localhost container messages |
| `manager.log` | `/prd/EIG_OUT/logs/manager.<date>.log` | Access logs for the `/manager` webapp |
| `host-manager.log` | `/prd/EIG_OUT/logs/host-manager.<date>.log` | Logs for host manager webapp |
| `localhost_access_log` | `/prd/EIG_OUT/logs/localhost_access_log.<date>.txt` | HTTP access logs (status codes, URLs) |

### Importance of Logs
- **catalina.out** → Primary debugging log for application errors and Tomcat startup issues.
- **localhost_access_log** → Monitor traffic, detect suspicious requests.
- **manager.log** → Track deployment activities.

---

## 4️⃣ Starting and Stopping Tomcat

### A. Using systemctl (Service Managed)
```bash
systemctl start EIG_OUT
systemctl stop EIG_OUT
systemctl restart EIG_OUT
systemctl status EIG_OUT
```

### B. Using Scripts (Manual Mode)
Tomcat scripts are located inside `/prd/EIG_OUT/bin`.

```bash
# Start Tomcat manually
/prd/EIG_OUT/bin/startup.sh

# Stop Tomcat manually
/prd/EIG_OUT/bin/shutdown.sh

# Check if Tomcat is running
ps -ef | grep tomcat

# View live logs
tail -f /prd/EIG_OUT/logs/catalina.out
```

---

## 5️⃣ Auto-Start Tomcat on Reboot (Crontab)

If you want Tomcat to **auto-start when the server reboots**, add an entry in the `crontab` of the Tomcat user.

Edit crontab:
```bash
crontab -e
```

Add:
```bash
@reboot /prd/EIG_OUT/bin/startup.sh
```

Save and exit. Now Tomcat will start automatically on reboot.

---

## 6️⃣ Adding SSL Certificate to Tomcat

### Step 1: Create Keystore
```bash
keytool -genkeypair -alias tomcat -keyalg RSA -keysize 2048   -keystore /prd/EIG_OUT/conf/tomcat.keystore   -validity 3650
```

### Step 2: Import CA-Signed Certificate
```bash
keytool -import -trustcacerts -alias tomcat   -file server.crt   -keystore /prd/EIG_OUT/conf/tomcat.keystore
```

### Step 3: Configure `server.xml`
Edit `/prd/EIG_OUT/conf/server.xml`:
```xml
<Connector port="8443" protocol="org.apache.coyote.http11.Http11NioProtocol"
           maxThreads="150" SSLEnabled="true">
    <SSLHostConfig>
        <Certificate certificateKeystoreFile="/prd/EIG_OUT/conf/tomcat.keystore"
                     type="RSA" />
    </SSLHostConfig>
</Connector>
```

### Step 4: Restart Tomcat
```bash
systemctl restart EIG_OUT
```

---

## 7️⃣ Maintenance Tips
- Rotate `catalina.out` logs to prevent huge file size.
- Always test SSL renewal in a staging environment before production.
- Keep backups of `server.xml` and `tomcat-users.xml` before changes.
- If using crontab auto-start, verify logs after reboot.

---

✅ **With this setup, you can deploy applications, monitor logs, secure Tomcat with SSL, and configure auto-start on reboot in your `/prd/EIG_OUT` environment on RHEL 9.**
