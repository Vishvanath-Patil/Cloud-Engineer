# Grafana Read-Only Dashboard Access Guide

This document outlines how to create users and restrict them to view-only access for specific dashboards in Grafana. It ensures teams such as SOC, TechOps, and Cloud have specific access to dashboards based on their roles.

---

## 👤 Step 1: Create Users

1. Go to **Server Admin > Users**
2. Click **+ New User**
3. Fill in user details for each team:
   - **SOC User**: soc_user / soc@example.com
   - **TechOps User**: techops_user / techops@example.com
   - **Cloud User**: cloud_user / cloud@example.com
4. Set a secure password and click **Create**

> All users are created with the default Org Role `Viewer`.

---

## 👥 Step 2: Create Teams

1. Go to **Server Admin > Teams**
2. Click **+ New Team** for each team:
   - Team Name: `SOC-Team`, add `soc_user`
   - Team Name: `TechOps-Team`, add `techops_user`
   - Team Name: `Cloud-Team`, add `cloud_user`

---

## 📁 Step 3: Create Dashboard Folders

Create folders to segregate dashboards:

- **SOC-Dashboards** for SOC team
- **TechOps-Dashboards** for TechOps team
- **Cloud-Dashboards** for Cloud team (can view all dashboards)

Go to **Dashboards > Manage > New Folder** and create each folder. Move dashboards to their respective folders.

---

## 🔐 Step 4: Configure Folder Permissions

### For SOC Team:
1. Go to `SOC-Dashboards > Settings > Permissions`
2. Remove `Everyone` if present
3. Add:
   - Team: `SOC-Team`
   - Role: `Viewer`

### For TechOps Team:
1. Go to `TechOps-Dashboards > Settings > Permissions`
2. Remove `Everyone`
3. Add:
   - Team: `TechOps-Team`
   - Role: `Viewer`

### For Cloud Team:
Give Cloud team viewer access to all folders:
1. Go to each folder's permissions
2. Add:
   - Team: `Cloud-Team`
   - Role: `Viewer`

You can skip removing `Everyone` if Cloud is meant to see everything.

---

## 🧪 Step 5: Test Access

Login as each user:
- `soc_user` should see only `SOC-Dashboards`
- `techops_user` should see only `TechOps-Dashboards`
- `cloud_user` should see all folders

---

## 🔄 Optional: Duplicate Dashboards for Public Access

If needed, duplicate a dashboard into a non-restricted folder:
1. Open a dashboard
2. Click **Save As**
3. Select a new folder (e.g., `General`, `Cloud-Dashboards`)

---

## 🔐 Summary Table
| Team      | Folder Access           | Role    |
|-----------|--------------------------|---------|
| SOC       | SOC-Dashboards           | Viewer  |
| TechOps   | TechOps-Dashboards       | Viewer  |
| Cloud     | All folders              | Viewer  |

---

**Author:** DevOps Team  
**Last Updated:** 2025-05-24
