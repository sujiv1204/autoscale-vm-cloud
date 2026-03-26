#!/bin/bash
# Test script for the sample application

BASE_URL="http://localhost:5000"

echo "=== Testing Sample Application ==="
echo ""

# Test health endpoint
echo "1. Testing health endpoint..."
curl -s $BASE_URL/health | jq .
echo ""

# Test metrics endpoint
echo "2. Testing metrics endpoint..."
curl -s $BASE_URL/metrics | jq .
echo ""

# Test CPU stress (10 seconds, 1 thread)
echo "3. Starting CPU stress test (10 seconds)..."
curl -s -X POST $BASE_URL/stress/cpu \
  -H "Content-Type: application/json" \
  -d '{"duration": 10, "intensity": 1}' | jq .
echo ""

echo "4. Waiting 5 seconds..."
sleep 5

# Check metrics during stress
echo "5. Checking metrics during stress..."
curl -s $BASE_URL/metrics | jq .
echo ""

echo "6. Waiting for stress test to complete..."
sleep 6

# Test memory stress (10 seconds, 100MB)
echo "7. Starting memory stress test (10 seconds, 100MB)..."
curl -s -X POST $BASE_URL/stress/memory \
  -H "Content-Type: application/json" \
  -d '{"duration": 10, "size_mb": 100}' | jq .
echo ""

echo "8. Checking metrics during memory stress..."
sleep 2
curl -s $BASE_URL/metrics | jq .
echo ""

echo "=== Tests Complete ==="
