
# Replacing Old SSL Certificate in Nginx (xyz.domain.com)

This guide explains how to replace an old SSL certificate for Nginx with minimal downtime.

---

## 1️⃣ Step 1: Locate Existing SSL Config

Nginx SSL configuration is usually in one of the following files:
- `/etc/nginx/nginx.conf`
- `/etc/nginx/conf.d/xyz.domain.com.conf`
- `/etc/nginx/sites-enabled/xyz.domain.com`

Check for current certificate paths:
```bash
grep -i "ssl_certificate" /etc/nginx/conf.d/*.conf /etc/nginx/sites-enabled/* 2>/dev/null
```
Example output:
```
ssl_certificate     /etc/nginx/ssl/xyz.domain.com.crt;
ssl_certificate_key /etc/nginx/ssl/xyz.domain.com.key;
ssl_trusted_certificate /etc/nginx/ssl/ca-bundle.crt;
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
cp /etc/nginx/ssl/xyz.domain.com.crt /etc/nginx/ssl/xyz.domain.com.crt.old_$(date +%F)
cp /etc/nginx/ssl/xyz.domain.com.key /etc/nginx/ssl/xyz.domain.com.key.old_$(date +%F)
cp /etc/nginx/ssl/ca-bundle.crt /etc/nginx/ssl/ca-bundle.crt.old_$(date +%F)
```

---

## 4️⃣ Step 4: Replace Certificates

Copy new files to the correct locations:
```bash
cp new_xyz.domain.com.crt /etc/nginx/ssl/xyz.domain.com.crt
cp new_xyz.domain.com.key /etc/nginx/ssl/xyz.domain.com.key
cp new_ca-bundle.crt /etc/nginx/ssl/ca-bundle.crt
```

Set correct permissions:
```bash
chown root:root /etc/nginx/ssl/xyz.domain.com.crt /etc/nginx/ssl/ca-bundle.crt
chown root:root /etc/nginx/ssl/xyz.domain.com.key
chmod 644 /etc/nginx/ssl/xyz.domain.com.crt /etc/nginx/ssl/ca-bundle.crt
chmod 600 /etc/nginx/ssl/xyz.domain.com.key
```

---

## 5️⃣ Step 5: Verify Nginx Config

Run:
```bash
nginx -t
```
Expected output:
```
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

---

## 6️⃣ Step 6: Reload Nginx

```bash
systemctl reload nginx
```
Reloading avoids full downtime. If reload fails, restart:
```bash
systemctl restart nginx
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

If Nginx is behind AWS ALB, CloudFront, or another proxy, upload the new SSL there first to avoid downtime.

---

**Author:** Vishwa  
**Date:** $(date +%F)
