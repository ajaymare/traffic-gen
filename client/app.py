"""Traffic Generator Client — Flask Web UI + REST API."""
import os
import socket
import logging
import subprocess
from flask import Flask, render_template, jsonify, request

from traffic_engine import TrafficEngine
import network_shaper
from router_shaper import router_manager

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s')

app = Flask(__name__)
engine = TrafficEngine()

SERVER_HOST = os.environ.get('SERVER_HOST', 'server')


def _get_json():
    """Safely get JSON from request, returning empty dict on None."""
    return request.json or {}


@app.route('/')
def dashboard():
    return render_template('dashboard.html', server_host=SERVER_HOST)


@app.route('/api/server_host')
def get_server_host():
    return jsonify({"server_host": SERVER_HOST})


@app.route('/api/status')
def status():
    return jsonify({
        "jobs": engine.get_status(),
        "shaping": network_shaper.get_current_settings(),
    })


@app.route('/api/start', methods=['POST'])
def start_traffic():
    data = _get_json()
    protocol = data.get('protocol')
    config = data.get('config', {})
    if not protocol:
        return jsonify({"error": "protocol required"}), 400
    ok, msg = engine.start_job(protocol, config)
    return jsonify({"ok": ok, "message": msg}), 200 if ok else 409


@app.route('/api/stop', methods=['POST'])
def stop_traffic():
    data = _get_json()
    protocol = data.get('protocol')
    if not protocol:
        return jsonify({"error": "protocol required"}), 400
    if protocol == 'all':
        engine.stop_all()
        return jsonify({"ok": True, "message": "Stopping all"})
    ok, msg = engine.stop_job(protocol)
    return jsonify({"ok": ok, "message": msg}), 200 if ok else 404


@app.route('/api/sudo', methods=['GET'])
def sudo_auth():
    return jsonify({"authenticated": True})


# ─── Router Link Simulation ──────────────────────────────

@app.route('/api/routers', methods=['GET'])
def list_routers():
    return jsonify(router_manager.list_routers())


@app.route('/api/routers', methods=['POST'])
def add_router():
    d = _get_json()
    name = d.get('name', '')
    ip = d.get('ip', '')
    username = d.get('username', '')
    password = d.get('password', '')
    ok, msg, data = router_manager.add_router(name, ip, username, password)
    if ok:
        return jsonify({"ok": True, "message": msg, "router": data})
    return jsonify({"ok": False, "error": msg}), 400


@app.route('/api/routers/<router_id>', methods=['DELETE'])
def remove_router(router_id):
    ok, msg = router_manager.remove_router(router_id)
    return jsonify({"ok": ok, "message": msg}), 200 if ok else 404


@app.route('/api/routers/<router_id>/connect', methods=['POST'])
def connect_router(router_id):
    ok, msg = router_manager.connect(router_id)
    return jsonify({"ok": ok, "message": msg}), 200 if ok else 400


@app.route('/api/routers/<router_id>/disconnect', methods=['POST'])
def disconnect_router(router_id):
    ok, msg = router_manager.disconnect(router_id)
    return jsonify({"ok": ok, "message": msg})


@app.route('/api/routers/<router_id>/interfaces')
def router_interfaces(router_id):
    interfaces = router_manager.discover_interfaces(router_id)
    return jsonify({"interfaces": interfaces})


@app.route('/api/routers/<router_id>/select-interface', methods=['POST'])
def router_select_interface(router_id):
    d = _get_json()
    iface = d.get('interface', '')
    ok, msg = router_manager.select_interface(router_id, iface)
    return jsonify({"ok": ok, "message": msg}), 200 if ok else 400


@app.route('/api/routers/<router_id>/mode', methods=['POST'])
def router_set_mode(router_id):
    d = _get_json()
    mode = d.get('mode', '')
    config = {
        'latency_ms': int(d.get('latency_ms', 0)),
        'jitter_ms': int(d.get('jitter_ms', 0)),
        'packet_loss_pct': float(d.get('packet_loss_pct', 0)),
        'bandwidth_mbps': int(d.get('bandwidth_mbps', 0)),
    }
    ok, msg = router_manager.apply_mode(router_id, mode, config)
    return jsonify({"ok": ok, "message": msg}), 200 if ok else 400


@app.route('/api/routers/<router_id>/status')
def router_status(router_id):
    return jsonify(router_manager.get_status(router_id))


@app.route('/api/topology')
def topology():
    """Return topology data: client IP, routers, server, running protocols."""
    # Client IP
    client_ip = '--'
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((SERVER_HOST, 80))
        client_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    # Running protocols and their destinations
    status = engine.get_status()
    protocols = []
    for proto, info in status.items():
        if info.get('running'):
            cfg = info.get('config', {})
            dest = cfg.get('host', SERVER_HOST)
            port = cfg.get('port', '')
            if 'url' in cfg:
                dest = cfg['url']
            protocols.append({
                'name': proto,
                'dest': dest,
                'port': str(port),
                'running': True,
            })

    # Routers
    routers = router_manager.list_routers()

    return jsonify({
        'client_ip': client_ip,
        'server_host': SERVER_HOST,
        'routers': routers,
        'protocols': protocols,
    })


@app.route('/api/shaping/random_bandwidth', methods=['POST'])
def toggle_random_bandwidth():
    d = _get_json()
    enabled = d.get('enabled', False)
    try:
        min_mbps = int(d.get('min_mbps', 20))
        max_mbps = int(d.get('max_mbps', 1000))
        interval = int(d.get('interval', 10))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid parameters"}), 400
    if enabled:
        network_shaper.start_random_bandwidth(min_mbps, max_mbps, interval)
        return jsonify({"ok": True, "message": f"Random bandwidth {min_mbps}-{max_mbps} Mbps every {interval}s"})
    else:
        network_shaper.stop_random_bandwidth()
        return jsonify({"ok": True, "message": "Random bandwidth stopped"})


@app.route('/api/interface', methods=['GET', 'POST'])
def interface():
    if request.method == 'POST':
        d = _get_json()
        iface = d.get('interface', '').strip()
        if not iface:
            return jsonify({"error": "interface required"}), 400
        # Validate interface exists inside the container
        try:
            result = subprocess.run(
                ['ip', 'link', 'show', iface],
                capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return jsonify({"error": f"Interface '{iface}' not found in container. Use 'ip link' inside the container to see available interfaces."}), 400
        except Exception:
            pass
        network_shaper.INTERFACE = iface
        return jsonify({"ok": True, "interface": iface,
                        "message": f"Interface changed to {iface}"})
    return jsonify({"interface": network_shaper.INTERFACE})


@app.route('/api/source_ips', methods=['GET', 'POST'])
def source_ips():
    if request.method == 'POST':
        d = _get_json()
        enabled = d.get('enabled', False)
        if enabled:
            base_ip = d.get('base_ip', '172.18.0.100')
            count = int(d.get('count', 5))
            try:
                added = network_shaper.add_ip_aliases(base_ip, count)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            return jsonify({"ok": True, "message": f"Added {len(added)} source IPs",
                            "ips": added})
        else:
            network_shaper.remove_ip_aliases()
            return jsonify({"ok": True, "message": "Source IPs removed", "ips": []})
    else:
        ips = network_shaper.get_alias_ips()
        return jsonify({"enabled": len(ips) > 0, "ips": ips})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
