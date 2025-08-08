
# Replacing Old SSL Certificate in Tomcat (Production Guide)

This guide explains how to replace an old SSL certificate in Tomcat with minimal downtime.

---

## 1️⃣ Step 1: Locate Existing SSL Setup

Find the current keystore path in Tomcat:
```bash
grep -i "keystoreFile" /opt/tomcat/conf/server.xml
```
Example output:
```
keystoreFile="/opt/tomcat/conf/keystore.jks"
```

Check the keystore type:
```bash
file /opt/tomcat/conf/keystore.jks
```
or:
```bash
keytool -list -keystore /opt/tomcat/conf/keystore.jks
```

---

## 2️⃣ Step 2: Get New SSL Files from CA

From your certificate provider, you should have:
- **Private Key** → `mydomain.key` (from CSR)
- **Certificate** → `mydomain.crt` (signed by CA)
- **CA Bundle / Intermediate Cert** → `ca-bundle.crt`

⚠ **Important:** If the private key is missing, re-generate CSR and request a new cert.

---

## 3️⃣ Step 3: Create New Keystore

We’ll use a temporary keystore file so old SSL keeps working until restart.

```bash
openssl pkcs12 -export   -in mydomain.crt   -inkey mydomain.key   -certfile ca-bundle.crt   -name tomcat   -out /opt/tomcat/conf/new_keystore.p12
```

Convert to JKS if Tomcat uses JKS:
```bash
keytool -importkeystore   -destkeystore /opt/tomcat/conf/new_keystore.jks   -srckeystore /opt/tomcat/conf/new_keystore.p12   -srcstoretype pkcs12
```

---

## 4️⃣ Step 4: Backup Old SSL

Before touching `server.xml` or keystore:
```bash
cp /opt/tomcat/conf/keystore.jks /opt/tomcat/conf/keystore_old_$(date +%F).jks
cp /opt/tomcat/conf/server.xml /opt/tomcat/conf/server.xml.bak
```

---

## 5️⃣ Step 5: Update Tomcat Config

Edit:
```bash
nano /opt/tomcat/conf/server.xml
```
Find the `<Connector>` block for SSL (port 8443 or 443):
```xml
<Connector 
    port="8443"
    protocol="org.apache.coyote.http11.Http11NioProtocol"
    SSLEnabled="true"
    keystoreFile="/opt/tomcat/conf/new_keystore.jks"
    keystorePass="changeit"
    keyAlias="tomcat"
    sslProtocol="TLS" />
```

Check:
- `keystoreFile` → full path to new keystore
- `keystorePass` → password used during creation
- `keyAlias` → matches alias in keystore

---

## 6️⃣ Step 6: Set Permissions

```bash
chown tomcat:tomcat /opt/tomcat/conf/new_keystore.jks
chmod 600 /opt/tomcat/conf/new_keystore.jks
```

---

## 7️⃣ Step 7: Test Before Restart

If you have staging Tomcat, test there first.  
If not, run Tomcat temporarily on another port (e.g., 8444) and test SSL:
```bash
openssl s_client -connect yourdomain:8444
```

---

## 8️⃣ Step 8: Restart Tomcat

```bash
systemctl restart tomcat
```
Or if manually installed:
```bash
/opt/tomcat/bin/shutdown.sh
/opt/tomcat/bin/startup.sh
```

---

## 9️⃣ Step 9: Verify New SSL

```bash
openssl s_client -connect yourdomain:443 | openssl x509 -noout -dates -subject -issuer
```

---

## 🔟 Step 10: Clean Up

After a few days of no issues:
```bash
rm /opt/tomcat/conf/keystore_old_*.jks
```

---

✅ **Zero-Downtime Tip**:  
If Tomcat is behind an AWS ALB or Nginx reverse proxy, upload the new SSL there first to avoid user downtime.

---

**Author:** Vishwa
**Date:** $(date +%F)
