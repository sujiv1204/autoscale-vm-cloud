#!/usr/bin/env python3
"""
Auto-Scaling Orchestrator
Monitors local VM resource usage via Prometheus and triggers cloud scaling when thresholds are exceeded.
"""

import requests
import time
import json
import subprocess
import sys
from datetime import datetime
import os


class AutoScaler:
    def __init__(self, prometheus_url, threshold_cpu=75, threshold_memory=75, check_interval=30):
        self.prometheus_url = prometheus_url
        self.threshold_cpu = threshold_cpu
        self.threshold_memory = threshold_memory
        self.check_interval = check_interval
        self.consecutive_violations = 0
        self.required_violations = 4  # 2 minutes at 30-second intervals
        self.scaled = False
        self.gcp_instance_ip = None

    def query_prometheus(self, query):
        """Query Prometheus API"""
        try:
            url = f"{self.prometheus_url}/api/v1/query"
            response = requests.get(url, params={'query': query}, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['status'] == 'success' and data['data']['result']:
                return float(data['data']['result'][0]['value'][1])
            return None
        except Exception as e:
            print(f"Error querying Prometheus: {e}")
            return None

    def get_cpu_usage(self):
        """Get CPU usage percentage from Prometheus"""
        # Query: 100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)
        query = '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)'
        return self.query_prometheus(query)

    def get_memory_usage(self):
        """Get memory usage percentage from Prometheus"""
        # Query: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
        query = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
        return self.query_prometheus(query)

    def check_thresholds(self):
        """Check if resource usage exceeds thresholds"""
        cpu_usage = self.get_cpu_usage()
        memory_usage = self.get_memory_usage()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if cpu_usage is None or memory_usage is None:
            print(f"[{timestamp}] Warning: Could not retrieve metrics")
            return False

        print(f"[{timestamp}] CPU: {cpu_usage:.2f}% | Memory: {memory_usage:.2f}%")

        # Check if either threshold is exceeded
        threshold_exceeded = (cpu_usage >= self.threshold_cpu or
                              memory_usage >= self.threshold_memory)

        if threshold_exceeded:
            self.consecutive_violations += 1
            print(
                f"  ⚠️  THRESHOLD EXCEEDED! (Consecutive: {self.consecutive_violations}/{self.required_violations})")

            if self.consecutive_violations >= self.required_violations:
                return True
        else:
            if self.consecutive_violations > 0:
                print(
                    f"  ✓ Back to normal (Resetting counter from {self.consecutive_violations})")
            self.consecutive_violations = 0

        return False

    def trigger_scaling(self):
        """Trigger scaling to GCP"""
        print("\n" + "=" * 60)
        print("🚀 INITIATING CLOUD SCALING")
        print("=" * 60)

        # Step 1: Provision GCP instance
        print("\n[Step 1/4] Provisioning GCP instance...")
        result = subprocess.run(
            ["python3", "scripts/gcp_provision.py"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Error provisioning GCP instance: {result.stderr}")
            return False

        print(result.stdout)

        # Extract IP address
        for line in result.stdout.split('\n'):
            if 'External IP:' in line:
                self.gcp_instance_ip = line.split(':')[1].strip()

        if not self.gcp_instance_ip:
            print("Error: Could not determine GCP instance IP")
            return False

        print(f"✓ GCP instance ready at {self.gcp_instance_ip}")

        # Step 2: Transfer Docker image
        print("\n[Step 2/4] Transferring application to GCP...")
        result = subprocess.run(
            ["python3", "scripts/gcp_deploy.py", self.gcp_instance_ip],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Warning: Deployment encountered issues: {result.stderr}")
        else:
            print(result.stdout)
            print("✓ Application deployed to GCP")

        # Step 3: Verify deployment
        print("\n[Step 3/4] Verifying deployment...")
        time.sleep(10)

        try:
            response = requests.get(
                f"http://{self.gcp_instance_ip}:5000/health", timeout=10)
            if response.status_code == 200:
                print("✓ Application is healthy on GCP")
            else:
                print(
                    f"Warning: Health check returned status {response.status_code}")
        except Exception as e:
            print(f"Warning: Could not verify deployment: {e}")

        # Step 4: Log scaling event
        print("\n[Step 4/4] Logging scaling event...")
        self.log_scaling_event()

        print("\n" + "=" * 60)
        print("✅ CLOUD SCALING COMPLETE")
        print(
            f"Application now running at: http://{self.gcp_instance_ip}:5000")
        print("=" * 60)

        self.scaled = True
        return True

    def log_scaling_event(self):
        """Log scaling event to file"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'auto_scale_triggered',
            'gcp_instance_ip': self.gcp_instance_ip,
            'threshold_cpu': self.threshold_cpu,
            'threshold_memory': self.threshold_memory
        }

        os.makedirs('logs', exist_ok=True)
        with open('logs/scaling_events.json', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

        print(f"✓ Event logged to logs/scaling_events.json")

    def run(self):
        """Main monitoring loop"""
        print("=" * 60)
        print("Auto-Scaling Orchestrator Started")
        print("=" * 60)
        print(f"Prometheus URL: {self.prometheus_url}")
        print(f"CPU Threshold: {self.threshold_cpu}%")
        print(f"Memory Threshold: {self.threshold_memory}%")
        print(f"Check Interval: {self.check_interval} seconds")
        print(f"Required Violations: {self.required_violations} consecutive")
        print("=" * 60)
        print("\nMonitoring started. Press Ctrl+C to stop.\n")

        try:
            while not self.scaled:
                if self.check_thresholds():
                    print("\n⚠️  Sustained threshold violation detected!")
                    if self.trigger_scaling():
                        print("\n✅ Scaling complete. Monitoring will continue...")
                        # Continue monitoring but don't scale again
                        self.scaled = True
                    else:
                        print(
                            "\n❌ Scaling failed. Resetting and continuing monitoring...")
                        self.consecutive_violations = 0

                time.sleep(self.check_interval)

            # After scaling, just monitor
            while True:
                cpu_usage = self.get_cpu_usage()
                memory_usage = self.get_memory_usage()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if cpu_usage is not None and memory_usage is not None:
                    print(
                        f"[{timestamp}] CPU: {cpu_usage:.2f}% | Memory: {memory_usage:.2f}% | Status: Scaled to GCP")

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user.")
            sys.exit(0)


def main():
    # Configuration
    PROMETHEUS_URL = "http://192.168.122.10:9090"
    CPU_THRESHOLD = 75  # percent
    MEMORY_THRESHOLD = 75  # percent
    CHECK_INTERVAL = 30  # seconds

    # Allow override via environment variables
    prometheus_url = os.getenv('PROMETHEUS_URL', PROMETHEUS_URL)
    cpu_threshold = int(os.getenv('CPU_THRESHOLD', CPU_THRESHOLD))
    memory_threshold = int(os.getenv('MEMORY_THRESHOLD', MEMORY_THRESHOLD))
    check_interval = int(os.getenv('CHECK_INTERVAL', CHECK_INTERVAL))

    scaler = AutoScaler(
        prometheus_url=prometheus_url,
        threshold_cpu=cpu_threshold,
        threshold_memory=memory_threshold,
        check_interval=check_interval
    )

    scaler.run()


if __name__ == "__main__":
    main()
