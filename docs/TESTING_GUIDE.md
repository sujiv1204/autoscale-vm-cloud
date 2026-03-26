# Testing and Demo Script

This document provides a complete testing workflow and demo script for the auto-scaling project.

---

## Pre-Demo Checklist

### ✅ Before Starting

- [ ] Local VM is running and accessible
- [ ] Monitoring stack is deployed (Prometheus, Node Exporter, Grafana)
- [ ] Sample application is running on local VM
- [ ] GCP project is configured with gcloud CLI
- [ ] Virtual environment is set up on host machine
- [ ] All scripts have executable permissions

### Verify Setup

```bash
# Run the setup verification script
cd /home/sujiv/Documents/projects/autoscale-vm-cloud
./scripts/setup.sh
```

---

## Demo Script (10-15 minutes)

### Part 1: Introduction (2 minutes)

**What to say:**

> "Today I'm demonstrating an intelligent auto-scaling system that monitors a local VM and automatically provisions resources on Google Cloud Platform when thresholds are exceeded."

**What to show:**

- Project repository structure
- README.md overview
- Architecture diagram

```bash
# Show project structure
tree -L 2 -I 'venv|__pycache__|*.pyc'

# Display README
cat README.md | head -50
```

### Part 2: Local Environment Setup (3 minutes)

**What to say:**

> "The local environment consists of a VM running Ubuntu with Docker containers for monitoring and the sample application."

**What to show:**

```bash
# Show local VM info
ssh sujiv@192.168.122.10 "uname -a && echo '---' && free -h && echo '---' && df -h /"

# Show running containers
ssh sujiv@192.168.122.10 "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

# Access Prometheus in browser
# Open: http://192.168.122.10:9090

# Show Prometheus targets
# Navigate to: Status → Targets

# Access Grafana in browser
# Open: http://192.168.122.10:3000
# Login: admin/admin123

# Test sample application
curl http://192.168.122.10:5000/ | jq .

# Check current metrics
curl http://192.168.122.10:5000/metrics | jq .
```

### Part 3: Monitoring Dashboard (2 minutes)

**What to say:**

> "Prometheus collects system metrics every 15 seconds. Let's query some metrics to see current resource usage."

**What to show:**

```bash
# Query current CPU usage
curl -s 'http://192.168.122.10:9090/api/v1/query?query=100%20-%20(avg%20by%20(instance)%20(rate(node_cpu_seconds_total{mode=%22idle%22}[1m]))%20*%20100)' | jq '.data.result[0].value'

# Query memory usage
curl -s 'http://192.168.122.10:9090/api/v1/query?query=(1%20-%20(node_memory_MemAvailable_bytes%20/%20node_memory_MemTotal_bytes))%20*%20100' | jq '.data.result[0].value'
```

**In Prometheus UI:**

1. Go to Graph tab
2. Enter query: `rate(node_cpu_seconds_total{mode="idle"}[1m])`
3. Show graph
4. Enter query: `node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes`
5. Show graph

### Part 4: Auto-Scaler Configuration (2 minutes)

**What to say:**

> "The auto-scaler monitors these metrics and triggers cloud scaling when CPU or Memory exceeds 75% for 2 consecutive minutes."

**What to show:**

```bash
# Show auto-scaler code structure
head -50 scripts/autoscaler.py

# Highlight key configuration
grep -A 5 "def __init__" scripts/autoscaler.py
```

**Explain the logic:**

1. Polls Prometheus every 30 seconds
2. Checks if CPU > 75% OR Memory > 75%
3. Requires 4 consecutive violations (2 minutes)
4. Triggers GCP provisioning workflow
5. Deploys application to cloud

### Part 5: Triggering Auto-Scaling (5 minutes)

**What to say:**

> "Now let's trigger the auto-scaling by generating load on the local VM. I'll start the auto-scaler, then generate CPU stress."

**What to do:**

**Terminal 1 - Start Auto-Scaler:**

```bash
# Activate virtual environment
source venv/bin/activate

# Start auto-scaler
python3 scripts/autoscaler.py

# You should see:
# ==============================
# Auto-Scaling Orchestrator Started
# ==============================
# Monitoring started. Press Ctrl+C to stop.
```

**Terminal 2 - Trigger Stress:**

```bash
# Wait 30 seconds for baseline metrics

# Trigger stress test
./scripts/trigger_stress.sh

# OR manually:
curl -X POST http://192.168.122.10:5000/stress/cpu \
  -H "Content-Type: application/json" \
  -d '{"duration": 300, "intensity": 2}'
```

**What to show:**

- Auto-scaler output showing increasing CPU
- Consecutive violation counter increasing
- Threshold breach detection
- Scaling workflow initiation

**Expected output timeline:**

```
[00:00] CPU: 12% | Memory: 25%
[00:30] CPU: 12% | Memory: 25%
[01:00] CPU: 96% | Memory: 26%  ⚠️ THRESHOLD EXCEEDED! (1/4)
[01:30] CPU: 96% | Memory: 26%  ⚠️ THRESHOLD EXCEEDED! (2/4)
[02:00] CPU: 95% | Memory: 26%  ⚠️ THRESHOLD EXCEEDED! (3/4)
[02:30] CPU: 96% | Memory: 26%  ⚠️ THRESHOLD EXCEEDED! (4/4)

⚠️ Sustained threshold violation detected!

============================================================
🚀 INITIATING CLOUD SCALING
============================================================
```

### Part 6: GCP Provisioning (3 minutes)

**What to say:**

> "The system is now automatically provisioning a VM instance on Google Cloud Platform and deploying the application."

**What to show:**

**Terminal 3 - Monitor GCP:**

```bash
# Watch GCP instances being created
watch -n 5 'gcloud compute instances list'

# Check firewall rules
gcloud compute firewall-rules list --filter="name:allow-app-5000"
```

**In GCP Console:**

1. Navigate to Compute Engine → VM instances
2. Show instance being created
3. Click on instance to see details
4. Show external IP address

**Auto-scaler will show:**

```
[Step 1/4] Provisioning GCP instance...
Creating GCP instance: autoscale-app-vm
Zone: us-central1-a
Machine type: e2-micro
✓ GCP instance ready at 35.xxx.xxx.xxx

[Step 2/4] Transferring application to GCP...
Saving Docker image from local VM...
✓ Image saved: 120M
Transferring image to GCP...
✓ Image transferred to GCP
Loading and running application on GCP...
✓ Application running on GCP

[Step 3/4] Verifying deployment...
✓ Application is healthy on GCP

[Step 4/4] Logging scaling event...
✓ Event logged to logs/scaling_events.json

============================================================
✅ CLOUD SCALING COMPLETE
Application now running at: http://35.xxx.xxx.xxx:5000
============================================================
```

### Part 7: Verification (2 minutes)

**What to say:**

> "Let's verify the application is now running on Google Cloud Platform and functioning correctly."

**What to show:**

```bash
# Get GCP instance IP
GCP_IP=$(gcloud compute instances describe autoscale-app-vm \
  --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "GCP Instance IP: $GCP_IP"

# Test health endpoint
curl http://${GCP_IP}:5000/health | jq .

# Test metrics endpoint
curl http://${GCP_IP}:5000/metrics | jq .

# Show in browser
# Open: http://[GCP_IP]:5000
```

**SSH into GCP instance:**

```bash
# Connect to instance
gcloud compute ssh autoscale-app-vm --zone=us-central1-a

# Check Docker containers
sudo docker ps

# Check application logs
sudo docker logs sample-app

# Exit
exit
```

### Part 8: Cost Management (1 minute)

**What to say:**

> "This solution is cost-effective. The e2-micro instance costs approximately $0.47 for 2 hours of runtime."

**What to show:**

```bash
# Show instance details
gcloud compute instances describe autoscale-app-vm \
  --zone=us-central1-a \
  --format="table(name, machineType, status)"

# Check billing (in GCP Console)
# Navigate to: Billing → Reports
```

**Explain:**

- e2-micro: 2 vCPUs, 1GB RAM
- Cost: ~$7/month = $0.23/day = $0.01/hour
- 10GB disk: ~$0.40/month
- Total demo cost: < $1

### Part 9: Cleanup (1 minute)

**What to say:**

> "To avoid ongoing charges, we can easily clean up all cloud resources."

**What to do:**

```bash
# Delete GCP instance
gcloud compute instances delete autoscale-app-vm \
  --zone=us-central1-a \
  --quiet

# Delete firewall rule
gcloud compute firewall-rules delete allow-app-5000 --quiet

# Verify cleanup
gcloud compute instances list
```

---

## Integration Testing Checklist

### Test 1: Monitoring Stack

```bash
# ✅ Verify Prometheus is scraping metrics
curl -s http://192.168.122.10:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Expected: All targets show health="up"
```

### Test 2: Sample Application

```bash
# ✅ Test health endpoint
curl http://192.168.122.10:5000/health

# ✅ Test metrics endpoint
curl http://192.168.122.10:5000/metrics

# ✅ Test CPU stress
curl -X POST http://192.168.122.10:5000/stress/cpu \
  -H "Content-Type: application/json" \
  -d '{"duration": 10, "intensity": 1}'

# Wait 10 seconds, check metrics show increased CPU
curl http://192.168.122.10:5000/metrics | jq '.cpu'
```

### Test 3: GCP Provisioning

```bash
# ✅ Test GCP provisioning script
python3 scripts/gcp_provision.py

# Expected: Instance created successfully
# Verify:
gcloud compute instances list | grep autoscale-app-vm
```

### Test 4: GCP Deployment

```bash
# ✅ Get GCP instance IP
GCP_IP=$(gcloud compute instances describe autoscale-app-vm \
  --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

# ✅ Test deployment script
python3 scripts/gcp_deploy.py $GCP_IP

# Expected: Application deployed successfully
# Verify:
curl http://${GCP_IP}:5000/health
```

### Test 5: Auto-Scaling Workflow

```bash
# ✅ Start auto-scaler (Terminal 1)
source venv/bin/activate
python3 scripts/autoscaler.py

# ✅ Trigger stress (Terminal 2)
./scripts/trigger_stress.sh

# ✅ Wait for scaling (2-3 minutes)
# Expected: Auto-scaler detects threshold and provisions GCP instance

# ✅ Verify deployment
GCP_IP=$(gcloud compute instances describe autoscale-app-vm \
  --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
curl http://${GCP_IP}:5000/health
```

### Test 6: Scaling Logs

```bash
# ✅ Check scaling event log
cat logs/scaling_events.json | jq .

# Expected: JSON entry with timestamp, GCP IP, thresholds
```

---

## Troubleshooting During Demo

### Issue: Auto-scaler doesn't trigger

**Quick fix:**

```bash
# Increase stress intensity
curl -X POST http://192.168.122.10:5000/stress/cpu \
  -H "Content-Type: application/json" \
  -d '{"duration": 300, "intensity": 2}'

# Or manually trigger (for demo purposes)
python3 scripts/gcp_provision.py
```

### Issue: GCP instance creation fails

**Quick fix:**

```bash
# Try different zone
# Edit scripts/gcp_provision.py
# Change: self.zone = "us-east1-b"

# Or use preemptible instance (cheaper)
# Add to create command: --preemptible
```

### Issue: Application not accessible on GCP

**Quick fix:**

```bash
# Check firewall rule
gcloud compute firewall-rules list | grep 5000

# Manually create if missing
gcloud compute firewall-rules create allow-app-5000 \
  --allow=tcp:5000 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server

# Check instance is running
gcloud compute instances list

# Check Docker on GCP
gcloud compute ssh autoscale-app-vm --zone=us-central1-a \
  --command="sudo docker ps"
```

---

## Video Recording Checklist

### Before Recording

- [ ] Clean terminal history: `history -c && history -w`
- [ ] Close unnecessary applications
- [ ] Set terminal font size to 14+
- [ ] Test audio levels
- [ ] Prepare script/notes
- [ ] Have GCP console open in browser
- [ ] Have Prometheus/Grafana open in browser

### Recording Structure

1. **Introduction** (1 min)
    - Project overview
    - Problem statement
    - Solution approach

2. **Architecture** (2 min)
    - Show architecture diagram
    - Explain components
    - Describe workflow

3. **Local Setup** (2 min)
    - Show monitoring stack
    - Demonstrate sample app
    - Show Prometheus metrics

4. **Auto-Scaling Demo** (5 min)
    - Start auto-scaler
    - Trigger stress test
    - Show threshold detection
    - Show GCP provisioning
    - Verify deployment

5. **Verification** (2 min)
    - Test GCP application
    - Show cost analysis
    - Demonstrate cleanup

6. **Conclusion** (1 min)
    - Summarize achievements
    - Discuss use cases
    - Future improvements

### Recording Tips

- Speak clearly and at moderate pace
- Pause between sections
- Show both terminal and browser
- Zoom in on important details
- Use cursor to highlight key points
- Keep video under 15 minutes

---

## Post-Demo Actions

### After Successful Demo

```bash
# 1. Stop stress test
curl -X POST http://192.168.122.10:5000/stress/stop

# 2. Save scaling logs
cp logs/scaling_events.json logs/demo-$(date +%Y%m%d-%H%M%S).json

# 3. Take screenshots
# - Prometheus dashboard
# - GCP console showing instance
# - Application running on GCP
# - Cost analysis

# 4. Stop GCP instance (save costs)
gcloud compute instances stop autoscale-app-vm --zone=us-central1-a

# 5. Commit demo logs
git add logs/demo-*.json
git commit -m "docs: Add demo scaling logs"
git push
```

### Complete Cleanup

```bash
# Delete all GCP resources
gcloud compute instances delete autoscale-app-vm --zone=us-central1-a --quiet
gcloud compute firewall-rules delete allow-app-5000 --quiet

# Verify
gcloud compute instances list
gcloud compute firewall-rules list

# Stop local containers (if needed)
ssh sujiv@192.168.122.10 "cd ~/monitoring && docker compose down"
ssh sujiv@192.168.122.10 "docker stop sample-app"
```

---

## Success Criteria

- [x] Monitoring stack deployed and collecting metrics
- [x] Sample application running with stress test capabilities
- [x] Auto-scaler detects threshold violations
- [x] GCP instance provisioned automatically
- [x] Application deployed to GCP successfully
- [x] Health checks pass on GCP
- [x] Complete documentation provided
- [x] Video demonstration recorded
- [x] All code committed to repository
- [x] Within budget ($20 credits)

---

## Additional Notes

### Performance Expectations

- **Threshold Detection Time:** ~2 minutes (4 x 30-second intervals)
- **GCP Provisioning Time:** ~2-3 minutes
- **Image Transfer Time:** ~1-2 minutes (depends on image size ~120MB)
- **Total Scaling Time:** ~5-7 minutes from trigger to deployment

### Cost Tracking

```bash
# Check current GCP spend
gcloud billing accounts list

# View detailed usage
# Navigate to: GCP Console → Billing → Reports

# Set up billing alerts
# Navigate to: Billing → Budgets & alerts
```

---

**Document Version:** 1.0  
**Last Updated:** March 26, 2026
