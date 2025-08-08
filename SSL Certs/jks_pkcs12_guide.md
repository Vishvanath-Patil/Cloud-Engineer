# 🔐 JKS & PKCS12 Keystore Management Guide

## 📌 Overview

This guide provides **ready-to-use keytool commands** for creating and
managing **Java Keystores (JKS & PKCS12)** for SSL/TLS.

------------------------------------------------------------------------

## 🛠 Prerequisites

-   Java JDK installed (`keytool` available in PATH)
-   Basic knowledge of SSL/TLS certificates
-   Access to **Root CA**, **Intermediate CA**, and **Server/SSL**
    certificates
-   Optional: Demo CA like <https://getacert.com/>

------------------------------------------------------------------------

## ⚠ Important Notes

-   Always **back up your keystore** before importing/deleting
    certificates.
-   Alias names must be **unique** in a keystore.
-   Ensure **password complexity** for production use.
-   `.jks` and `.pkcs12` formats are **interchangeable** via
    `keytool -importkeystore`.

------------------------------------------------------------------------

## 1️⃣ Create JKS Keystore

``` bash
keytool -genkey -alias test -keyalg RSA -keysize 2048 -keypass test123 -keystore mykeystore.jks -storepass test321 -sigalg SHA256withRSA -validity 360 -dname "CN=localhost, OU=IT, O=DG, L=XYZ, ST=Karnataka,C=IN"
```

### Self-Signed Certificate

``` bash
# Export Certificate 
keytool -export -alias test -file selfsign.cer -keystore mykeystore.jks -storepass test321  

# Import Certificate
keytool -import -v -trustcacerts -alias servercert -file selfsign.cer -keystore mykeystore.jks -storepass test321 -keypass test123           
```

### View Certificates

``` bash
keytool -list -v -keystore mykeystore.jks -storepass test321
```

### CA-Signed Certificate Process

``` bash
# Generate CSR
keytool -certreq -v -alias test -file request.csr -sigalg SHA256withRSA -keypass test123 -storepass test321 -keystore mykeystore.jks     
```

#### Certificates from CA:

1.  Server/SSL (Personal) Certificate → Import in identity store\
2.  Intermediate Certificate → Import in trust store\
3.  Root Certificate → Import in trust store

#### Import Certificates

``` bash
# Import Root Certificate 
keytool -import -v -trustcacerts -alias rootcacert -file getacert.cer -keystore mykeystore.jks -storepass test321

# Import Intermediate Certificate 
keytool -import -v -trustcacerts -alias intercert -file inter.cer -keystore mykeystore.jks -storepass test321

# Import Server Certificate 
keytool -import -v -alias test -file localhost-2024-08-22-050449.cer -keystore mykeystore.jks -keypass test123 -storepass test321
```

### Delete Certificate

``` bash
keytool -delete -alias rootcacert -keystore mykeystore.jks -storepass test321
```

------------------------------------------------------------------------

## 2️⃣ Create PKCS12 Keystore

``` bash
keytool -genkey -alias test -keyalg RSA -keysize 2048 -keypass test123 -storetype PKCS12 -keystore mykeystore.pkcs12 -storepass test123 -sigalg SHA256withRSA -validity 360 -dname "CN=localhost, OU=IT, O=DG, L=XYZ, ST=Karnataka,C=IN"
```

### View Certificates

``` bash
keytool -list -v -keystore mykeystore.pkcs12 -storepass test123
```

### Self-Signed Certificate

``` bash
# Export
keytool -export -alias test -file selfsign.cer -keystore mykeystore.pkcs12 -storepass test123            

# Import
keytool -import -v -trustcacerts -alias servercert -file selfsign.cer -keystore mykeystore.pkcs12 -storepass test123 -keypass test123
```

### CA-Signed Certificate Process

``` bash
# Generate CSR
keytool -certreq -v -alias test -file request.csr -sigalg SHA256withRSA -keypass test123 -storepass test123 -storetype PKCS12 -keystore mykeystore.pkcs12    
```

#### Import Certificates

``` bash
# Root Certificate
keytool -import -v -trustcacerts -alias rootcacert -file getacert.cer -storetype PKCS12 -keystore mykeystore.pkcs12 -storepass test123

# Intermediate Certificate
keytool -import -v -trustcacerts -alias intercert -file inter.cer -storetype PKCS12 -keystore mykeystore.pkcs12 -storepass test123

# Server Certificate
keytool -import -v -alias test -file localhost-2024-08-22-072327.cer -storetype PKCS12 -keystore mykeystore.pkcs12 -keypass test123 -storepass test123
```

### Delete Certificate

``` bash
keytool -delete -alias rootcacert -keystore mykeystore.pkcs12 -storepass test123
```
