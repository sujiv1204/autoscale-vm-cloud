# Auto-Scaling VM to Cloud Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GCP](https://img.shields.io/badge/cloud-Google%20Cloud-blue)](https://cloud.google.com/)

## 🚀 Project Overview

An intelligent auto-scaling system that monitors local VM resource usage and automatically provisions and deploys applications to Google Cloud Platform when resource thresholds are exceeded.

### Key Features

✅ **Real-time Monitoring** - Prometheus + Node Exporter for comprehensive metrics  
✅ **Intelligent Scaling** - Triggers when CPU/Memory exceeds 75% for 2 minutes  
✅ **Automated Provisioning** - Creates GCP instances via API  
✅ **Seamless Migration** - Transfers and deploys Docker containers  
✅ **Cost-Effective** - Uses e2-micro instances within budget constraints  
✅ **Production-Ready** - Complete with monitoring, logging, and error handling

---

## 📋 Table of Contents

- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Documentation](#documentation)
- [Demo Video](#demo-video)
- [Contributing](#contributing)
- [License](#license)

---

## 🏗 Architecture

```
Local VM → Prometheus → Auto-Scaler → GCP Provisioning → Application Deployment
   ↓           ↓            ↓              ↓                    ↓
 Docker    Metrics     Threshold      e2-micro           Health Check
 Container Collection  Detection     Instance            Verification
```

**Flow Diagram:**

- Local VM runs sample application with monitoring
- Prometheus collects system metrics every 15 seconds
- Auto-scaler polls Prometheus every 30 seconds
- When CPU/Memory > 75% for 2 minutes → Triggers scaling
- Provisions GCP instance, transfers Docker image, deploys application
- Verifies deployment and logs scaling event

---

## ⚡ Quick Start

### Prerequisites

- Local VM: Ubuntu 22.04 with Docker installed
- Host Machine: Linux with Python 3.8+
- GCP Account with Compute Engine API enabled
- gcloud CLI configured

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd autoscale-vm-cloud

# Run setup script
./scripts/setup.sh

# Activate virtual environment
source venv/bin/activate
```

### Running the System

**Terminal 1 - Start Auto-Scaler:**

```bash
python3 scripts/autoscaler.py
```

**Terminal 2 - Trigger Stress Test:**

```bash
./scripts/trigger_stress.sh
```

### Accessing Dashboards

- **Sample App:** http://192.168.122.10:5000
- **Prometheus:** http://192.168.122.10:9090
- **Grafana:** http://192.168.122.10:3000 (admin/admin123)

---

## 📁 Project Structure

```
autoscale-vm-cloud/
├── monitoring/                 # Monitoring stack configuration
│   ├── docker-compose.yml     # Prometheus, Node Exporter, Grafana
│   ├── prometheus/
│   │   └── prometheus.yml     # Prometheus configuration
│   └── grafana/
│       └── provisioning/      # Grafana datasources
├── sample-app/                # Sample Flask application
│   ├── app.py                 # Main application with stress endpoints
│   ├── Dockerfile             # Container definition
│   ├── requirements.txt       # Python dependencies
│   └── test_app.sh           # Application test script
├── scripts/                   # Automation scripts
│   ├── autoscaler.py         # Main auto-scaling orchestrator
│   ├── gcp_provision.py      # GCP instance provisioning
│   ├── gcp_deploy.py         # Application deployment to GCP
│   ├── setup.sh              # Environment setup script
│   ├── trigger_stress.sh     # Stress test trigger
│   └── requirements.txt      # Script dependencies
├── docs/                      # Documentation
│   └── IMPLEMENTATION_GUIDE.md  # Complete step-by-step guide
├── diagrams/                  # Architecture diagrams
├── logs/                      # Scaling event logs
└── README.md                  # This file
```

---

## 💻 Requirements

### Hardware

- **Host Machine:** 4GB+ RAM, 20GB storage
- **Local VM:** 1 core, 2GB RAM, 10GB disk

### Software

- Python 3.8+
- Docker & Docker Compose
- gcloud CLI
- Git
- SSH access configured

### Cloud

- GCP account with billing enabled
- ~$20 credits (e2-micro instances)
- Compute Engine API enabled

---

## 🔧 Installation

### 1. Setup Local VM

```bash
# SSH into VM
ssh sujiv@192.168.122.10

# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl start docker
sudo usermod -aG docker $USER

# Deploy monitoring stack
cd ~/monitoring
docker compose up -d

# Build and run sample app
cd ~/sample-app
docker build -t sample-app:latest .
docker run -d -p 5000:5000 --restart unless-stopped sample-app:latest
```

### 2. Setup Host Machine

```bash
# Clone repository
git clone <repository-url>
cd autoscale-vm-cloud

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r scripts/requirements.txt
```

### 3. Configure GCP

```bash
# Install gcloud CLI (if needed)
# https://cloud.google.com/sdk/docs/install

# Initialize and authenticate
gcloud init
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable compute.googleapis.com
```

---

## 📖 Usage

### Starting the Auto-Scaler

```bash
# Basic usage
source venv/bin/activate
python3 scripts/autoscaler.py

# With custom thresholds
export CPU_THRESHOLD=80
export MEMORY_THRESHOLD=80
python3 scripts/autoscaler.py
```

### Triggering Scaling

**Option 1: Using Script**

```bash
./scripts/trigger_stress.sh
```

**Option 2: Manual API Call**

```bash
# CPU stress (2 threads, 5 minutes)
curl -X POST http://192.168.122.10:5000/stress/cpu \
  -H "Content-Type: application/json" \
  -d '{"duration": 300, "intensity": 2}'

# Memory stress (1GB, 5 minutes)
curl -X POST http://192.168.122.10:5000/stress/memory \
  -H "Content-Type: application/json" \
  -d '{"duration": 300, "size_mb": 1000}'
```

### Monitoring

```bash
# Check current metrics
curl http://192.168.122.10:5000/metrics | jq .

# View Prometheus metrics
curl http://192.168.122.10:9090/api/v1/query?query=node_cpu_seconds_total

# Check scaling logs
cat logs/scaling_events.json
```

### GCP Management

```bash
# List instances
gcloud compute instances list

# Get instance IP
gcloud compute instances describe autoscale-app-vm \
  --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

# Stop instance (save costs)
gcloud compute instances stop autoscale-app-vm --zone=us-central1-a

# Delete instance
gcloud compute instances delete autoscale-app-vm --zone=us-central1-a
```

---

## 📚 Documentation

Comprehensive guides available in the `docs/` directory:

- **[Implementation Guide](docs/IMPLEMENTATION_GUIDE.md)** - Complete step-by-step instructions
- **Architecture Design** - System architecture and flow diagrams
- **API Documentation** - Sample application API reference
- **Troubleshooting** - Common issues and solutions
- **Cost Management** - Budget optimization tips

---

## 🎥 Demo Video

[Link to recorded demonstration video will be added here]

The video demonstrates:

1. System setup and configuration
2. Monitoring dashboard overview
3. Triggering resource stress
4. Auto-scaling in action
5. Application running on GCP
6. Verification and cleanup

---

## 🔍 Key Components

### Auto-Scaler (`scripts/autoscaler.py`)

- Polls Prometheus every 30 seconds
- Detects sustained threshold violations (2 minutes)
- Orchestrates complete scaling workflow
- Logs all scaling events

### GCP Provisioner (`scripts/gcp_provision.py`)

- Creates e2-micro instances
- Configures firewall rules
- Installs Docker via startup script
- Returns instance IP for deployment

### GCP Deployer (`scripts/gcp_deploy.py`)

- Transfers Docker images via gcloud scp
- Loads and runs containers on GCP
- Performs health checks
- Handles errors gracefully

### Sample Application (`sample-app/app.py`)

- Flask web server with stress test endpoints
- Real-time system metrics via psutil
- Configurable CPU and memory stress
- Health check endpoints for monitoring

---

## 🧪 Testing

### Run Complete Test Suite

```bash
# Setup test environment
./scripts/setup.sh

# Start auto-scaler in one terminal
python3 scripts/autoscaler.py

# Trigger test in another terminal
./scripts/trigger_stress.sh

# Expected: Scaling triggers after ~2 minutes
```

### Manual Testing

```bash
# Test local app
curl http://192.168.122.10:5000/health

# Test Prometheus connectivity
curl http://192.168.122.10:9090/api/v1/query?query=up

# Test GCP provisioning
python3 scripts/gcp_provision.py

# Test deployment
python3 scripts/gcp_deploy.py <GCP_INSTANCE_IP>
```

---

## 💰 Cost Estimation

| Component           | Cost         | Duration | Total      |
| ------------------- | ------------ | -------- | ---------- |
| e2-micro instance   | $0.0067/hour | 2 hours  | $0.47      |
| Disk storage (10GB) | $0.04/month  | 1 day    | $0.30      |
| Network egress      | $0.12/GB     | 1GB      | $0.12      |
| **Total per demo**  |              |          | **~$0.89** |

**With $20 budget:** ~22 complete demo cycles possible

---

## 🛠 Troubleshooting

### Common Issues

**1. Auto-scaler not triggering:**

- Verify Prometheus is accessible: `curl http://192.168.122.10:9090/api/v1/query?query=up`
- Check metrics are being collected: Open http://192.168.122.10:9090/targets
- Ensure stress test is actually increasing CPU/Memory

**2. GCP instance creation fails:**

- Verify APIs are enabled: `gcloud services list --enabled | grep compute`
- Check quotas: `gcloud compute project-info describe --project=YOUR_PROJECT`
- Ensure billing is active

**3. Cannot connect to GCP instance:**

- Wait 30-60 seconds after creation for SSH to be ready
- Check firewall rules: `gcloud compute firewall-rules list`
- Verify instance is running: `gcloud compute instances list`

See [Implementation Guide](docs/IMPLEMENTATION_GUIDE.md) for detailed troubleshooting.

---

## 🗑 Cleanup

```bash
# Delete GCP resources
gcloud compute instances delete autoscale-app-vm --zone=us-central1-a --quiet
gcloud compute firewall-rules delete allow-app-5000 --quiet

# Stop local containers
ssh sujiv@192.168.122.10 "cd ~/monitoring && docker compose down"
ssh sujiv@192.168.122.10 "docker stop sample-app && docker rm sample-app"

# Deactivate virtual environment
deactivate
```

---

## 📝 Plagiarism Declaration

**This project is original work created for academic purposes.**

All code, documentation, and configurations are developed from scratch using official documentation and public APIs. No code has been copied from external sources or other students.

External tools used (Prometheus, Docker, GCP) are properly utilized through their official interfaces.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🤝 Contributing

This is an academic project. For suggestions or improvements:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 👤 Author

**Student Implementation**  
Course: Cloud Computing  
Institution: [Your Institution]  
Date: March 2026

---

## 🙏 Acknowledgments

- Prometheus team for excellent monitoring tools
- Google Cloud Platform documentation
- Flask framework maintainers
- Docker and containerization community

---

## 📞 Support

For issues or questions:

- Check the [Implementation Guide](docs/IMPLEMENTATION_GUIDE.md)
- Review [Troubleshooting](docs/IMPLEMENTATION_GUIDE.md#troubleshooting) section
- Open an issue in the repository

---

**⭐ If you found this project helpful, please consider giving it a star!**
