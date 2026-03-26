#!/bin/bash
# Trigger stress test on local VM to test auto-scaling

LOCAL_VM="192.168.122.10"
APP_URL="http://${LOCAL_VM}:5000"

echo "======================================"
echo "Auto-Scaling Stress Test Trigger"
echo "======================================"
echo "Target: $APP_URL"
echo ""

# Check if app is running
echo "[1/3] Checking if application is running..."
if curl -s -f "${APP_URL}/health" > /dev/null 2>&1; then
    echo "✓ Application is running"
else
    echo "✗ Application is not responding"
    exit 1
fi

# Show current metrics
echo ""
echo "[2/3] Current system metrics:"
curl -s "${APP_URL}/metrics" | jq '{cpu: .cpu, memory: .memory}'

# Trigger CPU stress test
echo ""
echo "[3/3] Triggering stress test..."
echo "  • Duration: 300 seconds (5 minutes)"
echo "  • Type: CPU stress (2 threads)"
echo ""

# Start CPU stress (high intensity for 5 minutes)
curl -s -X POST "${APP_URL}/stress/cpu" \
  -H "Content-Type: application/json" \
  -d '{"duration": 300, "intensity": 2}' | jq .

echo ""
echo "======================================"
echo "✓ Stress test initiated!"
echo "======================================"
echo ""
echo "The auto-scaler should detect this within 2 minutes"
echo "Monitor the autoscaler output for scaling events."
echo ""
echo "To check current metrics:"
echo "  curl -s ${APP_URL}/metrics | jq ."
echo ""
echo "To stop the stress test early:"
echo "  curl -s -X POST ${APP_URL}/stress/stop | jq ."
