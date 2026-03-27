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

# Store current shaping settings so they persist across page refreshes
current_shaping = {"latency_ms": 0, "jitter_ms": 0, "packet_loss_pct": 0, "bandwidth_mbps": 0}


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
    data = request.json
    protocol = data.get('protocol')
    config = data.get('config', {})
    if not protocol:
        return jsonify({"error": "protocol required"}), 400
    ok, msg = engine.start_job(protocol, config)
    return jsonify({"ok": ok, "message": msg}), 200 if ok else 409


@app.route('/api/stop', methods=['POST'])
def stop_traffic():
    data = request.json
    protocol = data.get('protocol')
    if not protocol:
        return jsonify({"error": "protocol required"}), 400
    if protocol == 'all':
        engine.stop_all()
        return jsonify({"ok": True, "message": "Stopping all"})
    ok, msg = engine.stop_job(protocol)
    return jsonify({"ok": ok, "message": msg}), 200 if ok else 404


@app.route('/api/shaping', methods=['POST'])
def apply_shaping():
    d = request.json
    latency = int(d.get('latency_ms', 0))
    jitter = int(d.get('jitter_ms', 0))
    loss = float(d.get('packet_loss_pct', 0))
    bw = int(d.get('bandwidth_mbps', 0))
    network_shaper.apply_shaping(latency, jitter, loss, bw)
    current_shaping.update({"latency_ms": latency, "jitter_ms": jitter,
                            "packet_loss_pct": loss, "bandwidth_mbps": bw})
    return jsonify({"ok": True, "message": "Shaping applied",
                    "settings": current_shaping})


@app.route('/api/shaping/clear', methods=['POST'])
def clear_shaping():
    network_shaper.clear_all()
    current_shaping.update({"latency_ms": 0, "jitter_ms": 0, "packet_loss_pct": 0, "bandwidth_mbps": 0})
    return jsonify({"ok": True, "message": "Shaping cleared"})


@app.route('/api/shaping/current')
def get_shaping():
    return jsonify(current_shaping)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
