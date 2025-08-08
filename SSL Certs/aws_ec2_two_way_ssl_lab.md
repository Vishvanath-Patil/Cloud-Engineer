# Lab Exercise: Practice Two-Way SSL (Mutual SSL) on AWS EC2 — Partner API Integration

---

## Lab Objective

Configure Two-Way SSL between two AWS EC2 Linux instances simulating:

- **Server EC2**: Hosts a secure API with mutual SSL using Nginx.
- **Client EC2**: Acts as a trusted partner client connecting with a client certificate.

You will generate keys, sign certificates, configure trust, and test secure communication.

---

## Lab Setup Requirements

- 2 AWS EC2 instances running Amazon Linux 2 or Ubuntu.
- Both have OpenSSL and Nginx installed.
- Security group rules allowing port 443 TCP inbound on server.
- Basic Linux command line skills.

---

## Step 1: Prepare the Server EC2 (API Server)

### 1. Install Nginx and OpenSSL

```bash
sudo yum update -y
sudo yum install nginx openssl -y
```
Note:
Nginx will be the web server handling SSL/TLS connections, and OpenSSL provides tools for generating keys and certificates.

2. Generate Server Private Key & CSR
```bash
openssl genrsa -out /etc/nginx/ssl/server.key 2048
openssl req -new -key /etc/nginx/ssl/server.key -out /etc/nginx/ssl/server.csr -subj "/CN=api-server.internal"
```
Note:
The private key is a secret used for encryption; the CSR (Certificate Signing Request) contains the public key and information about the server, which will be signed by the CA to create a trusted certificate.

3. Generate Your Own CA (Self-Signed) to Sign Certificates
```bash
openssl genrsa -out /etc/nginx/ssl/myCA.key 4096
openssl req -x509 -new -nodes -key /etc/nginx/ssl/myCA.key -sha256 -days 3650 -out /etc/nginx/ssl/myCA.pem -subj "/CN=MyRootCA"
```
Note:
You create your own Certificate Authority (CA) here which will act as the trusted entity signing both server and client certificates. This simulates a private CA in the lab.

4. Sign Server CSR with Your CA
```bash
openssl x509 -req -in /etc/nginx/ssl/server.csr -CA /etc/nginx/ssl/myCA.pem -CAkey /etc/nginx/ssl/myCA.key -CAcreateserial -out /etc/nginx/ssl/server.crt -days 365 -sha256
```
Note:
This step signs the server CSR with your CA, creating a certificate (server.crt) trusted by any system that trusts your CA (myCA.pem).

5. Copy myCA.pem to partnerCA.pem
```bash
cp /etc/nginx/ssl/myCA.pem /etc/nginx/ssl/partnerCA.pem
```
Note:
We simulate the partner’s CA certificate by copying the CA cert and using it as the trusted CA on the server side for verifying client certificates.

6. Configure Nginx for Two-Way SSL
Create or edit /etc/nginx/conf.d/api_server.conf:

```bash

server {
    listen 443 ssl;
    server_name api-server.internal;

    ssl_certificate /etc/nginx/ssl/server.crt;
    ssl_certificate_key /etc/nginx/ssl/server.key;

    ssl_client_certificate /etc/nginx/ssl/partnerCA.pem;  # Trust this CA for client certs
    ssl_verify_client on;  # Enforce clients to provide a valid cert signed by above CA

    location / {
        return 200 'Mutual SSL Authentication Successful\n';
    }
}
```
Note:
This configuration requires clients to present certificates signed by the trusted partner CA. If a client does not, the connection will be refused.

7. Start and Enable Nginx
```bash
sudo systemctl enable nginx
sudo systemctl restart nginx
```
Step 2: Prepare Client EC2 (Partner Client)
1. Install OpenSSL and Curl
```bash
sudo yum install openssl curl -y
```
2. Generate Client Key & CSR
```bash
mkdir ~/client_certs && cd ~/client_certs
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr -subj "/CN=partner-client"
```
Note:
The client also generates its own private key and CSR to request a client certificate from the CA.

3. Transfer client.csr to Server EC2
```bash
scp client.csr ec2-user@<server-ec2-ip>:/home/ec2-user/
```
Note:
You send the client CSR to the CA (your server EC2) to be signed.

4. On Server EC2: Sign Client CSR with Your CA
```bash
openssl x509 -req -in /home/ec2-user/client.csr -CA /etc/nginx/ssl/myCA.pem -CAkey /etc/nginx/ssl/myCA.key -CAcreateserial -out /home/ec2-user/client.crt -days 365 -sha256
```
Note:
The CA signs the client CSR, generating a client certificate.

5. Transfer client.crt and CA Cert back to Client EC2
```bash
scp ec2-user@<server-ec2-ip>:/home/ec2-user/client.crt ~/client_certs/
scp ec2-user@<server-ec2-ip>:/etc/nginx/ssl/myCA.pem ~/client_certs/partnerCA.pem
```
Note:
Client must have the signed client certificate and the CA certificate to verify the server during connection.

Step 3: Test Mutual SSL
```bash
curl -vk https://<server-ec2-ip> --cert ~/client_certs/client.crt --key ~/client_certs/client.key --cacert ~/client_certs/partnerCA.pem
```
Note:
This command sends the client certificate and key to the server and verifies the server certificate using the CA cert. The -v flag shows verbose output to debug the SSL handshake.

Expected output:
Mutual SSL Authentication Successful

Step 4: Troubleshooting
Check Nginx logs on server EC2:
```bash
sudo tail -f /var/log/nginx/error.log
Verify certificates match their keys (openssl x509 -noout -modulus and openssl rsa -noout -modulus).
```

Ensure server config has ssl_verify_client on.

Confirm Security Group allows inbound TCP 443.

Use OpenSSL debug client:
```bash
openssl s_client -connect <server-ec2-ip>:443 -cert ~/client_certs/client.crt -key ~/client_certs/client.key -CAfile ~/client_certs/partnerCA.pem
```
Lab Summary Notes
Why generate your own CA?
To simulate a trusted Certificate Authority in your lab without needing a public CA.

What does ssl_verify_client on do?
It forces the server to request and verify a client certificate during the SSL handshake.

What is the purpose of the CA cert on the client?
It verifies the server’s certificate so the client can trust the server it connects to.

Why do we sign client and server certificates?
Signing by a trusted CA links the certificate to a trusted root, allowing verification and trust.

What if client does not present certificate or presents invalid one?
The server rejects the connection — the mutual authentication fails.
