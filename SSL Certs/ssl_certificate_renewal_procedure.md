
# SSL Certificate Renewal Procedure – One-Way and Two-Way SSL (Annual Process)

---

## Overview  
SSL certificates have a limited validity period (usually 1 year or 2 years). Companies must renew certificates before expiry to maintain secure communications and avoid service interruptions. This guide covers the **end-to-end renewal process** including key generation, CSR creation, certificate issuance, installation, and verification — ensuring **zero downtime** in production environments.

---

## Prerequisites  
- Access to the server where SSL certificates are installed (web servers, app servers).  
- Access to Certificate Authority (CA) portal or your internal CA system.  
- Backup of current private key and certificates.  
- Maintenance window planned if needed, but process aims to avoid downtime.  

---

# Part 1: Preparation

### 1. Backup Existing Certificates and Keys  
- Backup the current private key (`server.key`), certificate (`server.crt`), and intermediate CA certificates.  
- For Java apps, backup keystore/truststore files (`.jks`, `.p12`).

### 2. Check Certificate Expiry  
- Use commands like:
  ```bash
  openssl x509 -in server.crt -noout -dates
  ```
- Confirm certificate expiry date to plan renewal well in advance (at least 2 weeks before expiry).

---

# Part 2: Generate New Private Key and CSR

### Option 1: Generate New Key Pair (Recommended for Security)  
- Generate a new private key:
  ```bash
  openssl genrsa -out new_server.key 2048
  ```
- Generate a new CSR using the new key:
  ```bash
  openssl req -new -key new_server.key -out new_server.csr -subj "/CN=your.domain.com"
  ```
- Keep `new_server.key` secure and **never share** it.

### Option 2: Use Existing Private Key (If required by policy)  
- Generate CSR with existing private key:
  ```bash
  openssl req -new -key server.key -out new_server.csr -subj "/CN=your.domain.com"
  ```

---

# Part 3: Submit CSR to Certificate Authority (CA)

- Submit the `new_server.csr` file to your CA (public or internal).  
- Complete domain validation as required (email, DNS TXT, or file-based).  
- Receive the renewed SSL certificate (`new_server.crt`) and intermediate certificates from CA.

---

## Handling Renewed SSL Certificate: Converting Renewed Cert to PKCS12 and Creating JKS

---

## Step-by-Step Flow

1. **Receive renewed SSL certificate** from the CA (usually in `.crt` or `.pem` format).

2. **Ensure you have your original private key** used during CSR generation (`server.key`).

3. **Convert the renewed certificate and private key into a PKCS12 (.p12) file:**

```bash
openssl pkcs12 -export \
  -in renewed_server.crt \
  -inkey server.key \
  -out server.p12 \
  -name tomcat-alias \
  -CAfile ca_bundle.crt \
  -caname root
```
This creates a .p12 file bundling your private key, renewed cert, and CA chain.

### Create Java Keystore (JKS) from the PKCS12 file:
```bash
keytool -importkeystore \
  -deststorepass changeit \
  -destkeypass changeit \
  -destkeystore keystore.jks \
  -srckeystore server.p12 \
  -srcstoretype PKCS12 \
  -srcstorepass <p12-password> \
  -alias tomcat-alias
```
Replace passwords as needed.

### This imports the PKCS12 content into a keystore.jks for Java apps like Tomcat.

Verify the JKS keystore contents:

```bash
keytool -list -v -keystore keystore.jks -storepass changeit
```
Update your application server config (e.g., Tomcat) to use the new keystore.jks.

Restart the server to apply the renewed certificate.

### Summary:
Renewed cert (.crt) + private key (.key) → convert to PKCS12 (.p12) → import PKCS12 to JKS (keystore.jks) → configure server

This process ensures your Java applications securely use the renewed SSL certificate with the private key, in the required keystore format.

# Part 4: Install Renewed Certificate – Zero Downtime Approach

### For One-Way SSL (Web Servers, APIs)

1. **Prepare certificate files:**  
   - `new_server.crt` (renewed certificate)  
   - Intermediate CA certificates (often combined into a bundle `ca_bundle.crt`)

2. **Upload to server:**  
   - Place `new_server.crt`, `new_server.key` (or existing key), and `ca_bundle.crt` in SSL directory.

3. **Configure server for new certificate (test config):**

   - **Apache HTTPD:**
     ```apache
     SSLCertificateFile /path/to/new_server.crt
     SSLCertificateKeyFile /path/to/new_server.key
     SSLCertificateChainFile /path/to/ca_bundle.crt
     ```
   - **Nginx:**
     ```nginx
     ssl_certificate /path/to/new_server.crt;
     ssl_certificate_key /path/to/new_server.key;
     ssl_trusted_certificate /path/to/ca_bundle.crt;
     ```
   - **Tomcat (Java apps):**  
     - Convert PEM to PKCS12 (if needed):  
       ```bash
       openssl pkcs12 -export -in new_server.crt -inkey new_server.key -out server.p12 -name tomcat
       ```
     - Update keystore and restart Tomcat with new keystore.

4. **Reload/Restart server gracefully:**  
   - Use graceful reload commands that do not drop active connections.  
   - Examples:  
     ```bash
     sudo systemctl reload nginx
     sudo apachectl graceful
     sudo systemctl restart tomcat
     ```

5. **Verify installation:**  
   - Check with:  
     ```bash
     openssl s_client -connect your.domain.com:443 -showcerts
     ```
   - Use online SSL checker tools (e.g., SSL Labs).  
   - Confirm new expiry date is reflected.

---

### For Two-Way (Mutual) SSL

In addition to above steps:

1. **Renew both server and client certificates:**  
   - Repeat CSR generation and renewal for client certificates if managed internally or by partner.

2. **Update truststores and keystores:**  
   - Import renewed certificates into truststore and keystore as applicable.  
   - For Java keystores, use:  
     ```bash
     keytool -import -alias partnerCA -file partnerCA.pem -keystore truststore.jks
     ```
   - Restart client and server apps to pick updated truststore.

3. **Test client-server mutual authentication:**  
   - Use `openssl s_client` with client certs to verify handshake.  
   - Validate logs for successful client cert validation.

---

# Part 5: Post-Renewal Monitoring and Validation

- Monitor SSL expiry regularly using monitoring tools (Prometheus, Nagios, etc.).  
- Validate logs for handshake errors or failed connections.  
- Inform stakeholders about renewal completion.  
- Update documentation with new certificate details.

---

# Best Practices for SSL Renewal

- Always generate a **new private key** for improved security unless restricted by policy.  
- Automate renewals where possible (e.g., Let’s Encrypt with Certbot).  
- Test certificate renewals on staging before production rollout.  
- Keep backups of all keys and certificates securely.  
- Schedule renewal well before expiry (at least 2 weeks).  
- Use OCSP stapling and strong cipher suites in SSL config.  
- Coordinate with partners in case of two-way SSL for synchronized renewal.

---

# Summary Flowchart

```
Backup Existing Certs & Keys
         ↓
Generate New Private Key & CSR
         ↓
Submit CSR to CA & Validate Domain
         ↓
Receive New Certificate & Intermediate Certs
         ↓
Upload & Configure New Cert on Servers
         ↓
Gracefully Reload/Restart Services
         ↓
Validate New Cert Installation & Expiry
         ↓
Monitor & Document Renewal
```

---

*This document provides a clear, step-by-step procedure to renew SSL certificates annually without causing downtime in production environments, covering both one-way and two-way SSL.*

---
