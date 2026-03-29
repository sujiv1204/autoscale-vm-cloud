#!/usr/bin/env python3
"""
Sample Application for Auto-Scaling Demo
Flask app with a visual dashboard showing system info and environment detection.
"""

from flask import Flask, jsonify, request, render_template_string
import time
import os
import socket
import platform
import psutil

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auto-Scale Demo App</title>
    <meta http-equiv="refresh" content="5">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #0f1923;
            color: #c9d1d9;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }

        .container {
            max-width: 720px;
            width: 100%;
        }

        .header {
            text-align: center;
            margin-bottom: 2rem;
        }

        .header h1 {
            font-size: 1.6rem;
            font-weight: 600;
            color: #e6edf3;
            margin-bottom: 0.5rem;
        }

        .badge {
            display: inline-block;
            padding: 0.3rem 0.9rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }

        .badge-local {
            background: #1a3a2a;
            color: #3fb950;
            border: 1px solid #2a5a3a;
        }

        .badge-cloud {
            background: #1a2a3a;
            color: #58a6ff;
            border: 1px solid #2a3a5a;
        }

        .cards {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .card {
            background: #161b22;
            border: 1px solid #21262d;
            border-radius: 8px;
            padding: 1.2rem;
        }

        .card-full {
            grid-column: 1 / -1;
        }

        .card-label {
            font-size: 0.75rem;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }

        .card-value {
            font-size: 1.4rem;
            font-weight: 600;
            color: #e6edf3;
        }

        .card-value.small {
            font-size: 0.95rem;
            font-weight: 400;
        }

        .meter {
            margin-top: 0.6rem;
            background: #21262d;
            border-radius: 4px;
            height: 6px;
            overflow: hidden;
        }

        .meter-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.4s ease;
        }

        .meter-fill.green { background: #3fb950; }
        .meter-fill.yellow { background: #d29922; }
        .meter-fill.red { background: #f85149; }

        .info-table {
            background: #161b22;
            border: 1px solid #21262d;
            border-radius: 8px;
            padding: 1.2rem;
            margin-bottom: 1rem;
        }

        .info-table h3 {
            font-size: 0.85rem;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.8rem;
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 0.4rem 0;
            border-bottom: 1px solid #21262d;
            font-size: 0.85rem;
        }

        .info-row:last-child { border-bottom: none; }

        .info-key {
            color: #8b949e;
        }

        .info-val {
            font-family: 'Consolas', 'Monaco', monospace;
            color: #e6edf3;
        }

        .footer {
            text-align: center;
            margin-top: 1.5rem;
            font-size: 0.75rem;
            color: #484f58;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Auto-Scale Demo Application</h1>
            <span class="badge {{ 'badge-cloud' if is_cloud else 'badge-local' }}">
                Running on {{ 'Cloud (GCP)' if is_cloud else 'Local VM' }}
            </span>
        </div>

        <div class="cards">
            <div class="card">
                <div class="card-label">CPU Usage</div>
                <div class="card-value">{{ cpu_percent }}%</div>
                <div class="meter">
                    <div class="meter-fill {{ 'red' if cpu_percent > 75 else 'yellow' if cpu_percent > 50 else 'green' }}"
                         style="width: {{ cpu_percent }}%"></div>
                </div>
            </div>
            <div class="card">
                <div class="card-label">Memory Usage</div>
                <div class="card-value">{{ mem_percent }}%</div>
                <div class="meter">
                    <div class="meter-fill {{ 'red' if mem_percent > 75 else 'yellow' if mem_percent > 50 else 'green' }}"
                         style="width: {{ mem_percent }}%"></div>
                </div>
            </div>
            <div class="card">
                <div class="card-label">CPU Cores</div>
                <div class="card-value">{{ cpu_count }}</div>
            </div>
            <div class="card">
                <div class="card-label">Memory Total</div>
                <div class="card-value">{{ mem_total_mb }} MB</div>
            </div>
            <div class="card">
                <div class="card-label">Disk Usage</div>
                <div class="card-value">{{ disk_percent }}%</div>
                <div class="meter">
                    <div class="meter-fill {{ 'red' if disk_percent > 75 else 'yellow' if disk_percent > 50 else 'green' }}"
                         style="width: {{ disk_percent }}%"></div>
                </div>
            </div>
            <div class="card">
                <div class="card-label">Uptime</div>
                <div class="card-value small">{{ uptime }}</div>
            </div>
        </div>

        <div class="info-table">
            <h3>Server Information</h3>
            <div class="info-row">
                <span class="info-key">Hostname</span>
                <span class="info-val">{{ hostname }}</span>
            </div>
            <div class="info-row">
                <span class="info-key">Platform</span>
                <span class="info-val">{{ platform_info }}</span>
            </div>
            <div class="info-row">
                <span class="info-key">Accessed Via</span>
                <span class="info-val">{{ request_host }}</span>
            </div>
            <div class="info-row">
                <span class="info-key">Environment</span>
                <span class="info-val">{{ deploy_env }}</span>
            </div>
            <div class="info-row">
                <span class="info-key">Container ID</span>
                <span class="info-val">{{ container_id }}</span>
            </div>
        </div>

        <div class="info-table">
            <h3>API Endpoints</h3>
            <div class="info-row">
                <span class="info-val">GET /health</span>
                <span class="info-key">Health check</span>
            </div>
            <div class="info-row">
                <span class="info-val">GET /metrics</span>
                <span class="info-key">System metrics (JSON)</span>
            </div>
        </div>

        <div class="footer">
            Auto-Scale Demo | Page refreshes every 5 seconds | {{ timestamp }}
        </div>
    </div>
</body>
</html>
"""


def get_deploy_env():
    """Get deployment environment from env var"""
    return os.environ.get('DEPLOY_ENV', 'local')


def get_container_id():
    """Get Docker container ID from hostname (Docker sets hostname to container ID)"""
    hostname = socket.gethostname()
    # Docker container hostnames are 12-char hex strings
    if len(hostname) == 12 and all(c in '0123456789abcdef' for c in hostname):
        return hostname
    return hostname


def get_uptime():
    """Get system uptime as readable string"""
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


@app.route('/')
def home():
    """Dashboard page"""
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    is_cloud = get_deploy_env() == 'cloud'

    return render_template_string(HTML_TEMPLATE,
        hostname=socket.gethostname(),
        platform_info=f"{platform.system()} {platform.release()}",
        cpu_percent=round(cpu_percent, 1),
        cpu_count=psutil.cpu_count(),
        mem_percent=round(memory.percent, 1),
        mem_total_mb=round(memory.total / (1024 * 1024)),
        disk_percent=round(disk.percent, 1),
        uptime=get_uptime(),
        request_host=request.host,
        deploy_env="Cloud (GCP)" if is_cloud else "Local VM",
        container_id=get_container_id(),
        is_cloud=is_cloud,
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
    )


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'hostname': socket.gethostname(),
        'environment': get_deploy_env(),
        'timestamp': time.time()
    })


@app.route('/metrics')
def metrics():
    """Return current system metrics"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return jsonify({
        'hostname': socket.gethostname(),
        'environment': get_deploy_env(),
        'cpu': {
            'percent': cpu_percent,
            'count': psutil.cpu_count()
        },
        'memory': {
            'total_mb': round(memory.total / (1024 * 1024)),
            'used_mb': round(memory.used / (1024 * 1024)),
            'percent': memory.percent
        },
        'disk': {
            'total_gb': round(disk.total / (1024 * 1024 * 1024), 1),
            'used_gb': round(disk.used / (1024 * 1024 * 1024), 1),
            'percent': disk.percent
        }
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
