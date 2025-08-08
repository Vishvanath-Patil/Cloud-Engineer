
# Replacing Old SSL Certificate in Apache HTTPD (xyz.domain.com)

This guide explains how to replace an old SSL certificate for Apache HTTPD with minimal downtime.

---

## 1️⃣ Step 1: Locate Existing SSL Config

Apache HTTPD SSL configuration is usually in one of the following files:
- `/etc/httpd/conf.d/ssl.conf` (CentOS/Red Hat)
- `/etc/apache2/sites-enabled/default-ssl.conf` (Ubuntu/Debian)
- `/etc/httpd/conf.d/xyz.domain.com.conf` (custom virtual host)

Check the config file for the current certificate paths:
```bash
grep -i "SSLCertificate" /etc/httpd/conf.d/*.conf
```
Example output:
```
SSLCertificateFile /etc/pki/tls/certs/xyz.domain.com.crt
SSLCertificateKeyFile /etc/pki/tls/private/xyz.domain.com.key
SSLCertificateChainFile /etc/pki/tls/certs/ca-bundle.crt
```

---

## 2️⃣ Step 2: Get New SSL Files from CA

From your certificate provider, you should have:
- **Private Key** → `xyz.domain.com.key` (from CSR)
- **Certificate** → `xyz.domain.com.crt` (signed by CA)
- **CA Bundle / Intermediate Cert** → `ca-bundle.crt`

⚠ **Important:** If the private key is missing, re-generate CSR and request a new cert.

---

## 3️⃣ Step 3: Backup Old Certificates

Before replacing:
```bash
cp /etc/pki/tls/certs/xyz.domain.com.crt /etc/pki/tls/certs/xyz.domain.com.crt.old_$(date +%F)
cp /etc/pki/tls/private/xyz.domain.com.key /etc/pki/tls/private/xyz.domain.com.key.old_$(date +%F)
cp /etc/pki/tls/certs/ca-bundle.crt /etc/pki/tls/certs/ca-bundle.crt.old_$(date +%F)
```

---

## 4️⃣ Step 4: Replace Certificates

Copy new files to the correct locations (adjust paths if needed):
```bash
cp new_xyz.domain.com.crt /etc/pki/tls/certs/xyz.domain.com.crt
cp new_xyz.domain.com.key /etc/pki/tls/private/xyz.domain.com.key
cp new_ca-bundle.crt /etc/pki/tls/certs/ca-bundle.crt
```

Set correct permissions:
```bash
chown root:root /etc/pki/tls/certs/xyz.domain.com.crt /etc/pki/tls/certs/ca-bundle.crt
chown root:root /etc/pki/tls/private/xyz.domain.com.key
chmod 644 /etc/pki/tls/certs/xyz.domain.com.crt /etc/pki/tls/certs/ca-bundle.crt
chmod 600 /etc/pki/tls/private/xyz.domain.com.key
```

---

## 5️⃣ Step 5: Verify Apache Config

Run:
```bash
apachectl configtest
```
Expected output:
```
Syntax OK
```

---

## 6️⃣ Step 6: Reload Apache

```bash
systemctl reload httpd   # CentOS/RedHat
systemctl reload apache2 # Ubuntu/Debian
```

Reloading avoids full downtime. If reload fails, restart:
```bash
systemctl restart httpd
```

---

## 7️⃣ Step 7: Verify New SSL

From local machine:
```bash
openssl s_client -connect xyz.domain.com:443 | openssl x509 -noout -dates -subject -issuer
```

From browser: Visit https://xyz.domain.com and check the certificate details.

---

## 🔹 Zero-Downtime Tip

If Apache is behind AWS ALB, CloudFront, or Nginx, update SSL there first before changing on Apache to ensure no service interruption.

---

**Author:** Vishwa
**Date:** $(date +%F)
