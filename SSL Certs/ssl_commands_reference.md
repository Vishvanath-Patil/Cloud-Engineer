# SSL/TLS Certificate Commands Reference Guide

## 📌 Overview
This guide provides **all essential commands** related to SSL/TLS certificates including:
- Private key generation
- CSR creation
- Self-signed certificates
- Format conversions
- Keystore management (PKCS12, JKS)
- CA and truststore creation
- Certificate inspection

---

## 🛠 Prerequisites
- **OpenSSL** installed (`openssl version`)
- **Java keytool** installed (`keytool -version`)
- Basic Linux shell access
- Secure file permissions (`chmod 600` for sensitive files)

> ⚠ **Note:** Always protect private keys and use secure transfer methods (SFTP, encrypted email).

---

## 1️⃣ Generate a Private Key
```bash
# RSA 2048-bit private key
openssl genrsa -out private.key 2048

# RSA 4096-bit private key (more secure)
openssl genrsa -out private.key 4096
```

---

## 2️⃣ Create a CSR (Certificate Signing Request)
```bash
openssl req -new -key private.key -out request.csr -subj "/C=US/ST=California/L=LA/O=ExampleOrg/OU=IT/CN=example.com"
```

> 📄 **CSR file** is what you send to a CA (Certificate Authority) for signing.

---

## 3️⃣ Generate a Self-Signed Certificate
```bash
openssl req -x509 -new -nodes -key private.key -sha256 -days 365 -out certificate.crt -subj "/CN=example.com"
```

---

## 4️⃣ View Certificate Details
```bash
openssl x509 -in certificate.crt -text -noout
```

---

## 5️⃣ Convert Certificate Formats

### PEM → DER
```bash
openssl x509 -in certificate.pem -outform der -out certificate.der
```

### DER → PEM
```bash
openssl x509 -in certificate.der -inform der -out certificate.pem
```

### PEM → PKCS12 (.p12 / .pfx)
```bash
openssl pkcs12 -export -in certificate.crt -inkey private.key -out keystore.p12 -name myalias
```

### PKCS12 → PEM
```bash
openssl pkcs12 -in keystore.p12 -clcerts -nokeys -out certificate.pem
openssl pkcs12 -in keystore.p12 -nocerts -nodes -out private.key
```

### PEM → JKS
```bash
# Convert PEM to PKCS12 first
openssl pkcs12 -export -in certificate.crt -inkey private.key -out keystore.p12 -name myalias

# Then import PKCS12 into JKS
keytool -importkeystore -srckeystore keystore.p12 -srcstoretype pkcs12 -destkeystore keystore.jks -deststoretype jks
```

---

## 6️⃣ Create Your Own CA (Certificate Authority)
```bash
openssl genrsa -out myCA.key 4096
openssl req -x509 -new -nodes -key myCA.key -sha256 -days 3650 -out myCA.pem -subj "/CN=MyRootCA"
```

---

## 7️⃣ Sign a CSR with Your CA
```bash
openssl x509 -req -in request.csr -CA myCA.pem -CAkey myCA.key -CAcreateserial -out signed_certificate.crt -days 365 -sha256
```

---

## 8️⃣ Create a Truststore from a CA Certificate
```bash
keytool -import -trustcacerts -alias myCA -file myCA.pem -keystore truststore.jks -storepass changeit
```

---

## 9️⃣ Extract Certificates from PKCS12
```bash
# Extract cert
openssl pkcs12 -in keystore.p12 -clcerts -nokeys -out extracted.crt

# Extract key
openssl pkcs12 -in keystore.p12 -nocerts -nodes -out extracted.key
```

---

## 🔟 Check CSR Details
```bash
openssl req -in request.csr -text -noout
```

---

## 1️⃣1️⃣ Verify Private Key and Certificate Match
```bash
# Check modulus of private key
openssl rsa -noout -modulus -in private.key | openssl md5

# Check modulus of certificate
openssl x509 -noout -modulus -in certificate.crt | openssl md5

# Check modulus of CSR
openssl req -noout -modulus -in request.csr | openssl md5
```

> ✅ All three hashes should match.

---

## 1️⃣2️⃣ Check Expiry Date of Certificate
```bash
openssl x509 -enddate -noout -in certificate.crt
```

---

## 📌 Notes & Best Practices
- Always **backup** certificates and keys securely.
- Use **strong key lengths** (≥ 2048 bits).
- Rotate keys and certificates regularly.
- Use **intermediate CAs** instead of signing directly with root CA in production.
- For Java applications, always keep the `truststore.jks` updated with partner CA certs.

---
