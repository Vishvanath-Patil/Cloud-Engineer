# Apache Tomcat Deployment & Management Guide (RHEL 9)

This guide covers **deployment**, **log management**, **SSL setup**, and **important commands** for Apache Tomcat, customized for the environment where:
- **Tomcat service path:** `/prd/MY_APP`
- **Webapps directory:** `/prd/MY_APP/webapps`
- **OS:** RHEL 9

---

## 1️⃣ Tomcat Directory Structure

| Path | Description |
|------|-------------|
| `/prd/MY_APP/bin` | Startup and shutdown scripts (`startup.sh`, `shutdown.sh`) |
| `/prd/MY_APP/conf` | Configuration files (`server.xml`, `web.xml`, `tomcat-users.xml`) |
| `/prd/MY_APP/lib` | Java libraries required by Tomcat |
| `/prd/MY_APP/logs` | All Tomcat logs |
| `/prd/MY_APP/temp` | Temporary working directory |
| `/prd/MY_APP/webapps` | Deployment folder for `.war` applications |
| `/prd/MY_APP/work` | Compiled JSPs and temporary files |

---

## 2️⃣ Deploying Applications

### Deploy WAR File
1. Copy your `.war` file to:
   ```bash
   cp myapp.war /prd/MY_APP/webapps/
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
| `catalina.out` | `/prd/MY_APP/logs/catalina.out` | Main Tomcat console output (startup, shutdown, errors) |
| `localhost.log` | `/prd/MY_APP/logs/localhost.<date>.log` | Logs for localhost container messages |
| `manager.log` | `/prd/MY_APP/logs/manager.<date>.log` | Access logs for the `/manager` webapp |
| `host-manager.log` | `/prd/MY_APP/logs/host-manager.<date>.log` | Logs for host manager webapp |
| `localhost_access_log` | `/prd/MY_APP/logs/localhost_access_log.<date>.txt` | HTTP access logs (status codes, URLs) |

### Importance of Logs
- **catalina.out** → Primary debugging log for application errors and Tomcat startup issues.
- **localhost_access_log** → Monitor traffic, detect suspicious requests.
- **manager.log** → Track deployment activities.

---

## 4️⃣ Starting and Stopping Tomcat

### A. Using systemctl (Service Managed)
```bash
systemctl start MY_APP
systemctl stop MY_APP
systemctl restart MY_APP
systemctl status MY_APP
```

### B. Using Scripts (Manual Mode)
Tomcat scripts are located inside `/prd/MY_APP/bin`.

```bash
# Start Tomcat manually
/prd/MY_APP/bin/startup.sh

# Stop Tomcat manually
/prd/MY_APP/bin/shutdown.sh

# Check if Tomcat is running
ps -ef | grep tomcat

# View live logs
tail -f /prd/MY_APP/logs/catalina.out
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
@reboot /prd/MY_APP/bin/startup.sh
```

Save and exit. Now Tomcat will start automatically on reboot.

---

## 6️⃣ Adding SSL Certificate to Tomcat

### Step 1: Create Keystore
```bash
keytool -genkeypair -alias tomcat -keyalg RSA -keysize 2048   -keystore /prd/MY_APP/conf/tomcat.keystore   -validity 3650
```

### Step 2: Import CA-Signed Certificate
```bash
keytool -import -trustcacerts -alias tomcat   -file server.crt   -keystore /prd/MY_APP/conf/tomcat.keystore
```

### Step 3: Configure `server.xml`
Edit `/prd/MY_APP/conf/server.xml`:
```xml
<Connector port="8443" protocol="org.apache.coyote.http11.Http11NioProtocol"
           maxThreads="150" SSLEnabled="true">
    <SSLHostConfig>
        <Certificate certificateKeystoreFile="/prd/MY_APP/conf/tomcat.keystore"
                     type="RSA" />
    </SSLHostConfig>
</Connector>
```

### Step 4: Restart Tomcat
```bash
systemctl restart MY_APP
```

---

## 7️⃣ Maintenance Tips
- Rotate `catalina.out` logs to prevent huge file size.
- Always test SSL renewal in a staging environment before production.
- Keep backups of `server.xml` and `tomcat-users.xml` before changes.
- If using crontab auto-start, verify logs after reboot.

---

✅ **With this setup, you can deploy applications, monitor logs, secure Tomcat with SSL, and configure auto-start on reboot in your `/prd/MY_APP` environment on RHEL 9.**
