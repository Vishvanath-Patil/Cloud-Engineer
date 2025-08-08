# Two-Way (Mutual) SSL Authentication - Full Procedure with Partner CSR Exchange

## 📌 Overview
Two-way SSL (Mutual SSL) ensures **both server and client authenticate each other** using certificates.  
It is often used for:
- Secure API communication
- Internal system integration
- Payment gateway connections

This guide includes **real-world CSR exchange with a partner**.

---

## 1️⃣ Generate Your Own Certificate Authority (CA)
If not using a public CA, create your own CA to sign both server and client certs.

```bash
openssl genrsa -out myCA.key 4096
openssl req -x509 -new -nodes -key myCA.key -sha256 -days 3650 -out myCA.pem
```

**Files created:**
- `myCA.key` → Private key (keep safe!)
- `myCA.pem` → Public root certificate (shared for trust)

---

## 2️⃣ Partner CSR Exchange Flow

### A. Your Side (Server Owner)
1. Generate private key & CSR:
```bash
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=xyz.domain.com"
```
2. Send **server.csr** to your partner (never share `server.key`).
3. Partner signs it with their CA → returns `server.crt`.
4. Install:
   - `server.crt` (your server certificate signed by partner CA)
   - Partner's CA root certificate (`partnerCA.pem`) in your trust store.

---

### B. Partner Side (Client Owner)
1. Partner generates their own private key & CSR:
```bash
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr -subj "/CN=myclient"
```
2. Partner sends **client.csr** to you.
3. You sign it with your CA:
```bash
openssl x509 -req -in client.csr -CA myCA.pem -CAkey myCA.key -CAcreateserial -out client.crt -days 365 -sha256
```
4. Partner installs:
   - `client.crt` (client certificate signed by your CA)
   - Your CA root certificate (`myCA.pem`) in their trust store.

---

## 3️⃣ Typical File Exchange Table

| File Type         | Who Generates | Who Receives | Purpose |
|-------------------|--------------|--------------|---------|
| CSR (`.csr`)      | Server/Client | Other party  | Request for certificate signing |
| Certificate (`.crt` / `.cer`) | CA/Other party | Requestor | Actual signed identity |
| CA Root Cert (`.pem`) | CA owner | Other party  | To validate signatures |

---

## 4️⃣ Configure Nginx for Two-Way SSL
Edit `/etc/nginx/conf.d/xyz.domain.com.conf`:

```nginx
server {
    listen 443 ssl;
    server_name xyz.domain.com;

    ssl_certificate /etc/nginx/ssl/server.crt;
    ssl_certificate_key /etc/nginx/ssl/server.key;

    ssl_client_certificate /etc/nginx/ssl/partnerCA.pem;  # Partner CA cert to validate clients
    ssl_verify_client on;  # Enforce client auth

    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        root /var/www/html;
        index index.html;
    }
}
```

Apply changes:
```bash
nginx -t
systemctl restart nginx
```

---

## 5️⃣ Configure Apache HTTPD for Two-Way SSL
In `/etc/httpd/conf.d/ssl.conf`:

```apache
SSLEngine on
SSLCertificateFile /etc/httpd/ssl/server.crt
SSLCertificateKeyFile /etc/httpd/ssl/server.key

SSLCACertificateFile /etc/httpd/ssl/partnerCA.pem
SSLVerifyClient require
SSLVerifyDepth 2
```

Restart Apache:
```bash
systemctl restart httpd
```

---

## 6️⃣ Configure Tomcat for Two-Way SSL
Edit `server.xml`:

```xml
<Connector port="8443" protocol="org.apache.coyote.http11.Http11NioProtocol"
    maxThreads="200"
    scheme="https" secure="true" SSLEnabled="true"
    keystoreFile="/opt/tomcat/ssl/server.p12"
    keystoreType="PKCS12" keystorePass="changeit"
    clientAuth="true"
    truststoreFile="/opt/tomcat/ssl/truststore.p12"
    truststorePass="changeit"
    sslProtocol="TLS"/>
```

Convert server cert to PKCS12:
```bash
openssl pkcs12 -export -in server.crt -inkey server.key -out server.p12 -name tomcat
```

Import Partner CA into truststore:
```bash
keytool -import -trustcacerts -alias partnerCA -file partnerCA.pem -keystore truststore.p12
```

Restart Tomcat:
```bash
systemctl restart tomcat
```

---

## 7️⃣ Test Client Connection

**Using curl:**
```bash
curl -vk https://xyz.domain.com --cert client.crt --key client.key
```

**Using OpenSSL:**
```bash
openssl s_client -connect xyz.domain.com:443 -cert client.crt -key client.key
```

---

## 8️⃣ Troubleshooting
- Check Nginx logs:
```bash
tail -f /var/log/nginx/error.log
```
- Check Apache logs:
```bash
tail -f /var/log/httpd/ssl_error_log
```
- Check Tomcat logs:
```bash
tail -f /opt/tomcat/logs/catalina.out
```

---

## 9️⃣ Security Best Practices
- Use `TLSv1.2` or higher.
- Rotate certificates regularly.
- Store private keys securely with `chmod 600`.
- Use secure file transfer (SFTP, encrypted email) for CSR and cert exchanges.
- Always verify certificate fingerprints after receiving.

---

**Author:** Vishwa  
**Date:** 2025-08-08
