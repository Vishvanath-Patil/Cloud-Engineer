# PM2 User Setup Guide

This guide helps you move all PM2 Node.js services from **root** to specific user accounts
(like `avinash` and `chandra`), ensuring proper permissions and startup on reboot.

---

## 🧩 Step 1: Stop PM2 services running as root

Run the following commands as **root**:

```bash
pm2 stop all
pm2 delete all
pm2 kill
```

Then confirm that no Node processes are running under root:

```bash
ps -ef | grep node
```

If you still see any, stop them manually:

```bash
kill -9 <PID>
```

---

## 🧩 Step 2: Assign proper ownership to project directories

Ensure each project directory belongs to its respective user:

```bash
chown -R avinash:avinash /product/tops/topsServer
chown -R chandra:chandra /product/tops/topsServer
```

*(Replace `chandra` with the correct username truncated as “Cha…” in your environment.)*

---

## 🧩 Step 3: Start PM2 apps as the respective users

### For user **avinash**

Run these commands as **root** (they will switch to `avinash` automatically):

```bash
su - avinash -c 'pm2 start /product/tops/topsServer/compliance/src/index.js --name Compliance'
su - avinash -c 'pm2 start /product/tops/topsServer/ticket-service/src/app.js --name ticket-service'
su - avinash -c 'pm2 start /product/tops/topsServer/bizops/src/index.js --name Bizops'
su - avinash -c 'pm2 start /product/tops/topsServer/liquidity-dashboard/src/index.js --name Liquidity'
su - avinash -c 'pm2 start /product/tops/topsServer/partnerOnBoarding/index.js --name PartnerOnBoarding'
su - avinash -c 'pm2 start /product/tops/topsServer/document-management-service/src/index.js --name document-manage-service'
su - avinash -c 'pm2 save'
```

---

### For user **chandra**

Run these commands as **root**:

```bash
su - chandra -c 'pm2 start /product/tops/topsServer/treasury/src/index.js --name Treasury'
su - chandra -c 'pm2 save'
```

---

## 🧩 Step 4: Enable PM2 auto-start on reboot

Run these commands as **root** to configure systemd startup for each user:

```bash
pm2 startup systemd -u avinash --hp /home/avinash
pm2 startup systemd -u chandra --hp /home/chandra
```

When PM2 prints the generated command (like the example below), **run that command**:

```bash
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u avinash --hp /home/avinash
```

---

## 🧩 Step 5: Verify services

Check that all services are running correctly under the right users:

```bash
su - avinash -c 'pm2 status'
su - chandra -c 'pm2 status'
```

And confirm no processes are running as root:

```bash
ps -ef | grep node
```

Expected output (example):

| user     | process                         | status  |
|-----------|----------------------------------|----------|
| avinash   | Bizops, Compliance, Liquidity, Ticket-service, PartnerOnBoarding, Document-manage-service | online |
| chandra   | Treasury                        | online  |
| root      | — (none)                        | —        |

---

## ✅ Final Checks

- Run `pm2 save` for each user once all apps are online.  
- Run `systemctl enable pm2-avinash` and `systemctl enable pm2-chandra` to auto-start on boot.  
- Confirm after reboot with:

```bash
su - avinash -c 'pm2 status'
su - chandra -c 'pm2 status'
```

---

**Now all your PM2 apps will run under their respective users (not root), exactly as shown in your screenshot.**
