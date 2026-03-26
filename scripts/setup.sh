#!/bin/bash
# Setup script for the auto-scaling project

set -e

echo "======================================"
echo "Auto-Scaling Project Setup"
echo "======================================"
echo ""

# Check if Python 3 is installed
echo "[1/6] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 is not installed"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "✓ $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "[2/6] Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo ""
echo "[3/6] Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r scripts/requirements.txt
echo "✓ Dependencies installed"

# Check local VM connectivity
echo ""
echo "[4/6] Checking local VM connectivity..."
LOCAL_VM="192.168.122.10"
if ssh -o ConnectTimeout=5 sujiv@${LOCAL_VM} "echo 'Connected'" > /dev/null 2>&1; then
    echo "✓ Can connect to local VM (${LOCAL_VM})"
else
    echo "✗ Cannot connect to local VM"
    echo "  Make sure SSH key authentication is set up"
    exit 1
fi

# Check monitoring stack
echo ""
echo "[5/6] Checking monitoring stack..."
if curl -s -f "http://${LOCAL_VM}:9090/api/v1/query?query=up" > /dev/null 2>&1; then
    echo "✓ Prometheus is running"
else
    echo "✗ Prometheus is not responding"
    echo "  Run: ssh sujiv@${LOCAL_VM} 'cd ~/monitoring && docker compose up -d'"
    exit 1
fi

# Check sample app
if curl -s -f "http://${LOCAL_VM}:5000/health" > /dev/null 2>&1; then
    echo "✓ Sample application is running"
else
    echo "✗ Sample application is not responding"
    echo "  Run: ssh sujiv@${LOCAL_VM} 'cd ~/sample-app && docker run -d -p 5000:5000 sample-app:latest'"
    exit 1
fi

# Check GCP configuration
echo ""
echo "[6/6] Checking GCP configuration..."
if command -v gcloud &> /dev/null; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -n "$PROJECT_ID" ]; then
        echo "✓ gcloud CLI configured (Project: ${PROJECT_ID})"
    else
        echo "✗ No GCP project configured"
        echo "  Run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    fi
else
    echo "✗ gcloud CLI is not installed"
    exit 1
fi

echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "Quick Start Guide:"
echo "------------------"
echo ""
echo "1. Start the auto-scaler (in one terminal):"
echo "   source venv/bin/activate"
echo "   python3 scripts/autoscaler.py"
echo ""
echo "2. Trigger stress test (in another terminal):"
echo "   ./scripts/trigger_stress.sh"
echo ""
echo "3. Monitor Prometheus:"
echo "   Open http://${LOCAL_VM}:9090"
echo ""
echo "4. View application:"
echo "   curl http://${LOCAL_VM}:5000"
echo ""
echo "5. View Grafana dashboard:"
echo "   Open http://${LOCAL_VM}:3000"
echo "   Login: admin / admin123"
echo ""
