# Auto-Scaling VM to Cloud (GCP)

**Simple auto-scaling system that monitors VM resource usage and scales to Google Cloud Platform when thresholds exceed 75%.**

The auto-scaler runs **inside the VM** monitoring itself using psutil and automatically provisions GCP instances when needed.

---

## Quick Start

### 1. Setup (Already Done ✅)

- ✅ Local VM running at 192.168.122.10
- ✅ Docker installed on VM
- ✅ Monitoring stack running (Prometheus + Node Exporter)
- ✅ Sample app deployed on VM
- ✅ gcloud CLI configured on VM
- ✅ Python dependencies installed in venv

### 2. Run Auto-Scaler

```bash
# SSH into VM
ssh sujiv@192.168.122.10

# Start autoscaler
source ~/autoscale_venv/bin/activate
python3 ~/autoscaler.py
```

### 3. Trigger Load

**In another terminal:**
```bash
# From host
ssh sujiv@192.168.122.10 "~/trigger_load.sh"

# OR directly
curl -X POST http://192.168.122.10:5000/stress/cpu \
  -H "Content-Type: application/json" \
  -d '{"duration": 300, "intensity": 2}'
```

### 4. Watch Auto-Scaling

After ~2 minutes of sustained load:
- Auto-scaler detects 75% threshold
- Provisions GCP e2-micro instance
- Deploys application to cloud
- Returns GCP instance IP

---

## How It Works

```
┌─────────────────┐
│   Local VM      │  1. Monitors itself (CPU/Memory)
│  192.168.122.10 │  2. Detects threshold > 75%
│                 │  3. Creates GCP instance
│  • Sample App   │  4. Transfers Docker image
│  • Prometheus   │  5. Deploys to cloud
│  • Autoscaler   │  
└─────────────────┘
         │
         │ Scales when load > 75%
         ▼
┌─────────────────┐
│  GCP Instance   │
│  e2-micro       │
│                 │
│  • Sample App   │
│  • Port 5000    │
└─────────────────┘
```

---

## Components

### 1. Monitoring Stack (`monitoring/`)
- **Prometheus**: Metrics collection (port 9090)
- **Node Exporter**: System metrics (port 9100)  
- **Grafana**: Visualization (port 3000, admin/admin123)

### 2. Sample Application (`sample-app/`)
- **Flask app** with stress test endpoints
- Endpoints: `/health`, `/metrics`, `/stress/cpu`, `/stress/memory`
- Runs on port 5000

### 3. Auto-Scaler (`autoscaler.py`)
- Monitors CPU and memory usage
- Detects 75% threshold for 2 minutes
- Provisions GCP instance automatically
- Deploys application to cloud

---

## Configuration

Edit `autoscaler.py`:

```python
CPU_THRESHOLD = 75          # Trigger at 75% CPU
MEMORY_THRESHOLD = 75       # Trigger at 75% Memory
CHECK_INTERVAL = 30         # Check every 30 seconds
REQUIRED_CHECKS = 4         # 4 checks = 2 minutes

GCP_ZONE = "us-central1-a"
GCP_MACHINE_TYPE = "e2-micro"
```

---

## Access Points

- **Local App:** http://192.168.122.10:5000
- **Prometheus:** http://192.168.122.10:9090
- **Grafana:** http://192.168.122.10:3000
- **GCP App:** http://[GCP_IP]:5000 (after scaling)

---

## Testing

```bash
# Check system status
curl http://192.168.122.10:5000/metrics

# Trigger CPU stress
curl -X POST http://192.168.122.10:5000/stress/cpu \
  -H "Content-Type: application/json" \
  -d '{"duration": 300, "intensity": 2}'

# Check if GCP instance exists
gcloud compute instances list

# Stop stress test
curl -X POST http://192.168.122.10:5000/stress/stop
```

---

## Cost

| Item | Cost | Duration | Total |
|------|------|----------|-------|
| e2-micro instance | $0.0067/hr | 2 hours | $0.47 |
| 10GB disk | $0.04/month | 1 day | $0.30 |
| Network | $0.12/GB | 1GB | $0.12 |
| **Total** | | | **$0.89** |

**With $20 budget:** ~22 demos possible

---

## Cleanup

```bash
# Delete GCP instance
gcloud compute instances delete autoscale-cloud-vm --zone=us-central1-a --quiet

# Delete firewall rule
gcloud compute firewall-rules delete allow-app-autoscale-cloud-vm --quiet

# Verify
gcloud compute instances list
```

---

## Documentation

See `docs/IMPLEMENTATION_GUIDE.md` for:
- Detailed setup instructions
- Troubleshooting guide
- GCP configuration (CLI + Console)
- Cost management

---

## Plagiarism Declaration

This project is original work created for academic purposes. All code developed from scratch using official documentation. No code copied from external sources.

---

## License

MIT License - See LICENSE file
