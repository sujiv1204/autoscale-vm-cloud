# GCP Setup Guide (Both CLI and Console)

This guide provides instructions for setting up GCP resources using both **gcloud CLI** and the **GCP Web Console**.

---

## Prerequisites

- Active GCP account
- Billing enabled
- Project created

---

## Method 1: Using gcloud CLI (Recommended)

### 1. Install and Initialize gcloud CLI

```bash
# Install gcloud CLI
# Linux:
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize
gcloud init

# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### 2. Enable Required APIs

```bash
# Enable Compute Engine API
gcloud services enable compute.googleapis.com

# Enable Cloud Resource Manager API
gcloud services enable cloudresourcemanager.googleapis.com

# Verify
gcloud services list --enabled
```

### 3. Create GCP Instance

```bash
# Using the provisioning script
python3 scripts/gcp_provision.py

# OR manually
gcloud compute instances create autoscale-app-vm \
  --project=YOUR_PROJECT_ID \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=10GB \
  --boot-disk-type=pd-standard \
  --tags=http-server,https-server
```

### 4. Create Firewall Rules

```bash
# Allow traffic on port 5000
gcloud compute firewall-rules create allow-app-5000 \
  --allow=tcp:5000 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server \
  --description="Allow traffic on port 5000 for sample app"

# Verify
gcloud compute firewall-rules list
```

### 5. Set Up Budget Alerts

```bash
# List billing accounts
gcloud billing accounts list

# Create budget (requires billing account ID)
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Auto-Scale Project Budget" \
  --budget-amount=20USD \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.75 \
  --threshold-rule=percent=0.9
```

### 6. Useful Commands

```bash
# List instances
gcloud compute instances list

# Get instance details
gcloud compute instances describe autoscale-app-vm --zone=us-central1-a

# Get external IP
gcloud compute instances describe autoscale-app-vm \
  --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

# SSH into instance
gcloud compute ssh autoscale-app-vm --zone=us-central1-a

# Stop instance
gcloud compute instances stop autoscale-app-vm --zone=us-central1-a

# Start instance
gcloud compute instances start autoscale-app-vm --zone=us-central1-a

# Delete instance
gcloud compute instances delete autoscale-app-vm --zone=us-central1-a

# Delete firewall rule
gcloud compute firewall-rules delete allow-app-5000
```

---

## Method 2: Using GCP Web Console

### 1. Access GCP Console

1. Navigate to: https://console.cloud.google.com
2. Sign in with your Google account
3. Select or create your project

### 2. Enable Required APIs

1. Go to **Navigation Menu (☰)** → **APIs & Services** → **Library**
2. Search for "Compute Engine API"
3. Click on it and click **ENABLE**
4. Repeat for "Cloud Resource Manager API"

**Verification:**

- Go to **APIs & Services** → **Enabled APIs & services**
- Confirm both APIs are listed

### 3. Create VM Instance

1. Go to **Navigation Menu (☰)** → **Compute Engine** → **VM instances**
2. Click **CREATE INSTANCE**
3. Configure:
    - **Name:** `autoscale-app-vm`
    - **Region:** `us-central1`
    - **Zone:** `us-central1-a`
    - **Machine type:**
        - Series: E2
        - Machine type: e2-micro (2 vCPU, 1 GB memory)
    - **Boot disk:**
        - Click "CHANGE"
        - Operating system: Ubuntu
        - Version: Ubuntu 22.04 LTS
        - Boot disk type: Standard persistent disk
        - Size: 10 GB
        - Click "SELECT"
    - **Firewall:**
        - ☑ Allow HTTP traffic
        - ☑ Allow HTTPS traffic
    - **Management** tab → **Automation** → **Startup script:**
        ```bash
        #!/bin/bash
        apt-get update
        apt-get install -y docker.io
        systemctl start docker
        systemctl enable docker
        usermod -aG docker $(getent passwd 1000 | cut -d: -f1)
        apt-get install -y docker-compose
        ```
4. Click **CREATE**

**Wait for instance to be created (2-3 minutes)**

### 4. Create Firewall Rule

1. Go to **Navigation Menu (☰)** → **VPC network** → **Firewall**
2. Click **CREATE FIREWALL RULE**
3. Configure:
    - **Name:** `allow-app-5000`
    - **Description:** `Allow traffic on port 5000 for sample app`
    - **Logs:** Off
    - **Network:** default
    - **Priority:** 1000
    - **Direction of traffic:** Ingress
    - **Action on match:** Allow
    - **Targets:** Specified target tags
    - **Target tags:** `http-server`
    - **Source filter:** IPv4 ranges
    - **Source IPv4 ranges:** `0.0.0.0/0`
    - **Protocols and ports:**
        - ☑ TCP
        - Ports: `5000`
4. Click **CREATE**

### 5. Set Up Budget Alerts

1. Go to **Navigation Menu (☰)** → **Billing** → **Budgets & alerts**
2. Click **CREATE BUDGET**
3. **Scope:**
    - Select your project
    - Click **NEXT**
4. **Amount:**
    - Budget type: Specified amount
    - Target amount: $20
    - Click **NEXT**
5. **Actions:**
    - Set threshold rules:
        - 50% of budget
        - 75% of budget
        - 90% of budget
        - 100% of budget
    - ☑ Email alerts to billing admins and users
    - (Optional) Add additional email addresses
    - Click **FINISH**

### 6. Get Instance Information

**Via Console:**

1. Go to **Compute Engine** → **VM instances**
2. Find your instance `autoscale-app-vm`
3. Note the **External IP** address
4. Click **SSH** to connect via browser

**Via gcloud (after installation):**

```bash
gcloud compute instances list
```

### 7. Manage Instance via Console

**Stop Instance:**

1. Go to **Compute Engine** → **VM instances**
2. Check the box next to `autoscale-app-vm`
3. Click **STOP** at the top
4. Confirm

**Start Instance:**

1. Check the box next to stopped instance
2. Click **START**

**Delete Instance:**

1. Check the box next to instance
2. Click **DELETE**
3. Confirm

### 8. Monitor Costs

**View Current Spend:**

1. Go to **Navigation Menu (☰)** → **Billing** → **Reports**
2. View breakdown by:
    - Services
    - Projects
    - Time range

**View Detailed Billing:**

1. Go to **Billing** → **Transactions**
2. See all charges and credits

---

## Comparison: CLI vs Console

| Task               | gcloud CLI          | Web Console               |
| ------------------ | ------------------- | ------------------------- |
| **Speed**          | ⚡ Fast (seconds)   | 🐢 Slower (manual clicks) |
| **Automation**     | ✅ Yes (scriptable) | ❌ No                     |
| **Visibility**     | ⚠️ Terminal only    | ✅ Visual interface       |
| **Learning Curve** | 📈 Steeper          | 📉 Easier                 |
| **Repeatability**  | ✅ Perfect          | ⚠️ Manual                 |
| **Documentation**  | 📝 Required         | 👀 Self-explanatory       |

**Recommendation:**

- **For this project:** Use gcloud CLI (it's already integrated in the scripts)
- **For learning:** Try both methods to understand GCP better
- **For production:** Use CLI with Infrastructure as Code (Terraform)

---

## Quick Reference Card

### gcloud CLI Cheatsheet

```bash
# Configuration
gcloud config list
gcloud config set project PROJECT_ID
gcloud config set compute/zone us-central1-a

# Instances
gcloud compute instances list
gcloud compute instances create NAME --machine-type=e2-micro
gcloud compute instances stop NAME
gcloud compute instances start NAME
gcloud compute instances delete NAME

# Firewall
gcloud compute firewall-rules list
gcloud compute firewall-rules describe RULE_NAME
gcloud compute firewall-rules delete RULE_NAME

# SSH
gcloud compute ssh INSTANCE_NAME
gcloud compute scp FILE INSTANCE_NAME:/path/

# Services
gcloud services list --enabled
gcloud services enable SERVICE_NAME

# Billing
gcloud billing accounts list
gcloud billing projects list --billing-account=ACCOUNT_ID
```

### Console Navigation

- **Dashboard:** Home page with overview
- **Compute Engine:** VM instances, disks, images
- **VPC Network:** Firewall rules, routes, subnets
- **Billing:** Budgets, reports, transactions
- **APIs & Services:** Enable/disable APIs
- **IAM & Admin:** Users, roles, permissions

---

## Troubleshooting

### Issue: gcloud command not found

**Solution:**

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

### Issue: Permission denied when creating resources

**Solution:**

1. Via Console: Check IAM permissions
2. Go to **IAM & Admin** → **IAM**
3. Ensure you have "Compute Admin" or "Editor" role

### Issue: Cannot enable APIs

**Solution:**

1. Verify billing is enabled
2. Go to **Billing** → Check account status
3. Ensure you're the project owner or editor

### Issue: Instance won't start

**Solution:**

1. Check quotas: **IAM & Admin** → **Quotas**
2. Try different zone: `us-east1-b` instead of `us-central1-a`
3. Check billing status

### Issue: Firewall rule not working

**Solution:**

1. Verify target tags match instance tags
2. Check source IP ranges (0.0.0.0/0 for all)
3. Ensure protocol and ports are correct
4. Test: `curl http://INSTANCE_IP:5000/health`

---

## Next Steps

After GCP setup:

1. ✅ Verify instance is running
2. ✅ Test SSH connectivity
3. ✅ Run auto-scaler: `python3 scripts/autoscaler.py`
4. ✅ Trigger stress test: `./scripts/trigger_stress.sh`
5. ✅ Monitor scaling process
6. ✅ Verify application on GCP

---

## Additional Resources

- [GCP Documentation](https://cloud.google.com/docs)
- [gcloud CLI Reference](https://cloud.google.com/sdk/gcloud/reference)
- [Compute Engine Pricing](https://cloud.google.com/compute/pricing)
- [Free Tier Information](https://cloud.google.com/free)
- [GCP Console](https://console.cloud.google.com)
