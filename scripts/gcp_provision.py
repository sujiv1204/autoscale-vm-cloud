#!/usr/bin/env python3
"""
GCP Instance Provisioner
Creates a cost-effective VM instance on Google Cloud Platform for auto-scaling.
"""

import subprocess
import json
import sys
import time


class GCPProvisioner:
    def __init__(self, project_id):
        self.project_id = project_id
        self.instance_name = "autoscale-app-vm"
        self.zone = "us-central1-a"  # Using us-central1 for cost efficiency
        self.machine_type = "e2-micro"  # Free tier eligible, 2 vCPUs, 1GB RAM
        self.image_family = "ubuntu-2204-lts"
        self.image_project = "ubuntu-os-cloud"

    def run_command(self, cmd, capture_output=True):
        """Run a shell command and return output"""
        try:
            if capture_output:
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True)
                return result.returncode, result.stdout, result.stderr
            else:
                result = subprocess.run(cmd, shell=True)
                return result.returncode, "", ""
        except Exception as e:
            return 1, "", str(e)

    def check_instance_exists(self):
        """Check if instance already exists"""
        cmd = f"gcloud compute instances describe {self.instance_name} --zone={self.zone} --project={self.project_id} 2>/dev/null"
        returncode, stdout, stderr = self.run_command(cmd)
        return returncode == 0

    def create_instance(self):
        """Create a new GCP instance"""
        print(f"Creating GCP instance: {self.instance_name}")
        print(f"Zone: {self.zone}")
        print(f"Machine type: {self.machine_type}")
        print(f"Image: {self.image_family}")

        # Startup script to install Docker
        startup_script = """#!/bin/bash
# Update system
apt-get update

# Install Docker
apt-get install -y docker.io
systemctl start docker
systemctl enable docker

# Add default user to docker group
usermod -aG docker $(getent passwd 1000 | cut -d: -f1) 2>/dev/null || true

# Install docker-compose
apt-get install -y docker-compose

echo "Setup complete" > /tmp/startup-complete.txt
"""

        # Create instance with gcloud CLI
        cmd = f"""gcloud compute instances create {self.instance_name} \\
            --project={self.project_id} \\
            --zone={self.zone} \\
            --machine-type={self.machine_type} \\
            --image-family={self.image_family} \\
            --image-project={self.image_project} \\
            --boot-disk-size=10GB \\
            --boot-disk-type=pd-standard \\
            --tags=http-server,https-server \\
            --metadata=startup-script='{startup_script}' \\
            --scopes=https://www.googleapis.com/auth/cloud-platform"""

        returncode, stdout, stderr = self.run_command(
            cmd, capture_output=False)

        if returncode != 0:
            print(f"Error creating instance: {stderr}")
            return False

        print("Instance created successfully!")
        return True

    def create_firewall_rule(self):
        """Create firewall rule for application access"""
        print("Creating firewall rules...")

        # Check if rule exists
        cmd = f"gcloud compute firewall-rules describe allow-app-5000 --project={self.project_id} 2>/dev/null"
        returncode, _, _ = self.run_command(cmd)

        if returncode == 0:
            print("Firewall rule already exists")
            return True

        # Create rule for port 5000
        cmd = f"""gcloud compute firewall-rules create allow-app-5000 \\
            --project={self.project_id} \\
            --allow=tcp:5000 \\
            --source-ranges=0.0.0.0/0 \\
            --target-tags=http-server \\
            --description='Allow traffic on port 5000 for sample app'"""

        returncode, stdout, stderr = self.run_command(
            cmd, capture_output=False)

        if returncode != 0:
            print(f"Warning: Could not create firewall rule: {stderr}")
            return False

        print("Firewall rule created successfully!")
        return True

    def get_instance_ip(self):
        """Get external IP of the instance"""
        cmd = f"gcloud compute instances describe {self.instance_name} --zone={self.zone} --project={self.project_id} --format='get(networkInterfaces[0].accessConfigs[0].natIP)'"
        returncode, stdout, stderr = self.run_command(cmd)

        if returncode == 0:
            return stdout.strip()
        return None

    def wait_for_instance(self, timeout=300):
        """Wait for instance to be running"""
        print("Waiting for instance to be ready...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            cmd = f"gcloud compute instances describe {self.instance_name} --zone={self.zone} --project={self.project_id} --format='get(status)'"
            returncode, stdout, stderr = self.run_command(cmd)

            if returncode == 0 and stdout.strip() == "RUNNING":
                print("Instance is running!")
                # Wait a bit more for SSH to be ready
                time.sleep(30)
                return True

            time.sleep(10)

        return False

    def provision(self):
        """Main provisioning workflow"""
        print("=" * 60)
        print("GCP Instance Provisioner")
        print("=" * 60)

        # Check if instance already exists
        if self.check_instance_exists():
            print(f"Instance {self.instance_name} already exists!")
            ip = self.get_instance_ip()
            if ip:
                print(f"External IP: {ip}")
            return True

        # Create instance
        if not self.create_instance():
            return False

        # Create firewall rule
        self.create_firewall_rule()

        # Wait for instance to be ready
        if not self.wait_for_instance():
            print("Timeout waiting for instance to be ready")
            return False

        # Get and display IP
        ip = self.get_instance_ip()
        if ip:
            print("=" * 60)
            print(f"✓ Instance provisioned successfully!")
            print(f"✓ Instance name: {self.instance_name}")
            print(f"✓ External IP: {ip}")
            print(f"✓ Zone: {self.zone}")
            print("=" * 60)
            print(
                f"\nSSH command: gcloud compute ssh {self.instance_name} --zone={self.zone}")
            print(f"App URL (after deployment): http://{ip}:5000")

        return True


def main():
    # Get project ID from gcloud config
    result = subprocess.run(
        "gcloud config get-value project",
        shell=True,
        capture_output=True,
        text=True
    )

    project_id = result.stdout.strip()
    if not project_id:
        print("Error: No GCP project configured")
        print("Run: gcloud config set project YOUR_PROJECT_ID")
        sys.exit(1)

    print(f"Using GCP project: {project_id}\n")

    provisioner = GCPProvisioner(project_id)
    success = provisioner.provision()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
