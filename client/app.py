"""Traffic Generator Client — Flask Web UI + REST API."""
import os
import logging
from flask import Flask, render_template, jsonify, request

from traffic_engine import TrafficEngine
import network_shaper

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


@app.route('/api/link-simulation/start', methods=['POST'])
def start_link_sim():
    d = _get_json()
    try:
        config = {
            'preset': d.get('preset', 'custom'),
            'latency_ms': int(d.get('latency_ms', 0)),
            'jitter_ms': int(d.get('jitter_ms', 0)),
            'packet_loss_pct': float(d.get('packet_loss_pct', 0)),
            'bandwidth_mbps': int(d.get('bandwidth_mbps', 0)),
            'target': d.get('target', 'all'),
            'ports': d.get('ports', []),
            'cycle_mode': bool(d.get('cycle_mode', False)),
            'healthy_duration': int(d.get('healthy_duration', 30)),
            'impaired_duration': int(d.get('impaired_duration', 30)),
        }
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid parameters"}), 400
    network_shaper.start_link_simulation(config)
    return jsonify({"ok": True, "message": "Link simulation started"})


@app.route('/api/link-simulation/stop', methods=['POST'])
def stop_link_sim():
    network_shaper.stop_link_simulation()
    return jsonify({"ok": True, "message": "Link simulation stopped"})


@app.route('/api/link-simulation/status')
def link_sim_status():
    return jsonify(network_shaper.get_link_simulation_status())


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
