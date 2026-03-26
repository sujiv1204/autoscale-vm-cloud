# Video Demo Recording Script

## 🎬 Video Recording Instructions

**Duration:** 10-15 minutes  
**Format:** MP4, 1920x1080 (1080p) recommended  
**Audio:** Clear voice-over with minimal background noise

---

## Pre-Recording Checklist

### Environment Setup

- [ ] Clean desktop (close unnecessary windows)
- [ ] Terminal font size: 14+ (readable in video)
- [ ] Browser zoom: 100% or 125%
- [ ] Close notification popups
- [ ] Test audio levels
- [ ] Clear terminal history: `history -c && clear`

### Applications to Open

- [ ] Terminal (2-3 tabs)
- [ ] Web browser with tabs:
    - http://192.168.122.10:9090 (Prometheus)
    - http://192.168.122.10:3000 (Grafana)
    - http://192.168.122.10:5000 (Sample App)
    - https://console.cloud.google.com (GCP Console)
- [ ] Text editor with README.md open

### System Verification

```bash
# Run before recording
cd /home/sujiv/Documents/projects/autoscale-vm-cloud
./scripts/setup.sh

# Ensure all checks pass
```

---

## Recording Tools (Choose One)

### Option 1: OBS Studio (Recommended)

**Installation:**

```bash
sudo apt install obs-studio
```

**Settings:**

- Video: 1920x1080, 30 FPS
- Audio: Desktop audio + Microphone
- Output: MP4, Quality preset: High

**Recording:**

1. Open OBS Studio
2. Add "Screen Capture" source
3. Add "Audio Input Capture" (your microphone)
4. Click "Start Recording"
5. Follow script
6. Click "Stop Recording"

### Option 2: SimpleScreenRecorder

**Installation:**

```bash
sudo apt install simplescreenrecorder
```

**Settings:**

- Resolution: 1920x1080
- Frame rate: 30 FPS
- Audio: ALSA (Microphone) + PulseAudio (Desktop)

### Option 3: Kazam

**Installation:**

```bash
sudo apt install kazam
```

**Settings:**

- Capture mode: Fullscreen
- Include cursor
- Record audio from microphone

---

## Script Timeline

### 🎬 Scene 1: Introduction (0:00-2:00)

**Show:** Desktop with project folder open

**Say:**

> "Hello! Today I'm demonstrating an intelligent auto-scaling system that I've built for my cloud computing assignment. This system monitors a local virtual machine and automatically provisions resources on Google Cloud Platform when resource usage exceeds defined thresholds."

**Action:**

```bash
# Show project structure
cd /home/sujiv/Documents/projects/autoscale-vm-cloud
tree -L 2 -I 'venv|__pycache__|*.pyc'
```

**Say:**

> "The project consists of several components: monitoring infrastructure using Prometheus, a sample Flask application, and automation scripts for cloud provisioning and deployment."

**Action:**

- Open README.md in text editor
- Scroll through to show structure
- Show architecture diagram (if generated)

---

### 🎬 Scene 2: Architecture Overview (2:00-3:30)

**Show:** Architecture diagram or draw.io

**Say:**

> "Let me explain the architecture. On the left, we have our local VM running Ubuntu with Docker containers. It hosts our sample application and monitoring stack. Prometheus collects system metrics every 15 seconds through Node Exporter."

**Action:**

- Point to each component in diagram
- Trace the flow with cursor

**Say:**

> "The auto-scaler monitors these metrics via Prometheus API every 30 seconds. When CPU or memory usage exceeds 75% for two consecutive minutes, it triggers an automated workflow that provisions a VM on Google Cloud Platform, transfers the Docker image, and deploys the application."

---

### 🎬 Scene 3: Local Environment (3:30-5:30)

**Show:** Terminal

**Say:**

> "Let's start by looking at our local environment. I have a VM running at IP 192.168.122.10."

**Action:**

```bash
# Show VM details
ssh sujiv@192.168.122.10 "uname -a && echo '---' && free -h && echo '---' && nproc"

# Show running containers
ssh sujiv@192.168.122.10 "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
```

**Say:**

> "As you can see, we have Prometheus, Node Exporter, Grafana, and our sample application running in Docker containers."

**Action:**

- Switch to browser
- Open http://192.168.122.10:9090 (Prometheus)
- Navigate to Status → Targets
- Show all targets are "UP"

**Say:**

> "Prometheus is successfully scraping metrics from Node Exporter. Let's check our sample application."

**Action:**

```bash
# Test application
curl http://192.168.122.10:5000/ | jq .

# Check current metrics
curl http://192.168.122.10:5000/metrics | jq .
```

**Say:**

> "The application is healthy with current CPU at around 10-15% and memory at 25-30%."

---

### 🎬 Scene 4: Monitoring Dashboard (5:30-7:00)

**Show:** Prometheus UI

**Say:**

> "Let's look at the monitoring dashboard. I'll query some metrics in Prometheus."

**Action:**

- In Prometheus, go to Graph tab
- Enter query: `rate(node_cpu_seconds_total{mode="idle"}[1m])`
- Show graph
- Change to query: `node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes`
- Show graph

**Say:**

> "These are the same metrics that our auto-scaler monitors. Now let's also look at Grafana for a better visualization."

**Action:**

- Switch to Grafana (http://192.168.122.10:3000)
- Login if needed (admin/admin123)
- Browse to Node Exporter dashboard or create simple panel
- Show CPU and Memory graphs

---

### 🎬 Scene 5: Auto-Scaling Demo (7:00-12:00)

**Say:**

> "Now for the exciting part - let's trigger the auto-scaling. I'll start the auto-scaler in one terminal and generate load in another."

**Action:**
**Terminal 1:**

```bash
cd /home/sujiv/Documents/projects/autoscale-vm-cloud
source venv/bin/activate
python3 scripts/autoscaler.py
```

**Say:**

> "The auto-scaler is now running. It's polling Prometheus every 30 seconds and checking if CPU or memory exceeds 75%."

**Wait 30 seconds for baseline reading**

**Action:**
**Terminal 2:**

```bash
./scripts/trigger_stress.sh
```

**Say:**

> "I've just triggered a CPU stress test that will run for 5 minutes with high intensity. Now watch the auto-scaler output."

**Action:**

- Show auto-scaler terminal
- Point out when metrics start showing high CPU
- Highlight the consecutive violation counter
- Wait for threshold to be reached (about 2 minutes)

**Say:**

> "Notice how the auto-scaler is detecting CPU usage above 75%. It's now counting consecutive violations. After the fourth consecutive check - which represents 2 minutes of sustained high load - it will trigger the cloud scaling workflow."

**Action:**

- When scaling triggers, show the workflow:
    - "INITIATING CLOUD SCALING" message
    - GCP instance provisioning
    - Image transfer
    - Application deployment

**Say:**

> "The system is now automatically provisioning a VM on Google Cloud Platform. Let's switch to the GCP console to see this happening in real-time."

**Action:**

- Switch to browser
- Open GCP Console → Compute Engine → VM instances
- Refresh to show new instance being created
- Show instance details (type: e2-micro, zone, IP)

**Say:**

> "As you can see, an e2-micro instance has been created. The autoscaler is now transferring the Docker image and deploying the application."

---

### 🎬 Scene 6: Verification (12:00-13:30)

**Say:**

> "Once deployment is complete, let's verify the application is running on GCP."

**Action:**

```bash
# Get GCP IP
GCP_IP=$(gcloud compute instances describe autoscale-app-vm \
  --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "GCP Instance IP: $GCP_IP"

# Test health endpoint
curl http://${GCP_IP}:5000/health | jq .

# Test metrics endpoint
curl http://${GCP_IP}:5000/metrics | jq .
```

**Say:**

> "Perfect! The application is now running on Google Cloud and responding to requests. Let's also view it in the browser."

**Action:**

- Open http://[GCP_IP]:5000 in browser
- Show application homepage
- Navigate to /metrics endpoint

---

### 🎬 Scene 7: Cost Analysis (13:30-14:30)

**Say:**

> "Now let's talk about costs. This solution is designed to be budget-friendly."

**Action:**

- Show GCP Console → Billing → Reports
- Explain instance costs

**Say:**

> "The e2-micro instance costs approximately 47 cents for 2 hours of runtime. With the 20 dollar budget for this project, we can run approximately 22 complete demo cycles. This makes it very practical for development and testing."

**Action:**

```bash
# Show instance details
gcloud compute instances describe autoscale-app-vm \
  --zone=us-central1-a \
  --format="table(name, machineType, status, networkInterfaces[0].accessConfigs[0].natIP)"
```

---

### 🎬 Scene 8: Cleanup (14:30-15:00)

**Say:**

> "Finally, let's clean up the resources to avoid ongoing charges."

**Action:**

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

**Say:**

> "All cloud resources have been removed. The local environment continues to run for future demos."

---

### 🎬 Scene 9: Conclusion (15:00-15:30)

**Show:** Back to README or project folder

**Say:**

> "In summary, I've demonstrated an end-to-end auto-scaling solution that:
>
> - Monitors local VM resources in real-time
> - Automatically detects threshold violations
> - Provisions cloud infrastructure on demand
> - Deploys applications seamlessly
> - Operates within budget constraints
>
> The complete source code, documentation, and setup instructions are available in this GitHub repository. Thank you for watching!"

**Action:**

- Show README.md one more time
- Scroll to show documentation links
- End recording

---

## Post-Recording Checklist

### Video Editing (Optional)

- [ ] Trim silence at beginning/end
- [ ] Add title screen (5 seconds)
- [ ] Add transitions between sections
- [ ] Increase audio volume if needed
- [ ] Add captions/subtitles (optional)

### Video Export

- [ ] Format: MP4 (H.264)
- [ ] Resolution: 1920x1080 or 1280x720
- [ ] Frame rate: 30 FPS
- [ ] Bitrate: 5-10 Mbps
- [ ] File size: <500MB (for easy upload)

### Upload Options

#### Option 1: YouTube (Recommended)

1. Create account/login
2. Click "Create" → "Upload video"
3. Title: "Auto-Scaling VM to Cloud Platform - Demo"
4. Description: Include project summary and timestamps
5. Tags: cloud computing, auto-scaling, GCP, DevOps
6. Privacy: Unlisted or Public
7. Copy video URL

#### Option 2: Google Drive

1. Upload video file
2. Right-click → Share → Get link
3. Set permissions: "Anyone with the link can view"
4. Copy link

#### Option 3: Alternative Platforms

- Vimeo
- Microsoft OneDrive
- Dropbox

### Update Repository

```bash
cd /home/sujiv/Documents/projects/autoscale-vm-cloud

# Update README with video link
# Edit README.md and add:
# ## 🎥 Demo Video
# [Watch the demonstration video](YOUR_VIDEO_LINK)

git add README.md
git commit -m "docs: Add demo video link"
git push
```

---

## Troubleshooting

### Issue: Audio not recording

**Solution:**

- Check microphone permissions
- Test audio in OBS/SSR settings
- Use `pavucontrol` to adjust levels

### Issue: Video is laggy

**Solution:**

- Lower recording resolution to 720p
- Close other applications
- Reduce browser tabs
- Use simpler terminal (no transparency)

### Issue: File too large

**Solution:**

- Re-encode with HandBrake
- Target bitrate: 2-5 Mbps
- Compress with FFmpeg:

```bash
ffmpeg -i input.mp4 -c:v libx264 -crf 23 -c:a aac -b:a 128k output.mp4
```

### Issue: No scaling trigger during demo

**Quick fix:**

- Increase stress intensity: `intensity: 3`
- Reduce threshold temporarily: `export CPU_THRESHOLD=50`
- Pre-provision GCP instance for backup

---

## Alternative: Pre-Record Sections

If live demo is challenging:

1. Record each scene separately
2. Use video editing software to combine
3. Add voice-over in post-production
4. Ensures smooth transitions
5. Allows re-recording problem sections

**Tools:**

- OpenShot (Video editor)
- Kdenlive (Advanced editor)
- Audacity (Audio editing)

---

## Time Management

**Suggested Recording Schedule:**

| Section       | Duration     | Preparation Time |
| ------------- | ------------ | ---------------- |
| Introduction  | 2 min        | 5 min            |
| Architecture  | 1.5 min      | 3 min            |
| Local Env     | 2 min        | 2 min            |
| Monitoring    | 1.5 min      | 2 min            |
| Auto-scaling  | 5 min        | 10 min           |
| Verification  | 1.5 min      | 2 min            |
| Cost Analysis | 1 min        | 1 min            |
| Cleanup       | 0.5 min      | 1 min            |
| Conclusion    | 0.5 min      | 1 min            |
| **Total**     | **15.5 min** | **27 min**       |

**Total Time Investment:** ~1 hour (including setup and possible retakes)

---

## Quality Checklist

Before finalizing:

- [ ] Audio is clear (no background noise)
- [ ] Video is smooth (no lag)
- [ ] Text is readable (font size appropriate)
- [ ] All demos work correctly
- [ ] Timer shows 10-15 minutes
- [ ] Covers all key points
- [ ] Professional presentation
- [ ] Conclusion is clear
- [ ] File uploaded successfully
- [ ] Link accessible and working

---

**Good luck with your recording! 🎬**

Remember: It's okay to pause, explain clearly, and show that you understand the system. The goal is to demonstrate your knowledge and the working system.
