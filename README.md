# Auto-Scaling VM to Cloud (GCP)

Auto-scaling system that monitors a local VM's resource usage and scales to Google Cloud Platform when CPU or memory exceeds 75%.

---

## Repository Structure

```
autoscale-vm-cloud/
|-- autoscaler.py          # Core auto-scaling script (runs inside VM)
|-- direct_stress.py       # CPU stress test to trigger scaling
|-- requirements.txt       # Python dependencies (psutil)
|-- sample-app/
|   |-- Dockerfile
|   |-- app.py             # Flask web app with dashboard
|   +-- requirements.txt
|-- monitoring/
|   |-- docker-compose.yml # Prometheus + Grafana + Node Exporter
|   |-- prometheus/
|   |   +-- prometheus.yml
|   +-- grafana/
|       +-- provisioning/
|           |-- datasources/
|           |   +-- prometheus.yml
|           +-- dashboards/
|               +-- dashboards.yml
+-- .gitignore
```

---

## Prerequisites

- Host machine with KVM/QEMU and virt-manager
- Local VM running Ubuntu 22.04 (IP: 192.168.122.10)
- Docker installed on the VM
- Python 3 with psutil
- Google Cloud SDK (gcloud) authenticated on the VM

---

## Step 1: VM Setup

```bash
# Install KVM on host
sudo apt install qemu-kvm libvirt-daemon-system virt-manager

# Create VM in virt-manager (Ubuntu 22.04, 2 vCPU, 2GB RAM, 20GB disk)
# Configure static IP: 192.168.122.10

# SSH into VM
ssh sujiv@192.168.122.10

# Install Docker
sudo apt update
sudo apt install -y docker.io
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install Python and create venv
sudo apt install -y python3-pip python3-venv
python3 -m venv ~/autoscale_venv
source ~/autoscale_venv/bin/activate
pip install psutil

# Install and configure gcloud CLI
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list
sudo apt update && sudo apt install -y google-cloud-cli
gcloud init
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud config set compute/zone us-central1-a
```

## Step 2: Build and Run Sample App

```bash
cd ~/sample-app
docker build -t sample-app:latest .
docker run -d -p 5000:5000 --name sample-app sample-app:latest
curl http://localhost:5000/health
```

## Step 3: Start Monitoring (Prometheus + Grafana)

```bash
cd ~/monitoring
docker-compose up -d
```

- Prometheus: http://192.168.122.10:9090
- Node Exporter: http://192.168.122.10:9100/metrics
- Grafana: http://192.168.122.10:3000 (login: admin / admin123)

### Import Grafana Dashboard

1. Open Grafana at http://192.168.122.10:3000
2. Go to Dashboards > Import
3. Enter dashboard ID: **1860**
4. Select Prometheus as the data source
5. Click Import

This imports the "Node Exporter Full" dashboard which shows CPU, memory, disk, network, and other system metrics.

## Step 4: Run Auto-Scaler

```bash
# Terminal 1: Start auto-scaler
source ~/autoscale_venv/bin/activate
python3 ~/autoscaler.py

# Terminal 2: Trigger CPU load
source ~/autoscale_venv/bin/activate
python3 ~/direct_stress.py 8
```

## Step 5: Verify Cloud Deployment

After auto-scaling triggers:

```bash
gcloud compute instances list
curl http://<GCP_IP>:5000/health
gcloud compute ssh autoscale-cloud-vm --zone=us-central1-a --command='sudo docker ps'
```

Open http://<GCP_IP>:5000 in browser to see "Running on Cloud (GCP)".

---

## How It Works

1. autoscaler.py monitors CPU and memory via psutil every 10 seconds
2. If either exceeds 75% for 4 consecutive checks, triggers scale-up
3. Creates a GCP e2-micro instance with Docker via startup script
4. Polls until Docker is ready (up to 5 minutes)
5. Saves Docker image, transfers via gcloud compute scp
6. Loads image and runs container with -e DEPLOY_ENV=cloud
7. Verifies deployment via /health endpoint
8. When load drops below 50% for 4 checks, deletes GCP instance

---

## Cleanup

```bash
gcloud compute instances delete autoscale-cloud-vm --zone=us-central1-a --quiet
gcloud compute firewall-rules delete allow-app-autoscale-cloud-vm --quiet
```
