# Auto-Scaling VM to Cloud - Complete Implementation Guide

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Testing the Auto-Scaling](#testing-the-auto-scaling)
6. [Configuration Options](#configuration-options)
7. [Troubleshooting](#troubleshooting)
8. [Cost Management](#cost-management)
9. [Cleanup](#cleanup)

---

## Overview

This project implements an automatic scaling solution that monitors a local Virtual Machine's resource usage and automatically provisions and migrates the application to Google Cloud Platform (GCP) when resource thresholds are exceeded.

### Key Features

- **Real-time Monitoring**: Uses Prometheus and Node Exporter for comprehensive system metrics
- **Threshold-based Scaling**: Triggers when CPU or Memory exceeds 75% for 2 minutes
- **Automated Cloud Provisioning**: Creates GCP instances programmatically
- **Application Migration**: Transfers and deploys containerized applications
- **Cost-Effective**: Uses e2-micro instances and implements budget-aware practices

### Technologies Used

- **Monitoring**: Prometheus, Node Exporter, Grafana
- **Containerization**: Docker, Docker Compose
- **Cloud Platform**: Google Cloud Platform (Compute Engine)
- **Scripting**: Python 3, Bash
- **Application**: Python Flask with stress-testing capabilities

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     LOCAL ENVIRONMENT                        │
│                                                              │
│  ┌─────────────┐        ┌──────────────┐                   │
│  │  Local VM   │◄───────│  Prometheus  │                   │
│  │ (Ubuntu     │        │  (Port 9090) │                   │
│  │  22.04)     │        └──────┬───────┘                   │
│  │             │               │                            │
│  │ - Sample    │        ┌──────▼───────┐                   │
│  │   App:5000  │        │ Node Exporter│                   │
│  │ - Docker    │        │  (Port 9100) │                   │
│  └─────────────┘        └──────────────┘                   │
│                                │                             │
└────────────────────────────────┼─────────────────────────────┘
                                 │
                         ┌───────▼────────┐
                         │  Auto-Scaler   │
                         │   Orchestrator │
                         │                │
                         │ • Polls metrics│
                         │ • Detects      │
                         │   thresholds   │
                         │ • Triggers     │
                         │   scaling      │
                         └───────┬────────┘
                                 │
                      Threshold   │
                      Exceeded    │
                      (>75%)      │
                                 │
                         ┌───────▼────────┐
                         │  Cloud Scaling │
                         │   Workflow     │
                         │                │
                         │ 1. Provision   │
                         │ 2. Transfer    │
                         │ 3. Deploy      │
                         │ 4. Verify      │
                         └───────┬────────┘
                                 │
┌────────────────────────────────▼─────────────────────────────┐
│                    GOOGLE CLOUD PLATFORM                     │
│                                                              │
│  ┌─────────────────────────────────────────────────┐       │
│  │          GCP Compute Engine Instance            │       │
│  │                                                  │       │
│  │  • Type: e2-micro (2 vCPUs, 1GB RAM)           │       │
│  │  • OS: Ubuntu 22.04 LTS                         │       │
│  │  • Docker: Installed                            │       │
│  │  • Application: Deployed and Running            │       │
│  │  • Port 5000: Exposed                           │       │
│  └─────────────────────────────────────────────────┘       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Hardware Requirements

- **Host Machine**:
    - OS: Linux (Kubuntu 22.04 LTS or similar)
    - Virtualization: KVM/QEMU with virt-manager
    - RAM: 4GB+ recommended
    - Storage: 20GB+ free space

- **Local VM**:
    - OS: Ubuntu 22.04 Server LTS
    - CPU: 1 core
    - RAM: 2GB
    - Storage: 10GB
    - IP: Static or known (e.g., 192.168.122.10)

### Software Requirements

- Python 3.8+
- Docker & Docker Compose
- gcloud CLI
- SSH access configured between host and VM
- Git

### Cloud Requirements

- Active GCP account
- GCP project created
- Billing enabled (with budget alerts)
- Compute Engine API enabled
- Credits: ~20 USD (e2-micro for testing)

---

## Step-by-Step Implementation

### Phase 1: Local VM Setup

#### 1.1 Install Docker on Local VM

```bash
# SSH into your VM
ssh sujiv@192.168.122.10

# Update system
sudo apt-get update

# Install Docker
sudo apt-get install -y docker.io docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER

# Re-login for group changes to take effect
exit
ssh sujiv@192.168.122.10
```

#### 1.2 Deploy Monitoring Stack

```bash
# On local VM
cd ~/monitoring

# Start Prometheus, Node Exporter, and Grafana
docker compose up -d

# Verify containers are running
docker ps

# Expected output: 3 containers (prometheus, node-exporter, grafana)
```

**Access Points:**

- Prometheus: http://192.168.122.10:9090
- Node Exporter: http://192.168.122.10:9100/metrics
- Grafana: http://192.168.122.10:3000 (admin/admin123)

#### 1.3 Deploy Sample Application

```bash
# On local VM
cd ~/sample-app

# Build Docker image
docker build -t sample-app:latest .

# Run application
docker run -d --name sample-app \
  -p 5000:5000 \
  --restart unless-stopped \
  sample-app:latest

# Test application
curl http://localhost:5000/health
```

**Application Endpoints:**

- `GET /` - API documentation
- `GET /health` - Health check
- `GET /metrics` - System metrics
- `POST /stress/cpu` - Trigger CPU load
- `POST /stress/memory` - Trigger memory load
- `POST /stress/stop` - Stop stress tests

---

### Phase 2: Host Machine Setup

#### 2.1 Clone and Setup Project

```bash
# On host machine
cd /home/sujiv/Documents/projects/autoscale-vm-cloud

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r scripts/requirements.txt
```

#### 2.2 Configure SSH Key Authentication

```bash
# Generate SSH key (if not exists)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa

# Copy to local VM
ssh-copy-id sujiv@192.168.122.10

# Test connection
ssh sujiv@192.168.122.10 "echo Connected successfully"
```

#### 2.3 Setup GCP CLI

```bash
# Install gcloud CLI (if not installed)
# Follow: https://cloud.google.com/sdk/docs/install

# Initialize gcloud
gcloud init

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Authenticate
gcloud auth login

# Enable Compute Engine API
gcloud services enable compute.googleapis.com

# Verify configuration
gcloud config list
```

---

### Phase 3: GCP Configuration

#### 3.1 Enable Required APIs

**Via gcloud CLI:**

```bash
gcloud services enable compute.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

**Via GCP Console:**

1. Navigate to https://console.cloud.google.com
2. Select your project
3. Go to "APIs & Services" → "Library"
4. Search and enable:
    - Compute Engine API
    - Cloud Resource Manager API

#### 3.2 Set Up Budget Alerts

**Via GCP Console:**

1. Go to "Billing" → "Budgets & alerts"
2. Click "Create Budget"
3. Set amount: $20 (or your available credits)
4. Set alert thresholds: 50%, 75%, 90%, 100%
5. Configure email notifications

**Via gcloud CLI:**

```bash
# Set a budget programmatically (requires billing account ID)
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT_ID \
  --display-name="Auto-Scale Project Budget" \
  --budget-amount=20USD \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.75 \
  --threshold-rule=percent=0.9
```

#### 3.3 Configure Firewall Rules

The provisioning script automatically creates firewall rules, but you can also do it manually:

**Via gcloud CLI:**

```bash
# Allow HTTP traffic on port 5000
gcloud compute firewall-rules create allow-app-5000 \
  --allow=tcp:5000 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server \
  --description="Allow traffic on port 5000 for sample app"
```

**Via GCP Console:**

1. Go to "VPC Network" → "Firewall"
2. Click "Create Firewall Rule"
3. Name: `allow-app-5000`
4. Target tags: `http-server`
5. Source IP ranges: `0.0.0.0/0`
6. Protocols and ports: TCP 5000

---

### Phase 4: Running the Auto-Scaler

#### 4.1 Verify Setup

```bash
# Run setup script
cd /home/sujiv/Documents/projects/autoscale-vm-cloud
./scripts/setup.sh

# This will verify:
# - Python installation
# - Virtual environment
# - Local VM connectivity
# - Monitoring stack status
# - Sample application status
# - GCP configuration
```

#### 4.2 Start the Auto-Scaler

```bash
# Activate virtual environment
source venv/bin/activate

# Start auto-scaler (runs in foreground)
python3 scripts/autoscaler.py

# You should see:
# ==============================
# Auto-Scaling Orchestrator Started
# ==============================
# Prometheus URL: http://192.168.122.10:9090
# CPU Threshold: 75%
# Memory Threshold: 75%
# Check Interval: 30 seconds
# Required Violations: 4 consecutive
# ==============================
```

**Configuration via Environment Variables:**

```bash
# Custom thresholds
export CPU_THRESHOLD=80
export MEMORY_THRESHOLD=80
export CHECK_INTERVAL=60

python3 scripts/autoscaler.py
```

#### 4.3 Trigger Stress Test

**In a separate terminal:**

```bash
cd /home/sujiv/Documents/projects/autoscale-vm-cloud

# Run stress test trigger script
./scripts/trigger_stress.sh

# This will:
# 1. Verify app is running
# 2. Show current metrics
# 3. Start CPU stress test (2 threads, 5 minutes)
```

**Manual stress trigger:**

```bash
# High CPU load
curl -X POST http://192.168.122.10:5000/stress/cpu \
  -H "Content-Type: application/json" \
  -d '{"duration": 300, "intensity": 2}'

# High memory load
curl -X POST http://192.168.122.10:5000/stress/memory \
  -H "Content-Type: application/json" \
  -d '{"duration": 300, "size_mb": 1000}'
```

---

## Testing the Auto-Scaling

### Expected Behavior

1. **Normal Operation (0-60 seconds)**

    ```
    [2026-03-26 21:30:00] CPU: 10.50% | Memory: 25.30%
    [2026-03-26 21:30:30] CPU: 11.20% | Memory: 25.50%
    ```

2. **Stress Test Started (60-120 seconds)**

    ```
    [2026-03-26 21:31:00] CPU: 95.40% | Memory: 26.10%
      ⚠️  THRESHOLD EXCEEDED! (Consecutive: 1/4)
    [2026-03-26 21:31:30] CPU: 96.20% | Memory: 26.30%
      ⚠️  THRESHOLD EXCEEDED! (Consecutive: 2/4)
    ```

3. **Scaling Triggered (After 2 minutes)**

    ```
    [2026-03-26 21:32:00] CPU: 95.80% | Memory: 26.50%
      ⚠️  THRESHOLD EXCEEDED! (Consecutive: 4/4)

    ⚠️  Sustained threshold violation detected!

    ============================================================
    🚀 INITIATING CLOUD SCALING
    ============================================================

    [Step 1/4] Provisioning GCP instance...
    Creating GCP instance: autoscale-app-vm
    Zone: us-central1-a
    Machine type: e2-micro
    ...
    ✓ GCP instance ready at 35.xxx.xxx.xxx

    [Step 2/4] Transferring application to GCP...
    ...
    ✓ Application deployed to GCP

    [Step 3/4] Verifying deployment...
    ✓ Application is healthy on GCP

    [Step 4/4] Logging scaling event...
    ✓ Event logged to logs/scaling_events.json

    ============================================================
    ✅ CLOUD SCALING COMPLETE
    Application now running at: http://35.xxx.xxx.xxx:5000
    ============================================================
    ```

### Verification Steps

1. **Check GCP Instance**

    ```bash
    gcloud compute instances list

    # Expected output:
    # NAME               ZONE           STATUS
    # autoscale-app-vm   us-central1-a  RUNNING
    ```

2. **Test GCP Application**

    ```bash
    # Get instance IP
    GCP_IP=$(gcloud compute instances describe autoscale-app-vm \
      --zone=us-central1-a \
      --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

    # Test health endpoint
    curl http://${GCP_IP}:5000/health

    # Test metrics endpoint
    curl http://${GCP_IP}:5000/metrics
    ```

3. **Check Scaling Logs**
    ```bash
    cat logs/scaling_events.json
    ```

---

## Configuration Options

### Auto-Scaler Configuration

Edit `scripts/autoscaler.py` or use environment variables:

```python
# Default configuration
PROMETHEUS_URL = "http://192.168.122.10:9090"
CPU_THRESHOLD = 75  # percent
MEMORY_THRESHOLD = 75  # percent
CHECK_INTERVAL = 30  # seconds
REQUIRED_VIOLATIONS = 4  # consecutive checks (2 minutes)
```

### GCP Instance Configuration

Edit `scripts/gcp_provision.py`:

```python
# Instance settings
self.machine_type = "e2-micro"  # Options: e2-micro, e2-small, e2-medium
self.zone = "us-central1-a"     # Choose your preferred zone
self.boot_disk_size = "10GB"    # Disk size
```

**Available Machine Types (Cost-Effective):**

- `e2-micro`: 2 vCPUs, 1GB RAM (~$7/month)
- `e2-small`: 2 vCPUs, 2GB RAM (~$14/month)
- `f1-micro`: 1 vCPU, 0.6GB RAM (Free tier eligible)

### Sample Application Configuration

Edit `sample-app/app.py`:

```python
# Server configuration
port = int(os.environ.get('PORT', 5000))

# Stress test limits
max_intensity = psutil.cpu_count() * 2
max_memory = available_memory * 0.8
```

---

## Troubleshooting

### Common Issues

#### 1. Cannot Connect to Local VM

**Problem:** SSH connection fails

```bash
ssh: connect to host 192.168.122.10 port 22: Connection refused
```

**Solutions:**

- Verify VM is running: `virsh list --all`
- Check IP address: `virsh domifaddr YOUR_VM_NAME`
- Ensure SSH service is running on VM
- Verify firewall allows SSH (port 22)

#### 2. Prometheus Not Collecting Metrics

**Problem:** No data in Prometheus queries

**Solutions:**

```bash
# Check if containers are running
ssh sujiv@192.168.122.10 "docker ps"

# Check Prometheus logs
ssh sujiv@192.168.122.10 "docker logs prometheus"

# Restart monitoring stack
ssh sujiv@192.168.122.10 "cd ~/monitoring && docker compose restart"

# Verify targets in Prometheus
# Navigate to: http://192.168.122.10:9090/targets
```

#### 3. GCP Instance Creation Fails

**Problem:** Error creating GCP instance

**Solutions:**

```bash
# Check quotas
gcloud compute project-info describe --project=YOUR_PROJECT_ID

# Verify API is enabled
gcloud services list --enabled | grep compute

# Check billing is enabled
gcloud beta billing projects describe YOUR_PROJECT_ID

# Try a different zone
# Edit scripts/gcp_provision.py, change: self.zone = "us-east1-b"
```

#### 4. Auto-Scaler Not Triggering

**Problem:** Resource usage exceeds threshold but scaling doesn't trigger

**Solutions:**

- Check Prometheus connectivity: `curl http://192.168.122.10:9090/api/v1/query?query=up`
- Verify metrics are being collected: Open http://192.168.122.10:9090/graph
- Check auto-scaler logs for errors
- Ensure threshold is exceeded for consecutive intervals (2 minutes)
- Manually test Prometheus query:
    ```bash
    curl -s "http://192.168.122.10:9090/api/v1/query?query=100%20-%20(avg%20by%20(instance)%20(rate(node_cpu_seconds_total{mode=\"idle\"}[1m]))%20*%20100)"
    ```

#### 5. Docker Image Transfer Fails

**Problem:** Cannot transfer image to GCP

**Solutions:**

```bash
# Ensure gcloud SSH is configured
gcloud compute config-ssh

# Test SSH connection
gcloud compute ssh autoscale-app-vm --zone=us-central1-a

# Check disk space on GCP instance
gcloud compute ssh autoscale-app-vm --zone=us-central1-a \
  --command="df -h"

# Manual image transfer alternative
docker save sample-app:latest | gzip > sample-app.tar.gz
gcloud compute scp sample-app.tar.gz autoscale-app-vm:/tmp/ \
  --zone=us-central1-a
```

### Debug Mode

Enable verbose logging:

```python
# In autoscaler.py, add at the top:
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Cost Management

### Budget Monitoring

**Check Current Spend:**

```bash
# Via gcloud
gcloud beta billing accounts list

# View budget status
gcloud billing budgets list --billing-account=YOUR_BILLING_ACCOUNT_ID
```

**Via GCP Console:**

1. Navigate to "Billing" → "Reports"
2. View spending by service
3. Set up cost alerts

### Cost Optimization Tips

1. **Use Smallest Instance Type**
    - e2-micro is sufficient for this demo
    - Consider f1-micro for free tier

2. **Stop Instances When Not Needed**

    ```bash
    # Stop instance
    gcloud compute instances stop autoscale-app-vm --zone=us-central1-a

    # Start instance
    gcloud compute instances start autoscale-app-vm --zone=us-central1-a
    ```

3. **Use Preemptible Instances** (for testing)

    ```bash
    # In gcp_provision.py, add to create command:
    --preemptible
    ```

4. **Set Automatic Shutdown**
    ```bash
    # Schedule shutdown after 2 hours
    gcloud compute instances add-metadata autoscale-app-vm \
      --zone=us-central1-a \
      --metadata=shutdown-script='#!/bin/bash
    sudo shutdown -h +120'
    ```

### Estimated Costs

| Resource          | Type      | Cost/Month         | Demo Duration | Estimated Cost |
| ----------------- | --------- | ------------------ | ------------- | -------------- |
| e2-micro instance | Always-on | $7.11              | 2 hours       | $0.47          |
| e2-micro instance | Stopped   | ~$0.40 (disk only) | 22 hours      | $0.30          |
| Network egress    | Standard  | $0.12/GB           | 1GB           | $0.12          |
| **Total**         |           |                    | **24 hours**  | **~$0.89**     |

**For 20 credit budget:** You can run ~22 demo cycles

---

## Cleanup

### Remove All GCP Resources

```bash
# Delete the instance
gcloud compute instances delete autoscale-app-vm \
  --zone=us-central1-a \
  --quiet

# Delete firewall rule
gcloud compute firewall-rules delete allow-app-5000 --quiet

# Verify deletion
gcloud compute instances list
gcloud compute firewall-rules list
```

### Cleanup Local Environment

```bash
# Stop and remove containers on local VM
ssh sujiv@192.168.122.10 "docker stop \$(docker ps -aq) && docker rm \$(docker ps -aq)"

# Remove images (optional)
ssh sujiv@192.168.122.10 "docker rmi sample-app:latest"

# Deactivate virtual environment on host
deactivate

# Remove project directory (if desired)
rm -rf /home/sujiv/Documents/projects/autoscale-vm-cloud
```

---

## Plagiarism Declaration

**Declaration of Original Work**

I hereby declare that this implementation, including all code, documentation, scripts, and configuration files, is my original work created specifically for this assignment. No part of this project has been copied from external sources, online repositories, or other students' work.

All external libraries and tools used (Prometheus, Docker, GCP APIs, etc.) are properly utilized through their official documentation and public APIs, and are cited where applicable.

This work represents my understanding and application of cloud computing, monitoring, and auto-scaling concepts.

**Signature:** ************\_************  
**Date:** March 26, 2026  
**Student ID:** ************\_************

---

## Additional Resources

### Official Documentation

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Google Cloud Compute Engine](https://cloud.google.com/compute/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)

### Useful Commands Reference

```bash
# Prometheus queries
# CPU usage
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)

# Memory usage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# GCP instance management
gcloud compute instances list
gcloud compute instances describe INSTANCE_NAME --zone=ZONE
gcloud compute instances stop INSTANCE_NAME --zone=ZONE
gcloud compute instances start INSTANCE_NAME --zone=ZONE
gcloud compute instances delete INSTANCE_NAME --zone=ZONE

# Docker management
docker ps                    # List running containers
docker logs CONTAINER_NAME   # View logs
docker stats                 # View resource usage
docker system prune -a       # Clean up all unused resources

# SSH
ssh sujiv@192.168.122.10
ssh -L 9090:localhost:9090 sujiv@192.168.122.10  # Port forwarding
```

---

**Document Version:** 1.0  
**Last Updated:** March 26, 2026  
**Author:** Student Implementation  
**Project:** Auto-Scaling VM to Cloud Platform
