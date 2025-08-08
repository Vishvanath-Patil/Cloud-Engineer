
# SSL/TLS JKS (Java Keystore) Scenarios Guide

This document provides **real-world scenarios** for working with Java Keystores (JKS) in SSL/TLS contexts.

---
## 📌 Overview
This document provides **real-world scenarios** for working with Java Keystores (JKS) in SSL/TLS contexts.

---

## 1️⃣ Scenario: Import a Public Certificate into a Truststore
**Use Case:** You need your Java application to trust an external server's certificate.

```bash
keytool -import -trustcacerts -alias external-server -file server.crt -keystore truststore.jks -storepass changeit
```
📝 Notes:

- `truststore.jks` is used for trusting external servers.

- Always verify the certificate fingerprint before importing.
  
---
## 2️⃣ Scenario: Import PKCS12 Keystore into JKS
**Use Case:** You received a .p12 file from a CA and need to use it in a Java app.

```bash
keytool -importkeystore -srckeystore keystore.p12 -srcstoretype pkcs12 -destkeystore keystore.jks -deststoretype jks
```
📝 Notes:

- `keystore.jks` stores private keys and their certificates.

- Passwords for source and destination stores may differ.
  
---
## 3️⃣ Scenario: Create a New Keystore with Private Key and Cert
**Use Case:** You have a private key (.key) and a signed certificate (.crt) and want them in a JKS.

```bash
# Step 1: Convert to PKCS12
openssl pkcs12 -export -in certificate.crt -inkey private.key -out keystore.p12 -name myalias

# Step 2: Convert PKCS12 to JKS
keytool -importkeystore -srckeystore keystore.p12 -srcstoretype pkcs12 -destkeystore keystore.jks -deststoretype jks
```
## 4️⃣ Scenario: View Contents of a JKS
**Use Case:** You want to check what aliases and certs are inside a keystore.

```bash
keytool -list -v -keystore keystore.jks -storepass changeit
```
## 5️⃣ Scenario: Change JKS Password
**Use Case:** Rotate keystore password for security.

```bash
keytool -storepasswd -new newpassword -keystore keystore.jks -storepass oldpassword
```
## 6️⃣ Scenario: Export Certificate from JKS
**Use Case:** You want to share your public certificate with a partner.

```bash
keytool -export -alias myalias -keystore keystore.jks -rfc -file public_cert.crt -storepass changeit
```
## 7️⃣ Scenario: Remove a Certificate from Truststore
**Use Case:** A partner’s certificate expired or integration ended.

```bash
keytool -delete -alias partner-cert -keystore truststore.jks -storepass changeit
```














