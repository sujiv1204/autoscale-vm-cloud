#!/usr/bin/env python3
"""
Sample Load Generator Application
This Flask app provides endpoints to simulate CPU and memory stress for testing auto-scaling.
"""

from flask import Flask, jsonify, request
import multiprocessing
import time
import os
import sys
import threading
import psutil

app = Flask(__name__)

# Global variables for stress tests
stress_threads = []
stop_stress = False

def cpu_stress_worker(duration):
    """Worker function to stress CPU"""
    global stop_stress
    end_time = time.time() + duration
    while time.time() < end_time and not stop_stress:
        # Busy loop to consume CPU
        _ = sum(i * i for i in range(10000))

def memory_stress_worker(size_mb, duration):
    """Worker function to stress memory"""
    global stop_stress
    end_time = time.time() + duration
    # Allocate memory
    data = []
    chunk_size = 1024 * 1024  # 1MB chunks
    for _ in range(size_mb):
        if time.time() >= end_time or stop_stress:
            break
        data.append(b'0' * chunk_size)
        time.sleep(0.1)  # Small delay to avoid instant allocation
    
    # Hold memory until duration expires
    while time.time() < end_time and not stop_stress:
        time.sleep(0.5)

@app.route('/')
def home():
    """Home endpoint with API documentation"""
    return jsonify({
        'app': 'Auto-Scaling Demo Application',
        'version': '1.0',
        'endpoints': {
            '/': 'This help page',
            '/health': 'Health check endpoint',
            '/metrics': 'Current system metrics',
            '/stress/cpu': 'POST - Generate CPU load (params: duration, intensity)',
            '/stress/memory': 'POST - Generate memory load (params: duration, size_mb)',
            '/stress/stop': 'POST - Stop all active stress tests'
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time()
    })

@app.route('/metrics')
def metrics():
    """Return current system metrics"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return jsonify({
        'cpu': {
            'percent': cpu_percent,
            'count': psutil.cpu_count()
        },
        'memory': {
            'total_mb': memory.total / (1024 * 1024),
            'used_mb': memory.used / (1024 * 1024),
            'percent': memory.percent
        },
        'disk': {
            'total_gb': disk.total / (1024 * 1024 * 1024),
            'used_gb': disk.used / (1024 * 1024 * 1024),
            'percent': disk.percent
        }
    })

@app.route('/stress/cpu', methods=['POST'])
def stress_cpu():
    """Generate CPU load"""
    global stress_threads, stop_stress
    
    data = request.get_json() or {}
    duration = int(data.get('duration', 60))  # seconds
    intensity = int(data.get('intensity', 1))  # number of threads
    
    # Limit intensity to prevent excessive load
    max_intensity = psutil.cpu_count() or 1
    intensity = min(intensity, max_intensity * 8)  # Allow up to 8x CPU count for stress testing
    
    stop_stress = False
    
    # Start stress threads
    for i in range(intensity):
        thread = threading.Thread(target=cpu_stress_worker, args=(duration,))
        thread.daemon = True
        thread.start()
        stress_threads.append(thread)
    
    return jsonify({
        'status': 'started',
        'type': 'cpu',
        'duration': duration,
        'threads': intensity,
        'message': f'CPU stress test started with {intensity} threads for {duration} seconds'
    })

@app.route('/stress/memory', methods=['POST'])
def stress_memory():
    """Generate memory load"""
    global stress_threads, stop_stress
    
    data = request.get_json() or {}
    duration = int(data.get('duration', 60))  # seconds
    size_mb = int(data.get('size_mb', 500))  # MB to allocate
    
    # Get available memory
    memory = psutil.virtual_memory()
    available_mb = memory.available / (1024 * 1024)
    
    # Limit size to 80% of available memory
    max_size = int(available_mb * 0.8)
    size_mb = min(size_mb, max_size)
    
    stop_stress = False
    
    # Start memory stress thread
    thread = threading.Thread(target=memory_stress_worker, args=(size_mb, duration))
    thread.daemon = True
    thread.start()
    stress_threads.append(thread)
    
    return jsonify({
        'status': 'started',
        'type': 'memory',
        'duration': duration,
        'size_mb': size_mb,
        'message': f'Memory stress test started allocating {size_mb}MB for {duration} seconds'
    })

@app.route('/stress/stop', methods=['POST'])
def stop_stress_test():
    """Stop all active stress tests"""
    global stop_stress, stress_threads
    
    stop_stress = True
    active_count = len([t for t in stress_threads if t.is_alive()])
    
    # Clear the threads list
    stress_threads = []
    
    return jsonify({
        'status': 'stopped',
        'message': f'Stopped {active_count} active stress test(s)'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
