#!/usr/bin/env python3
"""
Simple Auto-Scaler - Runs inside the VM
Monitors local resource usage and triggers GCP scaling when threshold exceeded
"""

import psutil
import subprocess
import time
import json
import math
from datetime import datetime

# Configuration
CPU_THRESHOLD = 75
MEMORY_THRESHOLD = 75
SCALE_DOWN_THRESHOLD = 50  # Scale down when below this
CHECK_INTERVAL = 10  # seconds
REQUIRED_CHECKS = 4  # 4 checks of sustained load/low usage for scaling

# GCP Configuration
GCP_ZONE = "us-central1-a"
GCP_MACHINE_TYPE = "e2-micro"
GCP_INSTANCE_NAME = "autoscale-cloud-vm"

# Deployment Configuration
DOCKER_READY_TIMEOUT = 300   # Max seconds to wait for Docker on GCP
DOCKER_POLL_INTERVAL = 15    # Seconds between Docker readiness checks
DEPLOY_VERIFY_TIMEOUT = 60   # Seconds to wait for app health check


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


def run_gcp_ssh_command(command, suppress_errors=False):
    """Run a command on the GCP instance via SSH, return (success, stdout, stderr)"""
    stderr_redirect = "2>/dev/null" if suppress_errors else ""
    result = subprocess.run(
        f"gcloud compute ssh {GCP_INSTANCE_NAME} --zone={GCP_ZONE} "
        f"--command='{command}' {stderr_redirect}",
        shell=True,
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()


def wait_for_docker():
    """Poll GCP instance until Docker daemon is ready"""
    max_attempts = math.ceil(DOCKER_READY_TIMEOUT / DOCKER_POLL_INTERVAL)
    print("Waiting for Docker to be ready on GCP instance...")

    for i in range(max_attempts):
        elapsed = (i + 1) * DOCKER_POLL_INTERVAL
        success, stdout, _ = run_gcp_ssh_command("sudo docker info", suppress_errors=True)

        if success:
            print(f"OK Docker is ready! (took ~{elapsed}s)")
            return True

        print(f"  Docker not ready yet... ({elapsed}s/{DOCKER_READY_TIMEOUT}s)")
        time.sleep(DOCKER_POLL_INTERVAL)

    print(f"ERROR: Docker not ready after {DOCKER_READY_TIMEOUT}s")
    return False


def verify_deployment(gcp_ip):
    """Verify the application is running on GCP by hitting the health endpoint"""
    print("Verifying deployment...")
    max_attempts = DEPLOY_VERIFY_TIMEOUT // 5

    for i in range(max_attempts):
        try:
            result = subprocess.run(
                f"curl -s -o /dev/null -w '%{{http_code}}' --connect-timeout 3 http://{gcp_ip}:5000/health",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout.strip() == "200":
                print(f"OK Application verified at http://{gcp_ip}:5000")
                return True
        except:
            pass

        if i < max_attempts - 1:
            print(f"  App not responding yet, retrying... ({(i+1)*5}s)")
            time.sleep(5)

    print("WARNING: Could not verify application health")
    return False


def deprovision_gcp_instance():
    """Destroy GCP instance to scale down"""
    print("\n" + "="*60)
    print("DEPROVISIONING GCP INSTANCE")
    print("="*60)

    print("Deleting instance...")
    result = subprocess.run(
        f"gcloud compute instances delete {GCP_INSTANCE_NAME} --zone={GCP_ZONE} --quiet",
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("Instance deleted")

        # Delete firewall rule
        print("Cleaning up firewall rule...")
        subprocess.run(
            f"gcloud compute firewall-rules delete allow-app-{GCP_INSTANCE_NAME} --quiet 2>/dev/null",
            shell=True,
            capture_output=True
        )
        print("="*60)
        return True
    else:
        print(f"Error: {result.stderr}")
        return False


def provision_gcp_instance():
    """Provision GCP instance and deploy application"""
    print("\n" + "="*60)
    print("PROVISIONING GCP INSTANCE")
    print("="*60)

    # Step 1: Create instance with startup script that installs Docker
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
systemctl enable docker
systemctl start docker
' """

    print("Creating instance...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error creating instance: {result.stderr}")
        return None

    print("OK Instance created")

    # Step 2: Create firewall rule
    print("Creating firewall rule...")
    subprocess.run(
        f"gcloud compute firewall-rules create allow-app-{GCP_INSTANCE_NAME} "
        f"--allow=tcp:5000 --target-tags=http-server 2>/dev/null",
        shell=True,
        capture_output=True
    )

    # Step 3: Wait for Docker to be ready (polls instead of sleeping)
    if not wait_for_docker():
        print("ERROR: Docker installation timed out. Instance created but app not deployed.")
        # Get IP anyway so user can manually fix
        result = subprocess.run(
            f"gcloud compute instances describe {GCP_INSTANCE_NAME} --zone={GCP_ZONE} "
            f"--format='get(networkInterfaces[0].accessConfigs[0].natIP)'",
            shell=True, capture_output=True, text=True
        )
        gcp_ip = result.stdout.strip()
        if gcp_ip:
            print(f"Instance IP: {gcp_ip} (manual deployment needed)")
        return None

    # Step 4: Get instance IP
    result = subprocess.run(
        f"gcloud compute instances describe {GCP_INSTANCE_NAME} --zone={GCP_ZONE} "
        f"--format='get(networkInterfaces[0].accessConfigs[0].natIP)'",
        shell=True,
        capture_output=True,
        text=True
    )
    gcp_ip = result.stdout.strip()

    if not gcp_ip:
        print("Error: Could not get instance IP")
        return None

    print(f"OK Instance IP: {gcp_ip}")

    # Step 5: Deploy application
    print("\nDeploying application...")

    # 5a: Save Docker image locally
    print("Saving Docker image...")
    result = subprocess.run(
        "docker save sample-app:latest | gzip > /tmp/app.tar.gz",
        shell=True, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Error saving Docker image: {result.stderr}")
        print("Make sure 'sample-app:latest' image exists locally (run: docker build -t sample-app:latest ./sample-app/)")
        return gcp_ip

    # 5b: Transfer image to GCP
    print("Transferring to GCP...")
    result = subprocess.run(
        f"gcloud compute scp /tmp/app.tar.gz {GCP_INSTANCE_NAME}:/tmp/ --zone={GCP_ZONE}",
        shell=True, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Error transferring image: {result.stderr}")
        return gcp_ip

    # 5c: Load image and run container on GCP
    print("Loading and running on GCP...")
    success, stdout, stderr = run_gcp_ssh_command(
        "gunzip < /tmp/app.tar.gz | sudo docker load && "
        "sudo docker run -d -p 5000:5000 -e DEPLOY_ENV=cloud --restart unless-stopped --name sample-app sample-app:latest"
    )
    if not success:
        print(f"Error deploying container: {stderr}")
        print("Trying alternative: loading image first, then running...")
        # Retry: load then run separately
        run_gcp_ssh_command("gunzip < /tmp/app.tar.gz | sudo docker load")
        time.sleep(3)
        success, stdout, stderr = run_gcp_ssh_command(
            "sudo docker run -d -p 5000:5000 -e DEPLOY_ENV=cloud --restart unless-stopped --name sample-app sample-app:latest"
        )
        if not success:
            print(f"Error running container: {stderr}")
            return gcp_ip

    # Cleanup local temp file
    subprocess.run("rm -f /tmp/app.tar.gz", shell=True)

    # Step 6: Verify deployment
    time.sleep(5)  # Brief wait for container startup
    verify_deployment(gcp_ip)

    print("\n" + "="*60)
    print("DEPLOYMENT COMPLETE")
    print(f"Application URL: http://{gcp_ip}:5000")
    print("="*60)

    return gcp_ip


def main():
    print("="*60)
    print("Auto-Scaler Started (Running inside VM)")
    print("="*60)
    print(f"CPU Threshold: {CPU_THRESHOLD}%")
    print(f"Memory Threshold: {MEMORY_THRESHOLD}%")
    print(f"Scale-down Threshold: {SCALE_DOWN_THRESHOLD}%")
    print(f"Check Interval: {CHECK_INTERVAL}s")
    print("="*60 + "\n")

    high_load_count = 0
    low_load_count = 0
    scaled_up = False

    try:
        while True:
            cpu, memory = get_resource_usage()
            timestamp = datetime.now().strftime("%H:%M:%S")

            gcp_exists = check_gcp_instance_exists()
            status = "[SCALED]" if gcp_exists else "[LOCAL]"

            print(
                f"{status} [{timestamp}] CPU: {cpu:.1f}% | Memory: {memory:.1f}%", end="")

            # Scale-up logic
            if cpu >= CPU_THRESHOLD or memory >= MEMORY_THRESHOLD:
                high_load_count += 1
                low_load_count = 0
                print(f" [HIGH] Count: {high_load_count}/{REQUIRED_CHECKS}")

                if high_load_count >= REQUIRED_CHECKS and not gcp_exists:
                    print(f"\nSustained high load detected! Scaling up...")

                    gcp_ip = provision_gcp_instance()
                    if gcp_ip:
                        scaled_up = True
                        with open('/tmp/scaling.log', 'a') as f:
                            f.write(
                                f"{datetime.now().isoformat()}: Scaled UP to {gcp_ip}\n")
                        high_load_count = 0

            # Scale-down logic
            elif cpu < SCALE_DOWN_THRESHOLD and memory < SCALE_DOWN_THRESHOLD:
                high_load_count = 0

                if gcp_exists:
                    low_load_count += 1
                    print(f" [LOW] Count: {low_load_count}/{REQUIRED_CHECKS}")

                    if low_load_count >= REQUIRED_CHECKS:
                        print(f"\nSustained low load detected! Scaling down...")

                        if deprovision_gcp_instance():
                            scaled_up = False
                            with open('/tmp/scaling.log', 'a') as f:
                                f.write(
                                    f"{datetime.now().isoformat()}: Scaled DOWN\n")
                            low_load_count = 0
                else:
                    print()

            # Normal load
            else:
                if high_load_count > 0:
                    print(f" [NORMAL] (was high: {high_load_count})")
                elif low_load_count > 0:
                    print(f" [NORMAL] (was low: {low_load_count})")
                else:
                    print()
                high_load_count = 0
                low_load_count = 0

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n\nStopped by user")


if __name__ == "__main__":
    main()
