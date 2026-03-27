#!/usr/bin/env python3
"""
Simple Auto-Scaler - Runs inside the VM
Monitors local resource usage and triggers GCP scaling when threshold exceeded
"""

import psutil
import subprocess
import time
import json
from datetime import datetime

# Configuration
CPU_THRESHOLD = 75
MEMORY_THRESHOLD = 75
CHECK_INTERVAL = 30  # seconds
REQUIRED_CHECKS = 4  # 2 minutes of sustained load

# GCP Configuration
GCP_ZONE = "us-central1-a"
GCP_MACHINE_TYPE = "e2-micro"
GCP_INSTANCE_NAME = "autoscale-cloud-vm"


def get_resource_usage():
    """Get current CPU and memory usage"""
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    return cpu, memory


def check_gcp_instance_exists():
    """Check if GCP instance already exists"""
    try:
        result = subprocess.run(
            f"gcloud compute instances describe {GCP_INSTANCE_NAME} --zone={GCP_ZONE} 2>/dev/null",
            shell=True,
            capture_output=True
        )
        return result.returncode == 0
    except:
        return False


def provision_gcp_instance():
    """Provision GCP instance and deploy application"""
    print("\n" + "="*60)
    print("🚀 PROVISIONING GCP INSTANCE")
    print("="*60)

    # Create instance
    cmd = f"""gcloud compute instances create {GCP_INSTANCE_NAME} \
        --zone={GCP_ZONE} \
        --machine-type={GCP_MACHINE_TYPE} \
        --image-family=ubuntu-2204-lts \
        --image-project=ubuntu-os-cloud \
        --boot-disk-size=10GB \
        --tags=http-server \
        --metadata=startup-script='#!/bin/bash
apt-get update
apt-get install -y docker.io
systemctl start docker
usermod -aG docker \$(getent passwd 1000 | cut -d: -f1)
' """

    print("Creating instance...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None

    print("✓ Instance created")

    # Create firewall rule
    print("Creating firewall rule...")
    subprocess.run(
        f"gcloud compute firewall-rules create allow-app-{GCP_INSTANCE_NAME} --allow=tcp:5000 --target-tags=http-server 2>/dev/null",
        shell=True,
        capture_output=True
    )

    # Wait for instance
    print("Waiting for instance to be ready...")
    time.sleep(60)

    # Get IP
    result = subprocess.run(
        f"gcloud compute instances describe {GCP_INSTANCE_NAME} --zone={GCP_ZONE} --format='get(networkInterfaces[0].accessConfigs[0].natIP)'",
        shell=True,
        capture_output=True,
        text=True
    )
    gcp_ip = result.stdout.strip()

    if not gcp_ip:
        print("Error: Could not get instance IP")
        return None

    print(f"✓ Instance IP: {gcp_ip}")

    # Deploy application
    print("\nDeploying application...")

    # Save and transfer image
    print("Saving Docker image...")
    subprocess.run(
        "docker save sample-app:latest | gzip > /tmp/app.tar.gz", shell=True)

    print("Transferring to GCP...")
    subprocess.run(
        f"gcloud compute scp /tmp/app.tar.gz {GCP_INSTANCE_NAME}:/tmp/ --zone={GCP_ZONE}",
        shell=True,
        capture_output=True
    )

    print("Loading and running on GCP...")
    time.sleep(10)
    subprocess.run(
        f"gcloud compute ssh {GCP_INSTANCE_NAME} --zone={GCP_ZONE} --command='gunzip < /tmp/app.tar.gz | sudo docker load && sudo docker run -d -p 5000:5000 --restart unless-stopped sample-app:latest'",
        shell=True,
        capture_output=True
    )

    # Cleanup
    subprocess.run("rm -f /tmp/app.tar.gz", shell=True)

    print("\n" + "="*60)
    print(f"✅ DEPLOYMENT COMPLETE")
    print(f"Application URL: http://{gcp_ip}:5000")
    print("="*60)

    return gcp_ip


def main():
    print("="*60)
    print("Auto-Scaler Started (Running inside VM)")
    print("="*60)
    print(f"CPU Threshold: {CPU_THRESHOLD}%")
    print(f"Memory Threshold: {MEMORY_THRESHOLD}%")
    print(f"Check Interval: {CHECK_INTERVAL}s")
    print("="*60 + "\n")

    violation_count = 0
    scaled = False

    try:
        while not scaled:
            cpu, memory = get_resource_usage()
            timestamp = datetime.now().strftime("%H:%M:%S")

            print(f"[{timestamp}] CPU: {cpu:.1f}% | Memory: {memory:.1f}%", end="")

            if cpu >= CPU_THRESHOLD or memory >= MEMORY_THRESHOLD:
                violation_count += 1
                print(
                    f" ⚠️  THRESHOLD EXCEEDED! ({violation_count}/{REQUIRED_CHECKS})")

                if violation_count >= REQUIRED_CHECKS:
                    print(f"\n⚠️  Sustained high load detected!")

                    if not check_gcp_instance_exists():
                        gcp_ip = provision_gcp_instance()
                        if gcp_ip:
                            scaled = True
                            with open('/tmp/scaling.log', 'a') as f:
                                f.write(
                                    f"{datetime.now().isoformat()}: Scaled to {gcp_ip}\n")
                    else:
                        print("GCP instance already exists!")
                        scaled = True
            else:
                if violation_count > 0:
                    print(f" ✓ Back to normal (was {violation_count})")
                else:
                    print()
                violation_count = 0

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n\nStopped by user")


if __name__ == "__main__":
    main()
