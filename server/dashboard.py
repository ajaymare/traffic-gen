"""Server-side dashboard showing incoming traffic stats."""
import json
import subprocess
import time
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Traffic Server Dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a; color: #e2e8f0; min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #1e293b, #334155);
            padding: 16px 24px; border-bottom: 1px solid #475569;
            display: flex; align-items: center; justify-content: space-between;
        }
        .header h1 { font-size: 20px; font-weight: 600; color: #f97316; }
        .header .status { font-size: 12px; color: #94a3b8; }
        .container {
            max-width: 1200px; margin: 0 auto; padding: 20px;
            display: flex; flex-direction: column; gap: 20px;
        }
        .card {
            background: #1e293b; border: 1px solid #334155;
            border-radius: 8px; overflow: hidden;
        }
        .card-header {
            padding: 12px 16px; background: #334155;
            font-weight: 600; font-size: 14px;
        }
        .card-body { padding: 16px; }
        .stats-grid {
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
        }
        .stat-box {
            background: #0f172a; border: 1px solid #334155;
            border-radius: 6px; padding: 10px; text-align: center;
        }
        .stat-label { font-size: 11px; color: #94a3b8; margin-bottom: 4px; }
        .stat-value { font-size: 16px; font-weight: 700; color: #f97316; }
        .services-grid {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px;
        }
        .service-card {
            background: #0f172a; border: 1px solid #334155;
            border-radius: 6px; padding: 12px;
        }
        .service-header {
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 8px;
        }
        .service-name { font-weight: 600; font-size: 14px; color: #f97316; text-transform: uppercase; }
        .service-badge {
            font-size: 11px; padding: 2px 8px; border-radius: 10px;
        }
        .service-badge.active { background: #166534; color: #86efac; }
        .service-badge.idle { background: #475569; color: #94a3b8; }
        .service-stat {
            display: flex; justify-content: space-between;
            font-size: 12px; padding: 3px 0; border-bottom: 1px solid #1e293b;
        }
        .service-stat-label { color: #94a3b8; }
        .service-stat-value { color: #e2e8f0; font-weight: 500; }
        .connections-table {
            width: 100%; border-collapse: collapse; font-size: 12px;
        }
        .connections-table th {
            text-align: left; padding: 6px 8px; background: #0f172a;
            color: #94a3b8; font-weight: 500; border-bottom: 1px solid #334155;
        }
        .connections-table td {
            padding: 5px 8px; border-bottom: 1px solid #1e293b; color: #e2e8f0;
        }
        .connections-table tr:hover td { background: #334155; }
        @media (max-width: 900px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>

<div class="header">
    <h1>Traffic Server Dashboard</h1>
    <div class="status">Auto-refresh: 2s | <span id="last-update">--</span></div>
</div>

<div class="container">
    <!-- Aggregate Stats -->
    <div class="card">
        <div class="card-header">Aggregate Traffic</div>
        <div class="card-body">
            <div class="stats-grid">
                <div class="stat-box"><div class="stat-label">Total Bytes Received</div><div class="stat-value" id="total-recv">0 B</div></div>
                <div class="stat-box"><div class="stat-label">Total Bytes Sent</div><div class="stat-value" id="total-sent">0 B</div></div>
                <div class="stat-box"><div class="stat-label">Total Requests</div><div class="stat-value" id="total-reqs">0</div></div>
                <div class="stat-box"><div class="stat-label">Active Connections</div><div class="stat-value" id="total-conns">0</div></div>
            </div>
        </div>
    </div>

    <!-- Per-Service Stats -->
    <div class="card">
        <div class="card-header">Services</div>
        <div class="card-body">
            <div class="services-grid" id="services-grid"></div>
        </div>
    </div>

    <!-- Active Connections -->
    <div class="card">
        <div class="card-header">Active Connections</div>
        <div class="card-body">
            <table class="connections-table">
                <thead>
                    <tr><th>Protocol</th><th>Local Port</th><th>Remote Address</th><th>State</th></tr>
                </thead>
                <tbody id="conn-table-body">
                    <tr><td colspan="4" style="text-align:center;color:#94a3b8">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<script>
function fmtBytes(b) {
    if (b < 1024) return b + ' B';
    if (b < 1048576) return (b / 1024).toFixed(1) + ' KB';
    if (b < 1073741824) return (b / 1048576).toFixed(1) + ' MB';
    return (b / 1073741824).toFixed(2) + ' GB';
}

async function poll() {
    try {
        const resp = await fetch('/api/server-stats');
        const data = await resp.json();

        // Aggregate
        document.getElementById('total-recv').textContent = fmtBytes(data.aggregate.bytes_recv);
        document.getElementById('total-sent').textContent = fmtBytes(data.aggregate.bytes_sent);
        document.getElementById('total-reqs').textContent = data.aggregate.requests.toLocaleString();
        document.getElementById('total-conns').textContent = data.aggregate.active_connections;

        // Services
        const grid = document.getElementById('services-grid');
        grid.innerHTML = '';
        for (const [name, svc] of Object.entries(data.services)) {
            const active = svc.active_connections > 0;
            const badge = active
                ? '<span class="service-badge active">' + svc.active_connections + ' conn</span>'
                : '<span class="service-badge idle">Idle</span>';

            let statsHtml = '';
            for (const [k, v] of Object.entries(svc.stats)) {
                const label = k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                const val = k.includes('bytes') ? fmtBytes(v) : v.toLocaleString();
                statsHtml += '<div class="service-stat"><span class="service-stat-label">' +
                    label + '</span><span class="service-stat-value">' + val + '</span></div>';
            }

            grid.innerHTML += '<div class="service-card"><div class="service-header">' +
                '<span class="service-name">' + name + '</span>' + badge +
                '</div>' + statsHtml + '</div>';
        }

        // Connections table
        const tbody = document.getElementById('conn-table-body');
        if (data.connections.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#94a3b8">No active connections</td></tr>';
        } else {
            tbody.innerHTML = data.connections.map(c =>
                '<tr><td>' + c.proto + '</td><td>' + c.local_port + '</td><td>' +
                c.remote + '</td><td>' + c.state + '</td></tr>'
            ).join('');
        }

        document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
    } catch (e) { /* ignore */ }
}

setInterval(poll, 2000);
poll();
</script>
</body>
</html>
"""


def read_json_file(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_active_connections():
    """Use ss to get active connections on monitored ports."""
    ports = {
        80: 'HTTP', 443: 'HTTPS', 5201: 'iperf3',
        9999: 'TCP Echo', 9998: 'UDP Echo',
        21: 'FTP', 22: 'SSH',
    }
    connections = []
    try:
        result = subprocess.run(
            ['ss', '-tunp', '--no-header'],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            proto = parts[0].upper()
            local = parts[3]
            remote = parts[4]
            state = parts[0] if proto == 'UDP' else (parts[1] if len(parts) > 1 else '')
            # Extract local port
            local_port = local.rsplit(':', 1)[-1] if ':' in local else ''
            try:
                port_num = int(local_port)
            except ValueError:
                continue
            if port_num in ports:
                # Parse state properly
                if proto.startswith('TCP'):
                    state = parts[1] if len(parts) > 1 else 'UNKNOWN'
                else:
                    state = 'UNCONN'
                connections.append({
                    'proto': ports[port_num],
                    'local_port': port_num,
                    'remote': remote,
                    'state': state,
                })
    except Exception:
        pass
    return connections


def count_connections_by_port():
    """Count active connections per port."""
    counts = {}
    try:
        result = subprocess.run(
            ['ss', '-tun', '--no-header'],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            local = parts[3]
            local_port = local.rsplit(':', 1)[-1]
            try:
                port_num = int(local_port)
                counts[port_num] = counts.get(port_num, 0) + 1
            except ValueError:
                continue
    except Exception:
        pass
    return counts


@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/server-stats')
def server_stats():
    http = read_json_file('/tmp/http_stats.json')
    echo = read_json_file('/tmp/echo_stats.json')
    conn_counts = count_connections_by_port()
    connections = get_active_connections()

    tcp_echo = echo.get('tcp', {})
    udp_echo = echo.get('udp', {})

    total_recv = http.get('bytes_recv', 0) + tcp_echo.get('bytes_recv', 0) + udp_echo.get('bytes_recv', 0)
    total_sent = http.get('bytes_sent', 0) + tcp_echo.get('bytes_sent', 0) + udp_echo.get('bytes_sent', 0)
    total_reqs = http.get('requests', 0) + tcp_echo.get('connections', 0) + udp_echo.get('packets', 0)
    total_conns = sum(conn_counts.values())

    services = {
        'HTTP/HTTPS': {
            'active_connections': conn_counts.get(80, 0) + conn_counts.get(443, 0),
            'stats': {
                'requests': http.get('requests', 0),
                'bytes_recv': http.get('bytes_recv', 0),
                'bytes_sent': http.get('bytes_sent', 0),
                'uploads': http.get('uploads', 0),
                'downloads': http.get('downloads', 0),
            }
        },
        'TCP Echo': {
            'active_connections': conn_counts.get(9999, 0),
            'stats': {
                'total_connections': tcp_echo.get('connections', 0),
                'active': tcp_echo.get('active', 0),
                'bytes_recv': tcp_echo.get('bytes_recv', 0),
                'bytes_sent': tcp_echo.get('bytes_sent', 0),
            }
        },
        'UDP Echo': {
            'active_connections': conn_counts.get(9998, 0),
            'stats': {
                'packets': udp_echo.get('packets', 0),
                'bytes_recv': udp_echo.get('bytes_recv', 0),
                'bytes_sent': udp_echo.get('bytes_sent', 0),
            }
        },
        'iperf3': {
            'active_connections': conn_counts.get(5201, 0),
            'stats': {}
        },
        'FTP': {
            'active_connections': conn_counts.get(21, 0),
            'stats': {}
        },
        'SSH': {
            'active_connections': conn_counts.get(22, 0),
            'stats': {}
        },
    }

    return jsonify({
        'aggregate': {
            'bytes_recv': total_recv,
            'bytes_sent': total_sent,
            'requests': total_reqs,
            'active_connections': total_conns,
        },
        'services': services,
        'connections': connections,
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082)
