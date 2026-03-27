# Auto-Scaling Test Instructions

## Updated Features

- ✅ Auto-scale UP when CPU/Memory > 75% for 2 minutes
- ✅ Auto-scale DOWN when CPU/Memory < 50% for 2 minutes
- ✅ All emojis removed from output
- ✅ Continuous monitoring (doesn't exit after scaling)

## Test Procedure

### Step 1: Start Autoscaler (Terminal 1)

```bash
ssh sujiv@192.168.122.10
source ~/autoscale_venv/bin/activate
python3 -u ~/autoscaler.py
```

You should see:

```
============================================================
Auto-Scaler Started (Running inside VM)
============================================================
CPU Threshold: 75%
Memory Threshold: 75%
Scale-down Threshold: 50%
Check Interval: 30s
============================================================

[LOCAL] [22:00:00] CPU: 5.0% | Memory: 35.0%
```

### Step 2: Trigger High Load (Terminal 2) - Scale UP Test

```bash
# From host machine
ssh sujiv@192.168.122.10 "python3 ~/direct_stress.py 8 &"
```

Expected output (in Terminal 1):

```
[LOCAL] [22:00:30] CPU: 100.0% | Memory: 35.0% [HIGH] Count: 1/4
[LOCAL] [22:01:00] CPU: 100.0% | Memory: 35.0% [HIGH] Count: 2/4
[LOCAL] [22:01:30] CPU: 100.0% | Memory: 35.0% [HIGH] Count: 3/4
[LOCAL] [22:02:00] CPU: 100.0% | Memory: 35.0% [HIGH] Count: 4/4

Sustained high load detected! Scaling up...

============================================================
PROVISIONING GCP INSTANCE
============================================================
Creating instance...
OK Instance created
Creating firewall rule...
Waiting for instance to be ready...
OK Instance IP: 34.xx.xx.xx

Deploying application...
Saving Docker image...
Transferring to GCP...
Loading and running on GCP...

============================================================
DEPLOYMENT COMPLETE
Application URL: http://34.xx.xx.xx:5000
============================================================
```

After scale-up, monitoring continues:

```
[SCALED] [22:05:00] CPU: 100.0% | Memory: 35.0% [HIGH] Count: 1/4
[SCALED] [22:05:30] CPU: 95.0% | Memory: 35.0%
...
```

### Step 3: Wait for Load to Drop - Scale DOWN Test

The stress test runs for 3 minutes. After it completes:

```
[SCALED] [22:08:00] CPU: 5.0% | Memory: 35.0% [LOW] Count: 1/4
[SCALED] [22:08:30] CPU: 3.0% | Memory: 35.0% [LOW] Count: 2/4
[SCALED] [22:09:00] CPU: 2.0% | Memory: 34.0% [LOW] Count: 3/4
[SCALED] [22:09:30] CPU: 1.0% | Memory: 34.0% [LOW] Count: 4/4

Sustained low load detected! Scaling down...

============================================================
DEPROVISIONING GCP INSTANCE
============================================================
Deleting instance...
Instance deleted
Cleaning up firewall rule...
============================================================

[LOCAL] [22:10:00] CPU: 1.0% | Memory: 34.0%
```

### Step 4: Verify Scale-Down

```bash
# In Terminal 2, check GCP
gcloud compute instances list --filter="name:autoscale-cloud-vm"
```

Should show: "Listed 0 items." (instance deleted)

## Full Test Timeline

| Time | Event            | Expected Result            |
| ---- | ---------------- | -------------------------- |
| 0:00 | Start autoscaler | Monitoring at [LOCAL]      |
| 0:30 | Trigger load     | CPU jumps to 100%          |
| 2:00 | 4th high check   | Scale-up triggered         |
| 3:00 | GCP deployed     | Status changes to [SCALED] |
| 5:00 | Load ends        | CPU drops below 50%        |
| 7:00 | 4th low check    | Scale-down triggered       |
| 7:30 | Instance deleted | Status back to [LOCAL]     |

## Manual Verification Commands

```bash
# Check GCP instance exists
gcloud compute instances list --filter="name:autoscale-cloud-vm"

# Check app on GCP (when scaled up)
curl http://[GCP-IP]:5000/health

# Check local VM CPU
ssh sujiv@192.168.122.10 "top -bn1 | grep '%Cpu'"

# View scaling log
ssh sujiv@192.168.122.10 "cat /tmp/scaling.log"
```

## Cleanup (if needed)

```bash
# Stop autoscaler: Ctrl+C in Terminal 1

# Delete GCP instance manually if stuck
gcloud compute instances delete autoscale-cloud-vm \
  --zone=us-central1-a \
  --project=m25cse011-vcc-asn3 \
  --quiet
```

## Cost Note

Each test cycle costs ~$0.01 (5-10 minutes of e2-micro usage)
