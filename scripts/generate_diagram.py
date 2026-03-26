#!/usr/bin/env python3
"""
Architecture Diagram Generator
Creates a visual representation of the auto-scaling architecture using diagrams library.
"""

try:
    from diagrams import Diagram, Cluster, Edge
    from diagrams.onprem.compute import Server
    from diagrams.onprem.monitoring import Prometheus, Grafana
    from diagrams.onprem.container import Docker
    from diagrams.programming.language import Python
    from diagrams.gcp.compute import ComputeEngine
    from diagrams.gcp.network import FirewallRules
    print("✓ diagrams library available")
    DIAGRAMS_AVAILABLE = True
except ImportError:
    print("⚠ diagrams library not available. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "diagrams"], check=True)
    print("✓ diagrams library installed. Please run this script again.")
    DIAGRAMS_AVAILABLE = False

if DIAGRAMS_AVAILABLE:
    with Diagram("Auto-Scaling VM to Cloud Architecture",
                 filename="diagrams/architecture",
                 show=False,
                 direction="TB"):

        with Cluster("Local Environment"):
            with Cluster("Local VM (192.168.122.10)"):
                sample_app = Docker("Sample App\nPort 5000")
                node_exporter = Server("Node Exporter\nPort 9100")

            with Cluster("Monitoring Stack"):
                prometheus = Prometheus("Prometheus\nPort 9090")
                grafana = Grafana("Grafana\nPort 3000")

            # Monitoring connections
            node_exporter >> Edge(label="metrics") >> prometheus
            prometheus >> Edge(label="datasource") >> grafana

        with Cluster("Host Machine"):
            autoscaler = Python("Auto-Scaler\nOrchestrator")
            provisioner = Python("GCP\nProvisioner")
            deployer = Python("GCP\nDeployer")

        with Cluster("Google Cloud Platform"):
            with Cluster("Compute Engine"):
                gcp_instance = ComputeEngine("e2-micro\nInstance")
                firewall = FirewallRules("Firewall\nRules")

            gcp_app = Docker("Application\nContainer")

        # Main flow
        prometheus >> Edge(label="query metrics\nevery 30s",
                           style="dashed") >> autoscaler
        autoscaler >> Edge(
            label="threshold > 75%\nfor 2 minutes", color="red") >> provisioner
        provisioner >> Edge(label="create instance") >> gcp_instance
        provisioner >> Edge(label="configure") >> firewall

        autoscaler >> Edge(label="trigger deployment") >> deployer
        deployer >> Edge(label="transfer\nDocker image") >> gcp_instance
        gcp_instance >> Edge(label="load & run") >> gcp_app

        # Health check
        deployer >> Edge(label="verify health", style="dotted") >> gcp_app

    print("\n✅ Architecture diagram generated: diagrams/architecture.png")
    print("📁 Location: diagrams/architecture.png")

else:
    print("\nTo generate the diagram, run:")
    print("  pip install diagrams")
    print("  python3 scripts/generate_diagram.py")
