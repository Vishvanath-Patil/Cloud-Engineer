
# Two-Way SSL Sample Configuration Files for Apache/Nginx/Java Apps

---

## 📌 Scenario: Partner API Integration

You run an API server (`api.example.com`) and want only a trusted partner client to access your API via HTTPS with mutual SSL authentication.

- Your server presents its certificate to the client.
- The client (partner) presents its client certificate.
- Both authenticate each other.
- You maintain trust via CA certificates exchanged.

---

## Step 1: Prerequisites

- Server private key and CSR generated.
- Client private key and CSR generated.
- CA certificates to sign partner/server CSRs.
- Certificates exchanged and signed properly.
- Both server and client configured to trust each other’s CA.

---

## Step 2: Generate Server Keys & CSR (Example)

```bash
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=api.example.com"
```

Send `server.csr` to partner CA to sign and get `server.crt`.

---

## Step 3: Generate Client Keys & CSR (Example)

Partner generates:

```bash
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr -subj "/CN=partner-client"
```

Partner sends `client.csr` to your CA, you sign it:

```bash
openssl x509 -req -in client.csr -CA yourCA.pem -CAkey yourCA.key -CAcreateserial -out client.crt -days 365 -sha256
```

Partner installs `client.crt` and trusts your `yourCA.pem`.

---

## Step 4: Sample Configuration for Servers

### 1. Apache HTTPD (`/etc/httpd/conf.d/ssl.conf` or custom conf)

```apache
<VirtualHost *:443>
    ServerName api.example.com

    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/server.crt
    SSLCertificateKeyFile /etc/ssl/private/server.key

    # CA cert to validate client certs
    SSLCACertificateFile /etc/ssl/certs/partnerCA.pem

    # Require and verify client certificate
    SSLVerifyClient require
    SSLVerifyDepth 2

    # Optional SSL protocols & ciphers
    SSLProtocol all -SSLv3 -TLSv1
    SSLCipherSuite HIGH:!aNULL:!MD5

    <Location />
        ProxyPass http://localhost:8080/
        ProxyPassReverse http://localhost:8080/
    </Location>
</VirtualHost>
```

Restart Apache:

```bash
systemctl restart httpd
```

---

### 2. Nginx (`/etc/nginx/conf.d/api.example.com.conf`)

```nginx
server {
    listen 443 ssl;
    server_name api.example.com;

    ssl_certificate /etc/ssl/certs/server.crt;
    ssl_certificate_key /etc/ssl/private/server.key;

    ssl_client_certificate /etc/ssl/certs/partnerCA.pem;  # Partner CA to validate client certs
    ssl_verify_client on;  # Enforce client authentication

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Test and restart Nginx:

```bash
nginx -t
systemctl restart nginx
```

---

### 3. Tomcat (`server.xml`)

First, convert the server certificate and key to PKCS12 format:

```bash
openssl pkcs12 -export -in server.crt -inkey server.key -out server.p12 -name tomcat
```

Create a truststore and import partner CA certificate:

```bash
keytool -import -trustcacerts -alias partnerCA -file partnerCA.pem -keystore truststore.jks
```

Edit Tomcat `conf/server.xml` to enable mutual SSL:

```xml
<Connector port="8443" protocol="org.apache.coyote.http11.Http11NioProtocol"
    maxThreads="200" SSLEnabled="true" scheme="https" secure="true"
    keystoreFile="/path/to/server.p12"
    keystoreType="PKCS12"
    keystorePass="your_keystore_password"
    truststoreFile="/path/to/truststore.jks"
    truststorePass="your_truststore_password"
    clientAuth="true"
    sslProtocol="TLS"/>
```

Restart Tomcat:

```bash
systemctl restart tomcat
```

---

## Step 5: Testing Client Connection

### Using `curl` with client certificate:

```bash
curl -vk https://api.example.com --cert client.crt --key client.key
```

### Using OpenSSL:

```bash
openssl s_client -connect api.example.com:443 -cert client.crt -key client.key -CAfile yourCA.pem
```

---

## Step 6: Troubleshooting Tips

- Ensure server requests client certs (`ssl_verify_client on` in Nginx, `SSLVerifyClient require` in Apache, `clientAuth="true"` in Tomcat).
- Check certificate validity and trust chain on both client and server.
- Use logs:
  - Nginx: `/var/log/nginx/error.log`
  - Apache: `/var/log/httpd/ssl_error_log`
  - Tomcat: `logs/catalina.out`
- Verify private keys correspond to certificates.
- Check client certificates are signed by CA trusted by server.
- Test with OpenSSL to see handshake details.

---

If you want, I can prepare ready-to-use sample cert/key files or scripts to generate them.

---

Would you like me to provide those or help with any particular server?
