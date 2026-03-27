# Simple Setup Guide

## Prerequisites
- Ubuntu VM at 192.168.122.10 with Docker
- gcloud CLI configured on VM  
- $20 GCP credits

## Setup Steps

### 1. Deploy Monitoring (on VM)
```bash
ssh sujiv@192.168.122.10
cd ~/monitoring
docker compose up -d
```

### 2. Deploy Sample App (on VM)
```bash
cd ~/sample-app
docker build -t sample-app:latest .
docker run -d -p 5000:5000 --restart unless-stopped sample-app:latest
```

### 3. Install Python Deps (on VM)
```bash
cd ~
python3 -m venv autoscale_venv
source autoscale_venv/bin/activate
pip install psutil requests
```

### 4. Run Auto-Scaler (on VM)
```bash
source ~/autoscale_venv/bin/activate
python3 ~/autoscaler.py
```

### 5. Trigger Load (from anywhere)
```bash
ssh sujiv@192.168.122.10 "~/trigger_load.sh"
```

## What Happens

1. Auto-scaler checks CPU/Memory every 30s
2. When > 75% for 2 minutes, it triggers
3. Creates GCP e2-micro instance
4. Transfers Docker image
5. Runs app on GCP

## Verify

```bash
# Check local app
curl http://192.168.122.10:5000/health

# After scaling, check GCP
gcloud compute instances list
curl http://[GCP_IP]:5000/health
```

## Cleanup

```bash
gcloud compute instances delete autoscale-cloud-vm --zone=us-central1-a --quiet
```

---

## Troubleshooting

**Can't connect to VM:**
```bash
ping 192.168.122.10
ssh sujiv@192.168.122.10
```

**Docker not running:**
```bash
ssh sujiv@192.168.122.10 "sudo systemctl start docker"
```

**App not responding:**
```bash
ssh sujiv@192.168.122.10 "docker ps"
ssh sujiv@192.168.122.10 "docker logs sample-app"
```

**GCP auth issues:**
```bash
ssh sujiv@192.168.122.10 "gcloud auth list"
ssh sujiv@192.168.122.10 "gcloud config list"
```
