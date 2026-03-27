#!/bin/bash
# Simple trigger script to generate load
echo "Generating CPU load..."
curl -X POST http://localhost:5000/stress/cpu \
  -H "Content-Type: application/json" \
  -d '{"duration": 300, "intensity": 8}'
echo ""
echo "Load triggered! Monitor autoscaler output."
