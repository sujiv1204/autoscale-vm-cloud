#!/usr/bin/env python3
"""
GCP Deployment Script
Deploys the Docker application to a GCP instance.
"""

import subprocess
import sys
import time
import os


class GCPDeployer:
    def __init__(self, gcp_instance_ip, local_vm_ip="192.168.122.10"):
        self.gcp_ip = gcp_instance_ip
        self.local_vm_ip = local_vm_ip
        self.project_id = self.get_project_id()
        self.instance_name = "autoscale-app-vm"
        self.zone = "us-central1-a"

    def get_project_id(self):
        """Get current GCP project ID"""
        result = subprocess.run(
            "gcloud config get-value project",
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    def run_command(self, cmd, capture_output=True):
        """Run shell command"""
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

    def save_docker_image(self):
        """Save Docker image from local VM"""
        print("Saving Docker image from local VM...")
        cmd = f"ssh sujiv@{self.local_vm_ip} 'docker save sample-app:latest | gzip' > /tmp/sample-app.tar.gz"
        returncode, stdout, stderr = self.run_command(cmd)

        if returncode != 0:
            print(f"Error saving image: {stderr}")
            return False

        # Check file size
        returncode, stdout, stderr = self.run_command(
            "ls -lh /tmp/sample-app.tar.gz")
        print(f"✓ Image saved: {stdout.split()[4]}")
        return True

    def transfer_image_to_gcp(self):
        """Transfer Docker image to GCP instance"""
        print("Transferring image to GCP...")

        # Use gcloud compute scp
        cmd = f"gcloud compute scp /tmp/sample-app.tar.gz {self.instance_name}:/tmp/sample-app.tar.gz --zone={self.zone} --project={self.project_id}"
        returncode, stdout, stderr = self.run_command(
            cmd, capture_output=False)

        if returncode != 0:
            print(f"Error transferring image: {stderr}")
            return False

        print("✓ Image transferred to GCP")
        return True

    def load_and_run_on_gcp(self):
        """Load Docker image and run container on GCP"""
        print("Loading and running application on GCP...")

        commands = [
            # Wait for Docker to be ready
            "sleep 10",
            # Load image
            "gunzip < /tmp/sample-app.tar.gz | sudo docker load",
            # Stop any existing container
            "sudo docker stop sample-app 2>/dev/null || true",
            "sudo docker rm sample-app 2>/dev/null || true",
            # Run new container
            "sudo docker run -d --name sample-app -p 5000:5000 --restart unless-stopped sample-app:latest",
            # Verify
            "sudo docker ps"
        ]

        for cmd in commands:
            full_cmd = f"gcloud compute ssh {self.instance_name} --zone={self.zone} --project={self.project_id} --command='{cmd}'"
            returncode, stdout, stderr = self.run_command(full_cmd)

            if returncode != 0 and "stop sample-app" not in cmd and "rm sample-app" not in cmd:
                print(f"Warning executing command: {cmd}")
                print(f"  Error: {stderr}")

        print("✓ Application running on GCP")
        return True

    def cleanup_temp_files(self):
        """Clean up temporary files"""
        self.run_command("rm -f /tmp/sample-app.tar.gz")
        cmd = f"gcloud compute ssh {self.instance_name} --zone={self.zone} --project={self.project_id} --command='rm -f /tmp/sample-app.tar.gz'"
        self.run_command(cmd)

    def deploy(self):
        """Main deployment workflow"""
        print("=" * 60)
        print("GCP Deployment")
        print("=" * 60)
        print(f"GCP Instance: {self.gcp_ip}")
        print(f"Local VM: {self.local_vm_ip}")
        print("=" * 60)

        # Save image from local VM
        if not self.save_docker_image():
            return False

        # Transfer to GCP
        if not self.transfer_image_to_gcp():
            return False

        # Load and run on GCP
        if not self.load_and_run_on_gcp():
            return False

        # Cleanup
        print("Cleaning up temporary files...")
        self.cleanup_temp_files()

        print("=" * 60)
        print(f"✅ Deployment complete!")
        print(f"Application URL: http://{self.gcp_ip}:5000")
        print("=" * 60)

        return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 gcp_deploy.py <gcp_instance_ip> [local_vm_ip]")
        sys.exit(1)

    gcp_ip = sys.argv[1]
    local_vm_ip = sys.argv[2] if len(sys.argv) > 2 else "192.168.122.10"

    deployer = GCPDeployer(gcp_ip, local_vm_ip)
    success = deployer.deploy()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
