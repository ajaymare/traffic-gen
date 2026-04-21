"""Server-side dashboard with tabs: Server stats + multi-client control."""
import json
import os
import subprocess
import threading
import time

import requests as http_client
from flask import Flask, jsonify, request, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ─── Client Registry ────────────────────────────────────────
CLIENTS_FILE = '/tmp/clients.json'
clients_lock = threading.Lock()
clients = {}  # name -> url


def load_clients():
    global clients
    try:
        with open(CLIENTS_FILE) as f:
            clients = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        clients = {}


def save_clients():
    with open(CLIENTS_FILE, 'w') as f:
        json.dump(clients, f)


load_clients()

# ─── Dashboard HTML ──────────────────────────────────────────

DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Traffic Generator — Control Panel</title>
    <style>
        :root {
            --bg-primary: #f0f4f8;
            --bg-card: #ffffff;
            --bg-card-header: #f7f9fc;
            --bg-input: #f5f7fa;
            --bg-hover: #edf1f7;
            --bg-sub: #f7f9fc;
            --border: #d4dbe6;
            --text-primary: #1e2a3a;
            --text-secondary: #6b7a8d;
            --accent: #0066cc;
            --accent-teal: #00a67e;
            --danger: #dc3545;
            --success: #28a745;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary); color: var(--text-primary); min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #1a2a44, #243b5c);
            padding: 14px 24px; border-bottom: 2px solid var(--accent);
            display: flex; align-items: center; justify-content: space-between;
        }
        .header h1 { font-size: 18px; font-weight: 600; color: #ffffff; }
        .header .status { font-size: 11px; color: var(--text-secondary); }

        /* Tabs */
        .tab-bar {
            background: var(--bg-card); border-bottom: 1px solid var(--border);
            display: flex; align-items: center; padding: 0 16px; gap: 0;
            overflow-x: auto;
        }
        .tab {
            padding: 10px 20px; cursor: pointer; font-size: 13px; font-weight: 500;
            color: var(--text-secondary); border-bottom: 2px solid transparent;
            white-space: nowrap; transition: all 0.2s;
        }
        .tab:hover { color: var(--text-primary); background: var(--bg-hover); }
        .tab.active { color: var(--accent); border-bottom-color: var(--accent); }
        .tab.server-tab { color: var(--accent-teal); }
        .tab.server-tab.active { color: var(--accent-teal); border-bottom-color: var(--accent-teal); }
        .tab-add {
            padding: 6px 14px; cursor: pointer; font-size: 16px; font-weight: 700;
            color: var(--accent-teal); border: 1px solid var(--accent-teal); border-radius: 4px;
            background: transparent; margin-left: 8px;
        }
        .tab-add:hover { background: var(--accent-teal); color: #fff; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        .container {
            max-width: 1200px; margin: 0 auto; padding: 16px;
            display: flex; flex-direction: column; gap: 12px;
        }
        .card {
            background: var(--bg-card); border: 1px solid var(--border);
            border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }
        .card-header {
            padding: 10px 14px; background: var(--bg-card-header);
            font-weight: 600; font-size: 13px; color: var(--text-primary);
            display: flex; align-items: center; justify-content: space-between;
            border-bottom: 1px solid var(--border);
            cursor: pointer; user-select: none;
        }
        .card-header:hover { background: var(--bg-hover); }
        .card-body { padding: 12px; }
        .card-body.collapsed { display: none; }
        .chevron { font-size: 10px; color: var(--text-secondary); transition: transform 0.2s; margin-left: 8px; }
        .chevron.collapsed { transform: rotate(-90deg); }

        /* Stats */
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
        .stat-box {
            background: var(--bg-sub); border: 1px solid var(--border);
            border-radius: 6px; padding: 10px; text-align: center;
        }
        .stat-label { font-size: 10px; color: var(--text-secondary); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
        .stat-value { font-size: 16px; font-weight: 700; color: var(--accent); }
        .stat-value.client-val { color: var(--accent-teal); }

        /* Services grid */
        .services-grid {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 10px;
        }
        .service-card {
            background: var(--bg-sub); border: 1px solid var(--border);
            border-radius: 6px; padding: 10px;
        }
        .service-header {
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 6px;
        }
        .service-name { font-weight: 600; font-size: 13px; color: var(--accent); text-transform: uppercase; }
        .service-badge { font-size: 10px; padding: 2px 8px; border-radius: 10px; }
        .service-badge.active { background: #e6f4ee; color: var(--accent-teal); }
        .service-badge.idle { background: var(--bg-hover); color: var(--text-secondary); }
        .service-stat {
            display: flex; justify-content: space-between;
            font-size: 11px; padding: 2px 0; border-bottom: 1px solid var(--border);
        }
        .service-stat-label { color: var(--text-secondary); }
        .service-stat-value { color: var(--text-primary); font-weight: 500; }

        /* Connections table */
        .connections-table { width: 100%; border-collapse: collapse; font-size: 11px; }
        .connections-table th {
            text-align: left; padding: 5px 8px; background: var(--bg-sub);
            color: var(--text-secondary); font-weight: 500; border-bottom: 1px solid var(--border);
        }
        .connections-table td {
            padding: 4px 8px; border-bottom: 1px solid var(--border); color: var(--text-primary);
        }
        .connections-table tr:hover td { background: var(--bg-hover); }

        /* Protocol cards (client tabs) */
        .protocol-grid {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px;
        }
        .proto-card {
            background: var(--bg-sub); border: 1px solid var(--border);
            border-radius: 6px; padding: 10px; transition: border-color 0.15s;
        }
        .proto-card.running { border-color: var(--accent-teal); border-width: 2px; }
        .proto-header {
            display: flex; align-items: center; justify-content: space-between;
            cursor: pointer; user-select: none;
        }
        .proto-select { display: flex; align-items: center; gap: 8px; }
        .proto-checkbox { width: 14px; height: 14px; accent-color: var(--accent); cursor: pointer; }
        .proto-name { font-weight: 600; font-size: 13px; text-transform: uppercase; color: var(--text-primary); }
        .proto-header-right { display: flex; align-items: center; gap: 6px; }
        .proto-badge { font-size: 10px; padding: 2px 8px; border-radius: 10px; background: var(--bg-hover); color: var(--text-secondary); }
        .proto-badge.running { background: #e6f4ee; color: var(--accent-teal); }
        .proto-badge.countdown { background: #e8f0fe; color: var(--accent); font-variant-numeric: tabular-nums; }
        .proto-details { margin-top: 10px; }
        .proto-fields { display: flex; flex-direction: column; gap: 5px; margin-bottom: 8px; }
        .field-row { display: flex; align-items: center; gap: 8px; }
        .field-row label { font-size: 11px; color: var(--text-secondary); min-width: 85px; }
        .field-row input, .field-row select {
            flex: 1; padding: 4px 8px; background: var(--bg-input);
            border: 1px solid var(--border); border-radius: 4px;
            color: var(--text-primary); font-size: 12px;
        }
        .field-row input:focus, .field-row select:focus { outline: none; border-color: var(--accent-teal); }
        .field-row input[type="checkbox"] { flex: none; width: 14px; height: 14px; accent-color: var(--accent); }
        .proto-actions { display: flex; gap: 6px; align-items: center; }
        .bulk-actions { display: flex; gap: 6px; }
        .advanced-toggle { font-size: 11px; color: var(--accent); cursor: pointer; padding: 4px 0; margin: 2px 0; display: inline-block; }
        .advanced-toggle:hover { text-decoration: underline; }

        /* Buttons */
        .btn {
            padding: 5px 12px; border: none; border-radius: 4px;
            cursor: pointer; font-size: 11px; font-weight: 500;
            transition: background 0.15s, opacity 0.15s;
        }
        .btn:active { opacity: 0.8; }
        .btn-start { background: var(--accent-teal); color: #fff; }
        .btn-start:hover { background: #008f6b; }
        .btn-stop { background: var(--danger); color: #fff; }
        .btn-stop:hover { background: #dc2626; }
        .btn-primary { background: var(--accent); color: #fff; }
        .btn-primary:hover { background: #0055aa; }
        .btn-secondary { background: var(--bg-hover); color: var(--text-primary); border: 1px solid var(--border); }
        .btn-secondary:hover { background: #dce4ef; }
        .btn-danger { background: var(--danger); color: #fff; }
        .btn-danger:hover { background: #dc2626; }

        /* Log panel */
        .log-panel {
            background: #1e2a3a; border: 1px solid var(--border); border-radius: 4px;
            padding: 8px; font-family: 'Monaco', 'Menlo', monospace;
            font-size: 11px; max-height: 250px; overflow-y: auto; line-height: 1.5;
        }
        .log-entry { color: #b0bec5; white-space: pre-wrap; word-break: break-all; }
        .log-entry.error { color: #ff6b6b; }

        /* Modal */
        .modal-overlay {
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.6); z-index: 100; align-items: center; justify-content: center;
        }
        .modal-overlay.show { display: flex; }
        .modal {
            background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px;
            padding: 24px; width: 400px; max-width: 90vw;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        .modal h3 { margin-bottom: 16px; color: var(--accent); }
        .modal-field { margin-bottom: 12px; }
        .modal-field label { display: block; font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
        .modal-field input {
            width: 100%; padding: 8px; background: var(--bg-input); border: 1px solid var(--border);
            border-radius: 4px; color: var(--text-primary); font-size: 13px;
        }
        .modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }

        /* Toast notifications */
        .notification {
            display: none; padding: 12px 20px; border-radius: 6px;
            font-size: 13px; font-weight: 500; margin-bottom: 12px;
            animation: notifSlide 0.3s ease-out;
        }
        .notification.success {
            background: #e6f4ee; color: #0d6e3f; border: 1px solid #27ae60;
        }
        .notification.error {
            background: #fde8e8; color: #9b1c1c; border: 1px solid #dc3545;
        }
        .notification.info {
            background: #e8f0fe; color: #1a4a8a; border: 1px solid #0066cc;
        }
        @keyframes notifSlide {
            from { opacity: 0; transform: translateY(-8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Topology — vis.js tooltip override */
        div.vis-tooltip {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 12px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: var(--text-primary);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            max-width: 260px;
            line-height: 1.5;
        }
        .topo-legend {
            padding: 6px 12px;
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            align-items: center;
            font-size: 11px;
            border-top: 1px solid var(--border);
            background: var(--bg-card);
            min-height: 28px;
        }
        .topo-legend-item {
            display: flex;
            align-items: center;
            gap: 5px;
            color: var(--text-primary);
        }
        .topo-legend-dot {
            display: inline-block;
            width: 9px;
            height: 9px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        .topo-stats {
            padding: 8px 12px;
            font-size: 11px;
            color: var(--text-secondary);
            border-top: 1px solid var(--border);
            background: var(--bg-card);
        }

        @media (max-width: 900px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
</head>
<body>

<div class="header">
    <h1>Traffic Generator — Control Panel</h1>
    <div class="status">Auto-refresh: 2s | <span id="last-update">--</span></div>
</div>

<!-- Tab Bar -->
<div class="tab-bar" id="tab-bar">
    <div class="tab server-tab active" onclick="switchTab('server')">Server</div>
    <button class="tab-add" onclick="showAddClient()" title="Add Client">+</button>
</div>

<!-- Server Tab -->
<div class="tab-content active" id="tab-server">
<div class="container">
    <div class="notification" id="server-notification"></div>
    <div class="card">
        <div class="card-header" onclick="toggleSection('srv-stats')">
            <span>Aggregate Traffic</span>
            <div style="display:flex;align-items:center;gap:6px" onclick="event.stopPropagation()">
                <button class="btn btn-secondary" onclick="clearServerStats()" style="padding:3px 10px;font-size:10px">Clear Stats</button>
                <span class="chevron" id="chevron-srv-stats">&#9660;</span>
            </div>
        </div>
        <div class="card-body" id="section-srv-stats">
            <div class="stats-grid">
                <div class="stat-box"><div class="stat-label">Total Bytes Received</div><div class="stat-value" id="total-recv">0 B</div></div>
                <div class="stat-box"><div class="stat-label">Total Bytes Sent</div><div class="stat-value" id="total-sent">0 B</div></div>
                <div class="stat-box"><div class="stat-label">Total Requests</div><div class="stat-value" id="total-reqs">0</div></div>
                <div class="stat-box"><div class="stat-label">Active Connections</div><div class="stat-value" id="total-conns">0</div></div>
            </div>
        </div>
    </div>
    <div class="card">
        <div class="card-header" onclick="toggleSection('srv-services')">
            <span>Services</span>
            <div style="display:flex;align-items:center;gap:6px" onclick="event.stopPropagation()">
                <button class="btn btn-danger" onclick="restartAllServices()" style="padding:3px 10px;font-size:10px">Restart All</button>
                <span class="chevron" id="chevron-srv-services">&#9660;</span>
            </div>
        </div>
        <div class="card-body" id="section-srv-services"><div class="services-grid" id="services-grid"></div></div>
    </div>
    <div class="card">
        <div class="card-header" onclick="toggleSection('srv-conns')">
            <span>Active Connections</span>
            <span class="chevron collapsed" id="chevron-srv-conns">&#9660;</span>
        </div>
        <div class="card-body collapsed" id="section-srv-conns">
            <table class="connections-table">
                <thead><tr><th>Protocol</th><th>Local Port</th><th>Remote Address</th><th>State</th></tr></thead>
                <tbody id="conn-table-body">
                    <tr><td colspan="4" style="text-align:center;color:var(--text-secondary)">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    <div class="card">
        <div class="card-header" onclick="toggleSection('srv-ftp')">
            <span>FTP Files</span>
            <div style="display:flex;align-items:center;gap:6px" onclick="event.stopPropagation()">
                <label class="btn btn-start" style="cursor:pointer;margin:0;padding:3px 10px;font-size:10px">
                    Upload <input type="file" id="ftp-upload-input" style="display:none" onchange="uploadFtpFile()">
                </label>
                <span class="chevron collapsed" id="chevron-srv-ftp">&#9660;</span>
            </div>
        </div>
        <div class="card-body collapsed" id="section-srv-ftp">
            <div id="upload-status" style="display:none;padding:6px;margin-bottom:6px;border-radius:4px;background:#e6f4ee;color:var(--accent-teal);font-size:11px"></div>
            <table class="connections-table">
                <thead><tr><th>Filename</th><th>Size</th><th>Action</th></tr></thead>
                <tbody id="ftp-files-body">
                    <tr><td colspan="3" style="text-align:center;color:var(--text-secondary)">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>
</div>

<!-- Add Client Modal -->
<div class="modal-overlay" id="add-client-modal">
    <div class="modal">
        <h3>Add Client</h3>
        <div class="modal-field">
            <label>Client Name</label>
            <input type="text" id="client-name" placeholder="e.g. client-1">
        </div>
        <div class="modal-field">
            <label>Client URL</label>
            <input type="text" id="client-url" placeholder="e.g. http://192.168.1.10:8080">
        </div>
        <div class="modal-actions">
            <button class="btn btn-secondary" onclick="hideAddClient()">Cancel</button>
            <button class="btn btn-start" onclick="addClient()">Add</button>
        </div>
    </div>
</div>

<script>
// ─── Section Toggle ──────────────────────────────────────────
function toggleSection(name) {
    var body = document.getElementById('section-' + name);
    var chevron = document.getElementById('chevron-' + name);
    if (!body) return;
    body.classList.toggle('collapsed');
    if (chevron) chevron.classList.toggle('collapsed');
}
function toggleProtoDetails(clientName, proto) {
    var el = document.getElementById('c-' + clientName + '-details-' + proto);
    if (el) el.style.display = el.style.display === 'none' ? 'block' : 'none';
}
function toggleCustomProxy(clientName, proto) {
    var sel = document.getElementById('c-' + clientName + '-' + proto + '-proxy');
    var custom = document.getElementById('c-' + clientName + '-' + proto + '-proxy-custom');
    if (sel && custom) custom.style.display = sel.value === 'Custom' ? 'block' : 'none';
}
function toggleAdvanced(clientName, proto) {
    var el = document.getElementById('c-' + clientName + '-adv-' + proto);
    var toggle = document.getElementById('c-' + clientName + '-adv-toggle-' + proto);
    if (el) {
        var show = el.style.display === 'none';
        el.style.display = show ? 'block' : 'none';
        if (toggle) toggle.textContent = show ? 'Advanced Settings \u25BE' : 'Advanced Settings \u25B8';
    }
}
// ─── Protocol Definitions ────────────────────────────────────
const DSCP_OPTIONS = ['BE','CS1','AF11','AF12','AF13','CS2','AF21','AF22','AF23','CS3','AF31','AF32','AF33','CS4','AF41','AF42','AF43','CS5','VA','EF','CS6','CS7'];
const ADVANCED_KEYS = ['browser_mode', 'browser_type', 'proxy', 'dscp', 'rate_pps', 'burst_enabled', 'burst_count', 'burst_pause'];

const PROTOCOLS = {
    https: { name: 'HTTPS', fields: [
        { key: 'url', label: 'URL', type: 'text', default: 'https://server/' },
        { key: 'method', label: 'Method', type: 'select', options: ['GET','POST'], default: 'GET' },
        { key: 'data_size_kb', label: 'Data KB', type: 'number', default: 0 },
        { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
        { key: 'http2', label: 'HTTP/2', type: 'checkbox', default: false },
        { key: 'ignore_ssl', label: 'Ignore SSL', type: 'checkbox', default: true },
        { key: 'upload', label: 'Upload Mode', type: 'checkbox', default: false },
        { key: 'random_size', label: 'Random Size', type: 'checkbox', default: false },
        { key: 'browser_mode', label: 'Browser Mode', type: 'checkbox', default: false },
        { key: 'browser_type', label: 'Browser', type: 'select', options: ['Random','Chromium','Firefox','WebKit'], default: 'Random' },
        { key: 'proxy', label: 'Proxy', type: 'select', options: ['Global','On','Off','Custom'], default: 'Global' },
        { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
        { key: 'rate_pps', label: 'Rate (pps)', type: 'number', default: 0, step: 1 },
        { key: 'burst_enabled', label: 'Burst Mode', type: 'checkbox', default: false },
        { key: 'burst_count', label: 'Burst Size', type: 'number', default: 5 },
        { key: 'burst_pause', label: 'Burst Pause (s)', type: 'number', default: 2, step: 0.5 },
        { key: 'flows', label: 'Flows', type: 'number', default: 1 },
        { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
    ]},
    iperf: { name: 'iperf3', fields: [
        { key: 'host', label: 'Host', type: 'text', default: 'server' },
        { key: 'port', label: 'Port', type: 'number', default: 5201 },
        { key: 'protocol', label: 'Protocol', type: 'select', options: ['TCP','UDP'], default: 'TCP' },
        { key: 'bandwidth', label: 'Bandwidth', type: 'text', default: '100M' },
        { key: 'parallel', label: 'Parallel Streams', type: 'number', default: 1 },
        { key: 'reverse', label: 'Reverse (download)', type: 'checkbox', default: false },
        { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
        { key: 'flows', label: 'Flows', type: 'number', default: 1 },
        { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
    ]},
    hping3: { name: 'hping3', fields: [
        { key: 'host', label: 'Host', type: 'text', default: 'server' },
        { key: 'mode', label: 'Mode', type: 'select', options: ['ICMP','TCP SYN','TCP ACK','TCP FIN','UDP','Traceroute'], default: 'ICMP' },
        { key: 'port', label: 'Dest Port', type: 'number', default: 0 },
        { key: 'packet_size', label: 'Data Size (B)', type: 'number', default: 64 },
        { key: 'count', label: 'Count (0=cont)', type: 'number', default: 0 },
        { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
        { key: 'flood', label: 'Flood Mode', type: 'checkbox', default: false },
        { key: 'ttl', label: 'TTL', type: 'number', default: 64 },
        { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
        { key: 'flows', label: 'Flows', type: 'number', default: 1 },
        { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
    ]},
    http_plain: { name: 'HTTP (Plain)', fields: [
        { key: 'host', label: 'Host', type: 'text', default: 'server' },
        { key: 'port', label: 'Port', type: 'number', default: 9999 },
        { key: 'method', label: 'Method', type: 'select', options: ['GET','POST'], default: 'GET' },
        { key: 'data_size_kb', label: 'Data Size (KB)', type: 'number', default: 1 },
        { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
        { key: 'random_size', label: 'Random Size', type: 'checkbox', default: false },
        { key: 'browser_mode', label: 'Browser Mode', type: 'checkbox', default: false },
        { key: 'browser_type', label: 'Browser', type: 'select', options: ['Random','Chromium','Firefox','WebKit'], default: 'Random' },
        { key: 'proxy', label: 'Proxy', type: 'select', options: ['Global','On','Off','Custom'], default: 'Global' },
        { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
        { key: 'rate_pps', label: 'Rate (pps)', type: 'number', default: 0, step: 1 },
        { key: 'burst_enabled', label: 'Burst Mode', type: 'checkbox', default: false },
        { key: 'burst_count', label: 'Burst Size', type: 'number', default: 5 },
        { key: 'burst_pause', label: 'Burst Pause (s)', type: 'number', default: 2, step: 0.5 },
        { key: 'flows', label: 'Flows', type: 'number', default: 1 },
        { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
    ]},
    dns: { name: 'DNS', fields: [
        { key: 'host', label: 'Host', type: 'text', default: 'server' },
        { key: 'port', label: 'Port', type: 'number', default: 53 },
        { key: 'domains', label: 'Domains (one per line)', type: 'textarea', default: 'google.com\\namazon.com\\nmicrosoft.com\\ngithub.com\\ncloudflare.com' },
        { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
        { key: 'proxy', label: 'Proxy', type: 'select', options: ['Global','On','Off','Custom'], default: 'Global' },
        { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
        { key: 'rate_pps', label: 'Rate (pps)', type: 'number', default: 0, step: 1 },
        { key: 'burst_enabled', label: 'Burst Mode', type: 'checkbox', default: false },
        { key: 'burst_count', label: 'Burst Size', type: 'number', default: 5 },
        { key: 'burst_pause', label: 'Burst Pause (s)', type: 'number', default: 2, step: 0.5 },
        { key: 'flows', label: 'Flows', type: 'number', default: 1 },
        { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
    ]},
    ftp: { name: 'FTP', fields: [
        { key: 'host', label: 'Host', type: 'text', default: 'server' },
        { key: 'port', label: 'Port', type: 'number', default: 21 },
        { key: 'username', label: 'Username', type: 'text', default: 'anonymous' },
        { key: 'password', label: 'Password', type: 'password', default: '' },
        { key: 'filename', label: 'Filename', type: 'select', options: ['testfile_100mb.bin'], default: 'testfile_100mb.bin' },
        { key: 'random_size', label: 'Random File', type: 'checkbox', default: false },
        { key: 'proxy', label: 'Proxy', type: 'select', options: ['Global','On','Off','Custom'], default: 'Global' },
        { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
        { key: 'rate_pps', label: 'Rate (pps)', type: 'number', default: 0, step: 1 },
        { key: 'burst_enabled', label: 'Burst Mode', type: 'checkbox', default: false },
        { key: 'burst_count', label: 'Burst Size', type: 'number', default: 5 },
        { key: 'burst_pause', label: 'Burst Pause (s)', type: 'number', default: 2, step: 0.5 },
        { key: 'flows', label: 'Flows', type: 'number', default: 1 },
        { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
    ]},
    ssh: { name: 'SSH', fields: [
        { key: 'host', label: 'Host', type: 'text', default: 'server' },
        { key: 'port', label: 'Port', type: 'number', default: 2222 },
        { key: 'username', label: 'Username', type: 'text', default: 'testuser' },
        { key: 'password', label: 'Password', type: 'password', default: 'testpass' },
        { key: 'command', label: 'Command', type: 'text', default: 'uptime' },
        { key: 'interval', label: 'Interval (s)', type: 'number', default: 5 },
        { key: 'proxy', label: 'Proxy', type: 'select', options: ['Global', 'On', 'Off', 'Custom'], default: 'Global' },
        { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
        { key: 'rate_pps', label: 'Rate (pps)', type: 'number', default: 0, step: 1 },
        { key: 'burst_enabled', label: 'Burst Mode', type: 'checkbox', default: false },
        { key: 'burst_count', label: 'Burst Size', type: 'number', default: 5 },
        { key: 'burst_pause', label: 'Burst Pause (s)', type: 'number', default: 2, step: 0.5 },
        { key: 'flows', label: 'Flows', type: 'number', default: 1 },
        { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
    ]},
    ext_https: { name: 'External HTTPS', fields: [
        { key: 'urls', label: 'Target URLs (one per line)', type: 'textarea', default: 'https://www.google.com' },
        { key: 'method', label: 'Method', type: 'select', options: ['GET','POST','HEAD'], default: 'GET' },
        { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
        { key: 'ignore_ssl', label: 'Ignore SSL', type: 'checkbox', default: false },
        { key: 'browser_mode', label: 'Browser Mode', type: 'checkbox', default: false },
        { key: 'browser_type', label: 'Browser', type: 'select', options: ['Random','Chromium','Firefox','WebKit'], default: 'Random' },
        { key: 'proxy', label: 'Proxy', type: 'select', options: ['Global', 'On', 'Off', 'Custom'], default: 'Global' },
        { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
        { key: 'rate_pps', label: 'Rate (pps)', type: 'number', default: 0, step: 1 },
        { key: 'burst_enabled', label: 'Burst Mode', type: 'checkbox', default: false },
        { key: 'burst_count', label: 'Burst Size', type: 'number', default: 5 },
        { key: 'burst_pause', label: 'Burst Pause (s)', type: 'number', default: 2, step: 0.5 },
        { key: 'flows', label: 'Flows', type: 'number', default: 1 },
        { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
    ]},
};

let activeTab = 'server';
let clientList = {};
let clientLogs = {};
let pollInterval = null;

// ─── Notification ─────────────────────────────────────────────
function showNotification(message, type) {
    var el = document.getElementById('server-notification');
    if (!el) return;
    el.className = 'notification ' + (type || 'info');
    el.textContent = message;
    el.style.display = 'block';
    if (el._timer) clearTimeout(el._timer);
    el._timer = setTimeout(function() { el.style.display = 'none'; }, 6000);
}

// ─── Helpers ──────────────────────────────────────────────────
async function restartService(name) {
    if (!confirm('Restart ' + name + '?')) return;
    showNotification('Restarting ' + name + '...', 'info');
    try {
        const resp = await fetch('/api/service/restart', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({service: name})
        });
        const data = await resp.json();
        if (data.ok) {
            showNotification('Service ' + name + ' restarted successfully', 'success');
        } else {
            showNotification('Failed to restart ' + name + ': ' + (data.error || 'Unknown error'), 'error');
        }
    } catch(e) { showNotification('Failed to restart ' + name + ': ' + e, 'error'); }
}

async function restartAllServices() {
    if (!confirm('Restart all server services?')) return;
    showNotification('Restarting all services...', 'info');
    try {
        const resp = await fetch('/api/service/restart-all', {
            method: 'POST', headers: {'Content-Type': 'application/json'}
        });
        const data = await resp.json();
        if (data.ok) {
            showNotification('All services restarted successfully', 'success');
        } else {
            showNotification('Failed to restart services: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch(e) { showNotification('Failed to restart services: ' + e, 'error'); }
}

async function clearServerStats() {
    try {
        const resp = await apiPost('/api/clear_stats', {});
        if (resp.ok) showNotification('Server stats cleared', 'success');
    } catch(e) { showNotification('Failed to clear stats: ' + e, 'error'); }
}

function fmtBytes(b) {
    if (b < 1024) return b + ' B';
    if (b < 1048576) return (b / 1024).toFixed(1) + ' KB';
    if (b < 1073741824) return (b / 1048576).toFixed(1) + ' MB';
    return (b / 1073741824).toFixed(2) + ' GB';
}
function fmtTime(s) {
    if (s < 0) return '--';
    const m = Math.floor(s / 60); const sec = s % 60;
    return m > 0 ? m + 'm ' + sec + 's' : sec + 's';
}
async function apiPost(url, body) {
    const r = await fetch(url, {
        method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body)
    });
    return r.json();
}

function addClientLog(name, msg) {
    if (!clientLogs[name]) clientLogs[name] = [];
    clientLogs[name].push('[' + new Date().toLocaleTimeString() + '] ' + msg);
    if (clientLogs[name].length > 1000) clientLogs[name].splice(0, 500);
    const panel = document.getElementById('log-' + name);
    if (panel) {
        panel.innerHTML = clientLogs[name].map(l => {
            const cls = l.toLowerCase().includes('error') ? ' error' : '';
            const d = document.createElement('div');
            d.textContent = l;
            return '<div class="log-entry' + cls + '">' + d.innerHTML + '</div>';
        }).join('');
        panel.scrollTop = panel.scrollHeight;
    }
}

// ─── Tab Management ──────────────────────────────────────────
function switchTab(name) {
    activeTab = name;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    const tab = document.querySelector('.tab[data-tab="' + name + '"]');
    if (tab) tab.classList.add('active');
    const content = document.getElementById('tab-' + name);
    if (content) content.classList.add('active');
}

function rebuildTabs() {
    const bar = document.getElementById('tab-bar');
    bar.innerHTML = '<div class="tab server-tab' + (activeTab === 'server' ? ' active' : '') +
        '" data-tab="server" onclick="switchTab(\'server\')">Server</div>';
    for (const name of Object.keys(clientList)) {
        bar.innerHTML += '<div class="tab' + (activeTab === name ? ' active' : '') +
            '" data-tab="' + name + '" onclick="switchTab(\'' + name + '\')">' + name + '</div>';
    }
    bar.innerHTML += '<button class="tab-add" onclick="showAddClient()" title="Add Client">+</button>';
}

// ─── Client Tab Rendering ────────────────────────────────────
async function renderClientTab(name) {
    const existing = document.getElementById('tab-' + name);
    if (existing) return;

    let serverHost = 'server';
    try {
        const resp = await fetch('/api/client/' + name + '/server_host');
        const data = await resp.json();
        if (data.server_host) serverHost = data.server_host;
    } catch(e) {}

    const div = document.createElement('div');
    div.className = 'tab-content';
    div.id = 'tab-' + name;

    const inputStyle = 'padding:4px 8px;font-size:11px;background:var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:4px';

    let protoCardsHtml = '';
    for (const [proto, def] of Object.entries(PROTOCOLS)) {
        let basicHtml = '';
        let advancedHtml = '';
        let hasAdvanced = false;
        for (const f of def.fields) {
            if (f.key === 'flows') continue;
            var isAdv = ADVANCED_KEYS.includes(f.key);
            var input;
            var id = 'c-' + name + '-' + proto + '-' + f.key;
            var defVal = f.default;
            if (typeof defVal === 'string') defVal = defVal.replace(/server/g, serverHost);
            if (f.key === 'proxy') {
                var opts = f.options.map(function(o) {
                    return '<option value="' + o + '"' + (o === f.default ? ' selected' : '') + '>' + o + '</option>';
                }).join('');
                input = '<select id="' + id + '" onchange="toggleCustomProxy(\'' + name + '\',\'' + proto + '\')">' + opts + '</select>';
                var pfx = 'c-' + name + '-' + proto + '-';
                var customFields = '<div id="' + pfx + 'proxy-custom" style="display:none;margin-top:4px;padding:6px;background:var(--bg-sub);border:1px solid var(--border);border-radius:4px">' +
                    '<div style="display:grid;grid-template-columns:auto 1fr;gap:4px 6px;align-items:center;font-size:11px">' +
                    '<label style="color:var(--text-secondary)">Type</label>' +
                    '<select id="' + pfx + 'proxy_type" style="padding:2px 6px;font-size:11px;' + inputStyle + '"><option value="http">HTTP</option><option value="socks5">SOCKS5</option></select>' +
                    '<label style="color:var(--text-secondary)">Host</label>' +
                    '<input type="text" id="' + pfx + 'proxy_host" placeholder="proxy.example.com" style="padding:2px 6px;font-size:11px;' + inputStyle + '">' +
                    '<label style="color:var(--text-secondary)">Port</label>' +
                    '<input type="number" id="' + pfx + 'proxy_port" value="8080" style="padding:2px 6px;font-size:11px;width:80px;' + inputStyle + '">' +
                    '<label style="color:var(--text-secondary)">User</label>' +
                    '<input type="text" id="' + pfx + 'proxy_user" placeholder="(optional)" style="padding:2px 6px;font-size:11px;' + inputStyle + '">' +
                    '<label style="color:var(--text-secondary)">Pass</label>' +
                    '<input type="password" id="' + pfx + 'proxy_pass" placeholder="(optional)" style="padding:2px 6px;font-size:11px;' + inputStyle + '">' +
                    '</div></div>';
                var row = '<div class="field-row"><label>' + f.label + '</label>' + input + '</div>' + customFields;
                advancedHtml += row; hasAdvanced = true;
                continue;
            } else if (f.type === 'select') {
                var opts = f.options.map(function(o) {
                    return '<option value="' + o + '"' + (o === f.default ? ' selected' : '') + '>' + o + '</option>';
                }).join('');
                input = '<select id="' + id + '">' + opts + '</select>';
            } else if (f.type === 'textarea') {
                input = '<textarea id="' + id + '" rows="3" style="width:100%;' + inputStyle + ';resize:vertical;font-family:inherit">' + defVal + '</textarea>';
            } else if (f.type === 'checkbox') {
                input = '<input type="checkbox" id="' + id + '"' + (f.default ? ' checked' : '') + '>';
            } else {
                var step = f.step ? ' step="' + f.step + '"' : '';
                input = '<input type="' + f.type + '" id="' + id + '" value="' + defVal + '"' + step + '>';
            }
            var row = '<div class="field-row"><label>' + f.label + '</label>' + input + '</div>';
            if (isAdv) { advancedHtml += row; hasAdvanced = true; }
            else basicHtml += row;
        }
        let advSection = '';
        if (hasAdvanced) {
            advSection = '<div class="advanced-toggle" id="c-' + name + '-adv-toggle-' + proto + '" onclick="event.stopPropagation();toggleAdvanced(\'' + name + '\',\'' + proto + '\')">Advanced Settings \u25B8</div>' +
                '<div id="c-' + name + '-adv-' + proto + '" style="display:none">' + advancedHtml + '</div>';
        }
        protoCardsHtml += '<div class="proto-card" id="c-' + name + '-proto-' + proto + '">' +
            '<div class="proto-header" onclick="toggleProtoDetails(\'' + name + '\',\'' + proto + '\')">' +
            '<span class="proto-select" onclick="event.stopPropagation()">' +
            '<input type="checkbox" id="c-' + name + '-select-' + proto + '" class="proto-checkbox">' +
            '<span class="proto-name">' + def.name + '</span></span>' +
            '<span class="proto-header-right">' +
            '<span class="proto-badge" id="c-' + name + '-status-' + proto + '">Stopped</span>' +
            '<span class="proto-badge countdown" id="c-' + name + '-timer-' + proto + '" style="display:none"></span>' +
            '<button class="btn btn-start" onclick="event.stopPropagation();clientStartProto(\'' + name + '\',\'' + proto + '\')" style="padding:3px 10px;font-size:10px">Start</button>' +
            '<button class="btn btn-stop" onclick="event.stopPropagation();clientStopProto(\'' + name + '\',\'' + proto + '\')" style="padding:3px 10px;font-size:10px">Stop</button>' +
            '</span></div>' +
            '<div class="proto-details" id="c-' + name + '-details-' + proto + '" style="display:none">' +
            '<div class="proto-fields">' + basicHtml + '</div>' +
            advSection +
            '<div class="proto-actions" style="margin-top:6px">' +
            '<label style="font-size:10px;color:var(--text-secondary);display:flex;align-items:center;gap:4px">' +
            'Flows <input type="number" id="c-' + name + '-' + proto + '-flows" value="1" min="1" max="20" style="width:42px;' + inputStyle + '">' +
            '</label></div></div></div>';
    }

    div.innerHTML = '<div class="container">' +
        '<div class="card"><div class="card-header">' +
        '<span>Client: ' + name + ' (' + clientList[name] + ')</span>' +
        '<button class="btn btn-danger" onclick="removeClient(\'' + name + '\')">Remove Client</button>' +
        '</div></div>' +
        // Stats
        '<div class="card"><div class="card-header" onclick="toggleSection(\'c-' + name + '-stats\')"><span>Live Statistics</span>' +
        '<div style="display:flex;align-items:center;gap:6px" onclick="event.stopPropagation()">' +
        '<button class="btn btn-secondary" onclick="clientClearStats(\'' + name + '\')" style="padding:3px 10px;font-size:10px">Clear Stats</button>' +
        '<span class="chevron" id="chevron-c-' + name + '-stats">&#9660;</span></div></div><div class="card-body" id="section-c-' + name + '-stats">' +
        '<div class="stats-grid">' +
        '<div class="stat-box"><div class="stat-label">Bytes Sent</div><div class="stat-value client-val" id="c-' + name + '-sent">0 B</div></div>' +
        '<div class="stat-box"><div class="stat-label">Bytes Received</div><div class="stat-value client-val" id="c-' + name + '-recv">0 B</div></div>' +
        '<div class="stat-box"><div class="stat-label">Requests</div><div class="stat-value client-val" id="c-' + name + '-reqs">0</div></div>' +
        '<div class="stat-box"><div class="stat-label">Errors</div><div class="stat-value client-val" id="c-' + name + '-errors">0</div></div>' +
        '</div></div></div>' +
        // Traffic Topology
        '<div class="card"><div class="card-header" onclick="toggleSection(\'c-' + name + '-topo\')"><span>Traffic Topology</span>' +
        '<div style="display:flex;align-items:center;gap:6px" onclick="event.stopPropagation()">' +
        '<button class="btn btn-secondary" onclick="clientRefreshTopology(\'' + name + '\')" style="padding:3px 10px;font-size:10px">Refresh</button>' +
        '<span class="chevron collapsed" id="chevron-c-' + name + '-topo">&#9660;</span></div>' +
        '</div><div class="card-body collapsed" id="section-c-' + name + '-topo">' +
        '<div id="c-' + name + '-topo-container" style="width:100%;height:350px;border:1px solid var(--border);border-radius:6px;background:var(--bg-sub)"></div>' +
        '</div></div>' +
        // Router Link Simulation
        '<div class="card"><div class="card-header" onclick="toggleSection(\'c-' + name + '-routers\')"><span>Link Simulation — Routers</span><span class="chevron" id="chevron-c-' + name + '-routers">&#9660;</span></div><div class="card-body" id="section-c-' + name + '-routers">' +
        '<div style="margin-bottom:12px;padding:10px;background:var(--bg-sub);border:1px solid var(--border);border-radius:6px">' +
        '<label style="font-size:11px;font-weight:600;margin-bottom:6px;display:block;color:var(--text-secondary)">Add Router</label>' +
        '<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center">' +
        '<input type="text" id="c-' + name + '-router-add-name" placeholder="Name" style="width:110px;' + inputStyle + '">' +
        '<input type="text" id="c-' + name + '-router-add-ip" placeholder="Router IP" style="width:130px;' + inputStyle + '">' +
        '<input type="text" id="c-' + name + '-router-add-user" placeholder="Username" style="width:100px;' + inputStyle + '">' +
        '<input type="password" id="c-' + name + '-router-add-pass" placeholder="Password" style="width:100px;' + inputStyle + '">' +
        '<button class="btn btn-start" onclick="clientAddRouter(\'' + name + '\')">Add</button>' +
        '</div>' +
        '<div id="c-' + name + '-router-add-error" style="display:none;margin-top:4px;font-size:11px;color:var(--danger)"></div>' +
        '</div>' +
        '<div id="c-' + name + '-router-cards-container"></div>' +
        '</div></div>' +
        // Source IPs
        '<div class="card"><div class="card-header" onclick="toggleSection(\'c-' + name + '-srcip\')"><span>Source IP Simulation</span><span class="chevron collapsed" id="chevron-c-' + name + '-srcip">&#9660;</span></div><div class="card-body collapsed" id="section-c-' + name + '-srcip">' +
        '<div style="padding:8px;background:var(--bg-sub);border:1px solid var(--border);border-radius:6px">' +
        '<label style="display:flex;align-items:center;gap:8px;margin-bottom:6px">' +
        '<input type="checkbox" id="c-' + name + '-source-ip-toggle" onchange="clientToggleSourceIp(\'' + name + '\')">' +
        '<strong style="font-size:12px">Random Source IPs</strong> <span style="font-size:11px;color:var(--text-secondary)">(simulate multiple clients)</span></label>' +
        '<div id="c-' + name + '-source-ip-config" style="display:none;margin-top:6px">' +
        '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' +
        '<label style="font-size:11px;color:var(--text-secondary)">Base IP</label>' +
        '<input type="text" id="c-' + name + '-source-ip-base" value="172.18.0.100" style="width:130px;' + inputStyle + '">' +
        '<label style="font-size:11px;color:var(--text-secondary)">Count</label>' +
        '<input type="number" id="c-' + name + '-source-ip-count" value="5" min="1" max="50" style="width:55px;' + inputStyle + '">' +
        '<button class="btn btn-primary" onclick="clientApplySourceIps(\'' + name + '\')" style="padding:4px 10px">Apply</button>' +
        '</div><div id="c-' + name + '-source-ip-list" style="margin-top:6px;font-size:10px;color:var(--text-secondary)"></div></div>' +
        '</div></div></div>' +
        // Proxy Configuration
        '<div class="card"><div class="card-header" onclick="toggleSection(\'c-' + name + '-proxy\')"><span>Proxy Configuration</span><span class="chevron collapsed" id="chevron-c-' + name + '-proxy">&#9660;</span></div>' +
        '<div class="card-body collapsed" id="section-c-' + name + '-proxy">' +
        '<div style="padding:8px;background:var(--bg-sub);border:1px solid var(--border);border-radius:6px">' +
        '<label style="display:flex;align-items:center;gap:8px;margin-bottom:8px">' +
        '<input type="checkbox" id="c-' + name + '-proxy-enabled">' +
        '<strong style="font-size:12px">Enable Proxy</strong>' +
        '<span style="font-size:11px;color:var(--text-secondary)">(route traffic via proxy server)</span></label>' +
        '<div style="display:grid;grid-template-columns:auto 1fr;gap:6px 8px;align-items:center;font-size:12px">' +
        '<label style="color:var(--text-secondary)">Type</label>' +
        '<select id="c-' + name + '-proxy-type" style="padding:4px 8px;background:var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:4px;font-size:12px">' +
        '<option value="http">HTTP/HTTPS</option><option value="socks5">SOCKS5</option></select>' +
        '<label style="color:var(--text-secondary)">Host</label>' +
        '<input type="text" id="c-' + name + '-proxy-host" placeholder="proxy.example.com" style="padding:4px 8px;' + inputStyle + '">' +
        '<label style="color:var(--text-secondary)">Port</label>' +
        '<input type="number" id="c-' + name + '-proxy-port" value="8080" style="padding:4px 8px;' + inputStyle + 'width:100px">' +
        '<label style="color:var(--text-secondary)">Username</label>' +
        '<input type="text" id="c-' + name + '-proxy-username" placeholder="(optional)" style="padding:4px 8px;' + inputStyle + '">' +
        '<label style="color:var(--text-secondary)">Password</label>' +
        '<input type="password" id="c-' + name + '-proxy-password" placeholder="(optional)" style="padding:4px 8px;' + inputStyle + '">' +
        '</div>' +
        '<div style="margin-top:8px;display:flex;gap:6px">' +
        '<button class="btn btn-primary" onclick="clientSaveProxy(\'' + name + '\')" style="padding:4px 12px">Apply</button>' +
        '<button class="btn btn-secondary" onclick="clientTestProxy(\'' + name + '\')" style="padding:4px 12px">Test</button>' +
        '</div></div></div></div>' +
        // Protocol cards
        '<div class="card"><div class="card-header" onclick="toggleSection(\'c-' + name + '-protos\')"><span>Traffic Generators</span>' +
        '<div style="display:flex;align-items:center;gap:6px" onclick="event.stopPropagation()">' +
        '<div class="bulk-actions">' +
        '<button class="btn btn-secondary" onclick="clientSelectAll(\'' + name + '\')">Select All</button>' +
        '<button class="btn btn-secondary" onclick="clientDeselectAll(\'' + name + '\')">Deselect</button>' +
        '<button class="btn btn-start" onclick="clientStartSelected(\'' + name + '\')">Start Selected</button>' +
        '<button class="btn btn-stop" onclick="clientStopSelected(\'' + name + '\')">Stop Selected</button>' +
        '<button class="btn btn-danger" onclick="clientStopAll(\'' + name + '\')">Stop All</button>' +
        '</div><span class="chevron" id="chevron-c-' + name + '-protos">&#9660;</span></div>' +
        '</div><div class="card-body" id="section-c-' + name + '-protos"><div class="protocol-grid">' + protoCardsHtml + '</div></div></div>' +
        // Log
        '<div class="card"><div class="card-header" onclick="toggleSection(\'c-' + name + '-logs\')"><span>Activity Log</span>' +
        '<div style="display:flex;align-items:center;gap:8px" onclick="event.stopPropagation()">' +
        '<label style="display:flex;align-items:center;gap:4px;font-size:11px;font-weight:normal;cursor:pointer;color:var(--text-secondary)">' +
        '<input type="checkbox" id="auto-refresh-' + name + '" checked onchange="toggleAutoRefresh()"> Auto-refresh</label>' +
        '<button class="btn btn-secondary" onclick="clientLogs[\'' + name + '\']=[];document.getElementById(\'log-' + name + '\').innerHTML=\'\'">Clear</button>' +
        '<span class="chevron collapsed" id="chevron-c-' + name + '-logs">&#9660;</span></div>' +
        '</div><div class="card-body collapsed" id="section-c-' + name + '-logs"><div class="log-panel" id="log-' + name + '"></div></div></div>' +
        '</div>';

    document.body.appendChild(div);
}

// ─── Client Actions ──────────────────────────────────────────
function clientGetConfig(clientName, proto) {
    var cfg = {};
    for (var i = 0; i < PROTOCOLS[proto].fields.length; i++) {
        var f = PROTOCOLS[proto].fields[i];
        if (f.key === 'flows') continue;
        var el = document.getElementById('c-' + clientName + '-' + proto + '-' + f.key);
        if (!el) continue;
        if (f.type === 'checkbox') cfg[f.key] = el.checked;
        else if (f.type === 'number') cfg[f.key] = parseFloat(el.value);
        else cfg[f.key] = el.value;
    }
    if (cfg.proxy === 'Custom') {
        var pfx = 'c-' + clientName + '-' + proto + '-';
        var g = function(id) { return document.getElementById(pfx + id); };
        cfg.proxy_type = g('proxy_type') ? g('proxy_type').value : 'http';
        cfg.proxy_host = g('proxy_host') ? g('proxy_host').value : '';
        cfg.proxy_port = g('proxy_port') ? parseInt(g('proxy_port').value) : 8080;
        cfg.proxy_user = g('proxy_user') ? g('proxy_user').value : '';
        cfg.proxy_pass = g('proxy_pass') ? g('proxy_pass').value : '';
    }
    return cfg;
}

function clientGetFlowCount(clientName, proto) {
    const el = document.getElementById('c-' + clientName + '-' + proto + '-flows');
    return el ? Math.max(1, Math.min(20, parseInt(el.value) || 1)) : 1;
}

async function clientStartProto(clientName, proto) {
    const config = clientGetConfig(clientName, proto);
    const flows = clientGetFlowCount(clientName, proto);
    if (flows === 1) {
        const res = await apiPost('/api/client/' + clientName + '/start', { protocol: proto, config });
        addClientLog(clientName, '[' + proto.toUpperCase() + '] ' + (res.message || res.error || 'sent'));
    } else {
        for (let i = 1; i <= flows; i++) {
            const cfg = Object.assign({}, config, { flow_id: String(i) });
            const res = await apiPost('/api/client/' + clientName + '/start', { protocol: proto, config: cfg });
            addClientLog(clientName, '[' + proto.toUpperCase() + '] ' + (res.message || res.error || 'sent'));
        }
    }
}

async function clientStopProto(clientName, proto) {
    const res = await apiPost('/api/client/' + clientName + '/stop', { protocol: proto });
    addClientLog(clientName, '[' + proto.toUpperCase() + '] ' + (res.message || res.error || 'sent'));
}

async function clientClearStats(clientName) {
    const res = await apiPost('/api/client/' + clientName + '/clear_stats', {});
    addClientLog(clientName, '[STATS] ' + (res.message || 'Stats cleared'));
}

async function clientStopAll(clientName) {
    await apiPost('/api/client/' + clientName + '/stop', { protocol: 'all' });
    addClientLog(clientName, '[ALL] Stopping all traffic');
}

function clientSelectAll(clientName) {
    Object.keys(PROTOCOLS).forEach(p => {
        const el = document.getElementById('c-' + clientName + '-select-' + p);
        if (el) el.checked = true;
    });
}
function clientDeselectAll(clientName) {
    Object.keys(PROTOCOLS).forEach(p => {
        const el = document.getElementById('c-' + clientName + '-select-' + p);
        if (el) el.checked = false;
    });
}
async function clientStartSelected(clientName) {
    const selected = Object.keys(PROTOCOLS).filter(p =>
        document.getElementById('c-' + clientName + '-select-' + p)?.checked);
    if (!selected.length) { addClientLog(clientName, '[WARN] No protocols selected'); return; }
    for (const proto of selected) {
        await clientStartProto(clientName, proto);
    }
}
async function clientStopSelected(clientName) {
    const selected = Object.keys(PROTOCOLS).filter(p =>
        document.getElementById('c-' + clientName + '-select-' + p)?.checked);
    if (!selected.length) { addClientLog(clientName, '[WARN] No protocols selected'); return; }
    for (const proto of selected) {
        const res = await apiPost('/api/client/' + clientName + '/stop', { protocol: proto });
        addClientLog(clientName, '[' + proto.toUpperCase() + '] ' + (res.message || ''));
    }
}

const ROUTER_PRESETS = {
    degraded_wan: { latency_ms: 300, jitter_ms: 50, packet_loss_pct: 5, bandwidth_mbps: 0 },
    voice_sla: { latency_ms: 200, jitter_ms: 40, packet_loss_pct: 2, bandwidth_mbps: 0 },
    video_sla: { latency_ms: 150, jitter_ms: 30, packet_loss_pct: 3, bandwidth_mbps: 0 },
};

async function clientAddRouter(clientName) {
    const el = id => document.getElementById('c-' + clientName + '-' + id);
    const name = el('router-add-name').value.trim();
    const ip = el('router-add-ip').value.trim();
    const username = el('router-add-user').value.trim();
    const password = el('router-add-pass').value;
    const errEl = el('router-add-error');
    if (!name || !ip || !username) {
        errEl.textContent = 'Name, IP, and username are required';
        errEl.style.display = 'block'; return;
    }
    errEl.style.display = 'none';
    const res = await apiPost('/api/client/' + clientName + '/routers', { name, ip, username, password });
    if (res.ok) {
        el('router-add-name').value = '';
        el('router-add-ip').value = '';
        el('router-add-user').value = '';
        el('router-add-pass').value = '';
        addClientLog(clientName, '[ROUTER] ' + res.message);
        clientLoadRouters(clientName);
    } else {
        errEl.textContent = res.error || 'Failed to add router';
        errEl.style.display = 'block';
        addClientLog(clientName, '[ROUTER] Error: ' + (res.error || ''));
    }
}

async function clientRemoveRouter(clientName, rid) {
    if (!confirm('Remove this router?')) return;
    const resp = await fetch('/api/client/' + clientName + '/routers/' + rid, { method: 'DELETE' });
    const data = await resp.json();
    addClientLog(clientName, '[ROUTER] ' + data.message);
    clientLoadRouters(clientName);
}

async function clientReconnectRouter(clientName, rid) {
    const res = await apiPost('/api/client/' + clientName + '/routers/' + rid + '/connect', {});
    addClientLog(clientName, '[ROUTER] ' + res.message);
    clientLoadRouters(clientName);
}

async function clientRefreshInterfaces(clientName, rid) {
    await fetch('/api/client/' + clientName + '/routers/' + rid + '/interfaces');
    addClientLog(clientName, '[ROUTER] Refreshed interfaces');
    clientLoadRouters(clientName);
}

async function clientSelectInterface(clientName, rid, iface) {
    const res = await apiPost('/api/client/' + clientName + '/routers/' + rid + '/select-interface', { interface: iface });
    if (!res.ok) addClientLog(clientName, '[ROUTER] ' + (res.error || res.message));
}

function clientApplyRouterPreset(clientName, rid, presetName) {
    const p = ROUTER_PRESETS[presetName];
    if (!p) return;
    var el = function(f) { return document.getElementById('c-' + clientName + '-rtr-' + rid + '-' + f); };
    if (el('latency')) el('latency').value = p.latency_ms;
    if (el('jitter')) el('jitter').value = p.jitter_ms;
    if (el('loss')) el('loss').value = p.packet_loss_pct;
    if (el('bw')) el('bw').value = p.bandwidth_mbps;
}

async function clientApplyRouterMode(clientName, rid, mode) {
    var body = { mode: mode };
    if (mode === 'impaired') {
        var el = function(f) { return document.getElementById('c-' + clientName + '-rtr-' + rid + '-' + f); };
        body.latency_ms = parseInt((el('latency') || {}).value) || 0;
        body.jitter_ms = parseInt((el('jitter') || {}).value) || 0;
        body.packet_loss_pct = parseFloat((el('loss') || {}).value) || 0;
        body.bandwidth_mbps = parseInt((el('bw') || {}).value) || 0;
    }
    const res = await apiPost('/api/client/' + clientName + '/routers/' + rid + '/mode', body);
    addClientLog(clientName, '[ROUTER] ' + (res.message || res.error));
    clientLoadRouters(clientName);
}

function clientToggleRouterInterfaces(clientName, rid) {
    var el = document.getElementById('c-' + clientName + '-rtr-ifaces-' + rid);
    var toggle = document.getElementById('c-' + clientName + '-rtr-ifaces-toggle-' + rid);
    if (el) {
        var show = el.style.display === 'none';
        el.style.display = show ? 'block' : 'none';
        if (toggle) toggle.textContent = show ? 'Hide Interfaces' : 'Show Interfaces';
    }
}
function clientRenderRouterCard(clientName, r) {
    var id = r.router_id;
    var prefix = 'c-' + clientName + '-rtr-' + id;
    var connColor = r.connected ? 'var(--success)' : 'var(--danger)';
    var connText = r.connected ? 'Connected' : 'Disconnected';
    var selectedIfaceDisplay = r.selected_interface || 'None';
    var ifaceRows = '';
    if (r.interfaces && r.interfaces.length) {
        for (var i = 0; i < r.interfaces.length; i++) {
            var iface = r.interfaces[i];
            var checked = iface.name === r.selected_interface ? 'checked' : '';
            var stateColor = iface.state === 'up' ? 'var(--success)' : 'var(--danger)';
            var ipStr = iface.ip_address ? iface.ip_address + (iface.subnet || '') : '--';
            var descStr = iface.description ? ' — ' + iface.description : '';
            ifaceRows += '<label style="display:flex;align-items:center;gap:8px;padding:3px 0;font-size:11px;cursor:pointer;color:var(--text-primary)">' +
                '<input type="radio" name="' + prefix + '-iface" value="' + iface.name + '" ' + checked +
                ' onchange="clientSelectInterface(\'' + clientName + '\',\'' + id + '\',\'' + iface.name + '\')">' +
                '<strong>' + iface.name + '</strong>' +
                '<span style="color:var(--text-secondary);font-style:italic">' + descStr + '</span>' +
                '<span style="color:var(--text-secondary)">' + ipStr + '</span>' +
                '<span style="color:' + stateColor + ';font-weight:600;font-size:10px">' + iface.state.toUpperCase() + '</span></label>';
        }
    } else {
        ifaceRows = '<div style="color:var(--text-secondary);font-size:11px">No interfaces discovered</div>';
    }
    var modeHtml = '';
    if (r.current_mode === 'healthy') {
        modeHtml = '<div style="padding:6px 10px;background:rgba(39,174,96,0.1);border:1px solid rgba(39,174,96,0.3);border-radius:6px;font-size:12px;margin-bottom:8px;color:var(--success)">' +
            '<strong>HEALTHY</strong> — ' + (r.selected_interface || '?') + ' up, no impairment</div>';
    } else if (r.current_mode === 'impaired') {
        var cfg = r.impairment_config || {};
        var parts = [];
        if (cfg.latency_ms) parts.push(cfg.latency_ms + 'ms latency');
        if (cfg.jitter_ms) parts.push(cfg.jitter_ms + 'ms jitter');
        if (cfg.packet_loss_pct) parts.push(cfg.packet_loss_pct + '% loss');
        if (cfg.bandwidth_mbps) parts.push(cfg.bandwidth_mbps + ' Mbps');
        modeHtml = '<div style="padding:6px 10px;background:rgba(231,76,60,0.1);border:1px solid rgba(231,76,60,0.3);border-radius:6px;font-size:12px;margin-bottom:8px;color:var(--danger)">' +
            '<strong>IMPAIRED</strong> — ' + (r.selected_interface || '?') + ' | ' + (parts.join(', ') || 'custom') + '</div>';
    } else if (r.current_mode === 'link_down') {
        modeHtml = '<div style="padding:6px 10px;background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.4);border-radius:6px;font-size:12px;margin-bottom:8px;color:#ff6b6b">' +
            '<strong>LINK DOWN</strong> — ' + (r.selected_interface || '?') + ' is shut down</div>';
    }
    var inputStyle = 'width:60px;padding:3px 6px;font-size:11px;background:var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:3px';
    var connectedContent = r.connected ?
        modeHtml +
        '<div style="margin-bottom:8px"><div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">' +
        '<span style="font-size:11px;color:var(--text-secondary)">Interface: <strong style="color:var(--text-primary)">' + selectedIfaceDisplay + '</strong></span>' +
        '<button class="btn btn-secondary" id="c-' + clientName + '-rtr-ifaces-toggle-' + id + '" onclick="clientToggleRouterInterfaces(\'' + clientName + '\',\'' + id + '\')" style="padding:2px 8px;font-size:10px">Show Interfaces</button>' +
        '<button class="btn btn-secondary" onclick="clientRefreshInterfaces(\'' + clientName + '\',\'' + id + '\')" style="padding:2px 8px;font-size:10px">Refresh</button></div>' +
        '<div id="c-' + clientName + '-rtr-ifaces-' + id + '" style="display:none;padding:6px 8px;background:var(--bg-card);border:1px solid var(--border);border-radius:4px;margin-top:4px">' + ifaceRows + '</div></div>' +
        '<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:8px">' +
        '<span style="font-size:10px;color:var(--text-secondary)">Presets:</span>' +
        '<button class="btn btn-secondary" onclick="clientApplyRouterPreset(\'' + clientName + '\',\'' + id + '\',\'degraded_wan\')" style="padding:2px 8px;font-size:10px">Degraded WAN</button>' +
        '<button class="btn btn-secondary" onclick="clientApplyRouterPreset(\'' + clientName + '\',\'' + id + '\',\'voice_sla\')" style="padding:2px 8px;font-size:10px">Voice SLA</button>' +
        '<button class="btn btn-secondary" onclick="clientApplyRouterPreset(\'' + clientName + '\',\'' + id + '\',\'video_sla\')" style="padding:2px 8px;font-size:10px">Video SLA</button></div>' +
        '<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:8px">' +
        '<label style="font-size:10px;color:var(--text-secondary)">Latency</label><input type="number" id="' + prefix + '-latency" value="' + ((r.impairment_config||{}).latency_ms||0) + '" min="0" max="5000" style="' + inputStyle + '"><span style="font-size:10px;color:var(--text-secondary)">ms</span>' +
        '<label style="font-size:10px;color:var(--text-secondary);margin-left:4px">Jitter</label><input type="number" id="' + prefix + '-jitter" value="' + ((r.impairment_config||{}).jitter_ms||0) + '" min="0" max="2000" style="' + inputStyle + '"><span style="font-size:10px;color:var(--text-secondary)">ms</span>' +
        '<label style="font-size:10px;color:var(--text-secondary);margin-left:4px">Loss</label><input type="number" id="' + prefix + '-loss" value="' + ((r.impairment_config||{}).packet_loss_pct||0) + '" min="0" max="100" step="0.5" style="' + inputStyle + '"><span style="font-size:10px;color:var(--text-secondary)">%</span>' +
        '<label style="font-size:10px;color:var(--text-secondary);margin-left:4px">BW</label><input type="number" id="' + prefix + '-bw" value="' + ((r.impairment_config||{}).bandwidth_mbps||0) + '" min="0" max="10000" step="10" style="width:70px;padding:3px 6px;font-size:11px;background:var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:3px"><span style="font-size:10px;color:var(--text-secondary)">Mbps</span></div>' +
        '<div style="display:flex;gap:6px">' +
        '<button class="btn btn-start" onclick="clientApplyRouterMode(\'' + clientName + '\',\'' + id + '\',\'healthy\')" style="padding:4px 12px;font-size:11px">Healthy</button>' +
        '<button class="btn btn-primary" onclick="clientApplyRouterMode(\'' + clientName + '\',\'' + id + '\',\'impaired\')" style="padding:4px 12px;font-size:11px">Apply Impaired</button>' +
        '<button class="btn btn-danger" onclick="clientApplyRouterMode(\'' + clientName + '\',\'' + id + '\',\'link_down\')" style="padding:4px 12px;font-size:11px">Link Down</button></div>'
        : '<div style="color:var(--text-secondary);font-size:11px;padding:6px 0">Router disconnected. Click Reconnect to restore.</div>';
    return '<div style="background:var(--bg-sub);border:1px solid var(--border);border-radius:6px;padding:10px;margin-bottom:8px">' +
        '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">' +
        '<div style="display:flex;align-items:center;gap:8px">' +
        '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:' + connColor + '"></span>' +
        '<strong style="font-size:13px;color:var(--text-primary)">' + r.name + '</strong>' +
        '<span style="color:var(--text-secondary);font-size:11px">' + r.ip + '</span>' +
        '<span style="color:' + connColor + ';font-size:10px;font-weight:600">' + connText + '</span></div>' +
        '<div style="display:flex;gap:4px">' +
        (!r.connected ? '<button class="btn btn-start" onclick="clientReconnectRouter(\'' + clientName + '\',\'' + id + '\')" style="padding:2px 8px;font-size:10px">Reconnect</button>' : '') +
        '<button class="btn btn-danger" onclick="clientRemoveRouter(\'' + clientName + '\',\'' + id + '\')" style="padding:2px 8px;font-size:10px">Remove</button></div></div>' +
        connectedContent + '</div>';
}

async function clientLoadRouters(clientName) {
    try {
        const resp = await fetch('/api/client/' + clientName + '/routers');
        const routers = await resp.json();
        const container = document.getElementById('c-' + clientName + '-router-cards-container');
        if (!container) return;
        if (!routers.length) {
            container.innerHTML = '<div style="color:var(--text-secondary);font-size:12px;text-align:center;padding:12px">No routers added. Add a router above to start link simulation.</div>';
            return;
        }
        container.innerHTML = routers.map(function(r) { return clientRenderRouterCard(clientName, r); }).join('');
    } catch(e) {}
}

async function clientPollRouterStatus(clientName) {
    try {
        const resp = await fetch('/api/client/' + clientName + '/routers');
        const routers = await resp.json();
        const container = document.getElementById('c-' + clientName + '-router-cards-container');
        if (!container) return;
        if (!routers.length) {
            container.innerHTML = '<div style="color:var(--text-secondary);font-size:12px;text-align:center;padding:12px">No routers added. Add a router above to start link simulation.</div>';
            return;
        }
        // Preserve impairment input values and interface toggle state during re-render
        var savedValues = {};
        var expandedIfaces = {};
        for (var i = 0; i < routers.length; i++) {
            var rid = routers[i].router_id;
            var fields = ['latency','jitter','loss','bw'];
            for (var j = 0; j < fields.length; j++) {
                var el = document.getElementById('c-' + clientName + '-rtr-' + rid + '-' + fields[j]);
                if (el) savedValues[rid + '-' + fields[j]] = el.value;
            }
            var ifaceEl = document.getElementById('c-' + clientName + '-rtr-ifaces-' + rid);
            if (ifaceEl && ifaceEl.style.display !== 'none') expandedIfaces[rid] = true;
        }
        container.innerHTML = routers.map(function(r) { return clientRenderRouterCard(clientName, r); }).join('');
        for (var key in savedValues) {
            var el = document.getElementById('c-' + clientName + '-rtr-' + key);
            if (el) el.value = savedValues[key];
        }
        for (var rid in expandedIfaces) {
            var ifaceEl = document.getElementById('c-' + clientName + '-rtr-ifaces-' + rid);
            var toggleBtn = document.getElementById('c-' + clientName + '-rtr-ifaces-toggle-' + rid);
            if (ifaceEl) ifaceEl.style.display = 'block';
            if (toggleBtn) toggleBtn.textContent = 'Hide Interfaces';
        }
    } catch(e) {}
}

function clientToggleSourceIp(clientName) {
    const enabled = document.getElementById('c-' + clientName + '-source-ip-toggle').checked;
    const cfg = document.getElementById('c-' + clientName + '-source-ip-config');
    if (cfg) cfg.style.display = enabled ? 'block' : 'none';
    if (!enabled) {
        apiPost('/api/client/' + clientName + '/source_ips', { enabled: false });
        const list = document.getElementById('c-' + clientName + '-source-ip-list');
        if (list) list.textContent = '';
        addClientLog(clientName, '[SOURCE IP] Disabled');
    }
}

async function clientApplySourceIps(clientName) {
    const base_ip = document.getElementById('c-' + clientName + '-source-ip-base').value.trim();
    const count = parseInt(document.getElementById('c-' + clientName + '-source-ip-count').value);
    const res = await apiPost('/api/client/' + clientName + '/source_ips', { enabled: true, base_ip, count });
    addClientLog(clientName, '[SOURCE IP] ' + (res.message || ''));
    const list = document.getElementById('c-' + clientName + '-source-ip-list');
    if (list && res.ips && res.ips.length) list.textContent = 'Active: ' + res.ips.join(', ');
}

async function clientLoadSourceIps(clientName) {
    try {
        const resp = await fetch('/api/client/' + clientName + '/source_ips');
        const data = await resp.json();
        const toggle = document.getElementById('c-' + clientName + '-source-ip-toggle');
        if (toggle) toggle.checked = data.enabled;
        const cfg = document.getElementById('c-' + clientName + '-source-ip-config');
        if (cfg) cfg.style.display = data.enabled ? 'block' : 'none';
        const list = document.getElementById('c-' + clientName + '-source-ip-list');
        if (list && data.ips && data.ips.length) list.textContent = 'Active: ' + data.ips.join(', ');
    } catch(e) {}
}

// ─── Client Proxy ───────────────────────────────────────────
async function clientLoadProxy(clientName) {
    try {
        var resp = await fetch('/api/client/' + clientName + '/proxy');
        var data = await resp.json();
        var el = function(id) { return document.getElementById('c-' + clientName + '-proxy-' + id); };
        if (el('enabled')) el('enabled').checked = !!data.enabled;
        if (el('type')) el('type').value = data.type || 'http';
        if (el('host')) el('host').value = data.host || '';
        if (el('port')) el('port').value = data.port || 8080;
        if (el('username')) el('username').value = data.username || '';
        if (el('password')) el('password').value = data.password || '';
    } catch(e) {}
}

async function clientSaveProxy(clientName) {
    var el = function(id) { return document.getElementById('c-' + clientName + '-proxy-' + id); };
    var payload = {
        enabled: el('enabled') ? el('enabled').checked : false,
        type: el('type') ? el('type').value : 'http',
        host: el('host') ? el('host').value.trim() : '',
        port: el('port') ? parseInt(el('port').value) : 8080,
        username: el('username') ? el('username').value.trim() : '',
        password: el('password') ? el('password').value : ''
    };
    var res = await apiPost('/api/client/' + clientName + '/proxy', payload);
    addClientLog(clientName, '[PROXY] ' + (res.message || 'Config updated'));
    showNotification(res.message || 'Proxy config updated', 'success');
}

async function clientTestProxy(clientName) {
    var el = function(id) { return document.getElementById('c-' + clientName + '-proxy-' + id); };
    var payload = {
        type: el('type') ? el('type').value : 'http',
        host: el('host') ? el('host').value.trim() : '',
        port: el('port') ? parseInt(el('port').value) : 8080,
        username: el('username') ? el('username').value.trim() : '',
        password: el('password') ? el('password').value : ''
    };
    showNotification('Testing proxy...', 'info');
    try {
        var resp = await fetch('/api/client/' + clientName + '/proxy/test', {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
        });
        var data = await resp.json();
        showNotification(data.message || 'Test done', data.ok ? 'success' : 'error');
        addClientLog(clientName, '[PROXY] Test: ' + (data.message || ''));
    } catch(e) {
        showNotification('Proxy test failed: ' + e.message, 'error');
    }
}

// ─── Client Topology ────────────────────────────────────────
var clientTopoNetworks = {};
var clientTopoEdges = {};
var clientTopoAnimIntervals = {};
var clientTopoAnimState = {};
var clientTopoHasTraffic = {};
var clientTopoActiveEdgeIds = {};

var TOPO_COLORS = ['#2563eb','#059669','#d97706','#7c3aed','#0891b2','#dc2626','#0d9488','#ea580c','#4f46e5','#16a34a'];

var TOPO_ICONS = {
    client: function(fill, stroke) { return 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 56 56"><defs><filter id="s"><feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.15"/></filter></defs><rect x="8" y="12" width="40" height="28" rx="3" fill="' + fill + '" stroke="' + stroke + '" stroke-width="2" filter="url(#s)"/><rect x="16" y="17" width="24" height="16" rx="1.5" fill="#fff" opacity="0.6"/><path d="M20 44h16M28 40v4" stroke="' + stroke + '" stroke-width="2" stroke-linecap="round"/><rect x="18" y="44" width="20" height="3" rx="1.5" fill="' + stroke + '" opacity="0.5"/></svg>'); },
    server: function(fill, stroke) { return 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 56 56"><defs><filter id="s"><feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.15"/></filter></defs><rect x="10" y="6" width="36" height="44" rx="4" fill="' + fill + '" stroke="' + stroke + '" stroke-width="2" filter="url(#s)"/><rect x="15" y="12" width="26" height="8" rx="2" fill="#fff" opacity="0.5"/><circle cx="36" cy="16" r="2" fill="' + stroke + '"/><rect x="15" y="24" width="26" height="8" rx="2" fill="#fff" opacity="0.5"/><circle cx="36" cy="28" r="2" fill="' + stroke + '"/><rect x="15" y="36" width="26" height="8" rx="2" fill="#fff" opacity="0.5"/><circle cx="36" cy="40" r="2" fill="' + stroke + '"/></svg>'); },
    router: function(fill, stroke) { return 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48"><defs><filter id="s"><feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.15"/></filter></defs><circle cx="24" cy="24" r="18" fill="' + fill + '" stroke="' + stroke + '" stroke-width="2" filter="url(#s)"/><circle cx="24" cy="24" r="5" fill="' + stroke + '" opacity="0.8"/><path d="M24 10v8M24 30v8M10 24h8M30 24h8M14.5 14.5l5.5 5.5M28 28l5.5 5.5M33.5 14.5l-5.5 5.5M20 28l-5.5 5.5" stroke="' + stroke + '" stroke-width="1.5" stroke-linecap="round" opacity="0.6"/></svg>'); },
    hop: function(fill, stroke) { return 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><circle cx="16" cy="16" r="10" fill="' + fill + '" stroke="' + stroke + '" stroke-width="2"/><circle cx="16" cy="16" r="4" fill="' + stroke + '" opacity="0.4"/></svg>'); },
    timeout: function() { return 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><circle cx="16" cy="16" r="10" fill="#fef2f2" stroke="#ef4444" stroke-width="2" stroke-dasharray="4 3"/><text x="16" y="20" text-anchor="middle" fill="#ef4444" font-size="14" font-weight="bold">?</text></svg>'); }
};

async function clientRefreshTopology(clientName) {
    try {
        var resp = await fetch('/api/client/' + clientName + '/topology');
        var data = await resp.json();
        clientRenderTopology(clientName, data);
    } catch(e) {
        var container = document.getElementById('c-' + clientName + '-topo-container');
        if (container) container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-secondary)">Failed to load topology</div>';
    }
}

function _topoTip(lines) {
    var el = document.createElement('div');
    el.className = 'topo-tooltip';
    el.innerHTML = lines.join('<br>');
    return el;
}

function clientRenderTopology(clientName, data) {
    var container = document.getElementById('c-' + clientName + '-topo-container');
    if (!container) return;

    var nodes = new vis.DataSet();
    var edges = new vis.DataSet();
    clientTopoEdges[clientName] = edges;
    clientTopoActiveEdgeIds[clientName] = [];

    var pathsObj = data.paths || {};
    var routers = data.routers || [];

    var routerByIp = {};
    routers.forEach(function(r) { routerByIp[r.ip] = r; });

    var pathKeys = Object.keys(pathsObj).filter(function(k) { return k !== 'default'; });
    var runningPaths = pathKeys.filter(function(k) { return pathsObj[k].running; });
    var hasTraffic = runningPaths.length > 0;
    clientTopoHasTraffic[clientName] = hasTraffic;

    var hopSigMap = {};
    pathKeys.forEach(function(k) {
        var p = pathsObj[k];
        var sig = (p.hops || []).map(function(h) { return h.ip; }).join(',');
        if (!hopSigMap[sig]) hopSigMap[sig] = [];
        hopSigMap[sig].push(k);
    });

    // CLIENT node — laptop icon
    nodes.add({ id: 'client', label: 'Client', shape: 'image', size: 30,
        image: TOPO_ICONS.client('#ecfdf5', '#059669'),
        font: { size: 12, face: '-apple-system, sans-serif', color: '#1e2a3a', vadjust: 8 },
        level: 0,
        title: _topoTip(['<strong style="font-size:13px">Client</strong>', '<span style="color:#6b7a8d">IP: ' + data.client_ip + '</span>']) });

    // SERVER node — server rack icon
    var maxHops = 1;
    pathKeys.forEach(function(k) { var h = (pathsObj[k].hops || []).length; if (h > maxHops) maxHops = h; });
    nodes.add({ id: 'server', label: 'Server', shape: 'image', size: 30,
        image: TOPO_ICONS.server('#eff6ff', '#2563eb'),
        font: { size: 12, face: '-apple-system, sans-serif', color: '#1e2a3a', vadjust: 8 },
        level: maxHops + 1,
        title: _topoTip(['<strong style="font-size:13px">Server</strong>', '<span style="color:#6b7a8d">IP: ' + data.server_host + '</span>']) });

    var renderedSigs = {};
    var pathIndex = 0;
    var addedNodes = { client: true, server: true };
    var legendItems = [];

    pathKeys.forEach(function(pathKey) {
        var path = pathsObj[pathKey];
        var hops = path.hops || [];
        var sig = hops.map(function(h) { return h.ip; }).join(',');

        if (renderedSigs[sig]) return;
        renderedSigs[sig] = true;

        var mergedKeys = hopSigMap[sig] || [pathKey];
        var labels = mergedKeys.map(function(k) { return pathsObj[k].label; });
        var isRunning = mergedKeys.some(function(k) { return k !== 'default' && pathsObj[k].running; });
        var isDefaultOnly = mergedKeys.length === 1 && mergedKeys[0] === 'default';

        var color = isDefaultOnly ? '#94a3b8' : TOPO_COLORS[pathIndex % TOPO_COLORS.length];
        if (!isDefaultOnly) pathIndex++;

        legendItems.push({ labels: labels, color: color, running: isRunning, defaultOnly: isDefaultOnly });

        var edgeWidth = isRunning ? 3.5 : 1.5;

        var nodeChain = ['client'];
        for (var i = 0; i < hops.length; i++) {
            var h = hops[i];
            var isLast = i === hops.length - 1;
            var isTimeout = h.ip === '*';

            if (isLast && !isTimeout && (h.ip === data.server_host || h.ip === data.client_ip)) continue;

            var sharedId = 'hop_shared_' + h.hop + '_' + h.ip;
            if (addedNodes[sharedId]) { nodeChain.push(sharedId); continue; }

            var router = routerByIp[h.ip];
            var nodeImage, nodeLabel = '', nodeSize = 18, tipLines = [];

            if (isTimeout) {
                nodeImage = TOPO_ICONS.timeout();
                nodeSize = 16;
                tipLines = ['<strong style="font-size:13px">Hop ' + h.hop + '</strong>', '<span style="color:#ef4444;font-weight:500">* Request timed out</span>'];
            } else if (router) {
                var modeColorMap = { healthy: { fill: '#ecfdf5', stroke: '#059669' }, impaired: { fill: '#fffbeb', stroke: '#d97706' }, link_down: { fill: '#fef2f2', stroke: '#dc2626' } };
                var mc = modeColorMap[router.current_mode] || { fill: '#eff6ff', stroke: color };
                nodeImage = TOPO_ICONS.router(mc.fill, mc.stroke);
                nodeLabel = router.name; nodeSize = 26;
                var mode = router.current_mode ? router.current_mode.replace('_', ' ') : 'unknown';
                var modeTextColors = { healthy: '#059669', impaired: '#d97706', link_down: '#dc2626' };
                var modeColor = modeTextColors[router.current_mode] || '#6b7a8d';
                tipLines = ['<strong style="font-size:13px">' + router.name + '</strong>',
                    '<span style="color:#6b7a8d">IP: ' + h.ip + '</span>',
                    'Status: <span style="color:' + modeColor + ';font-weight:600">' + mode + '</span>'];
                if (h.rtt && h.rtt !== '--') tipLines.push('Latency: <strong>' + h.rtt + ' ms</strong>');
                if (router.current_mode === 'impaired' && router.impairment_config) {
                    var ic = router.impairment_config;
                    var parts = [];
                    if (ic.latency_ms) parts.push(ic.latency_ms + 'ms delay');
                    if (ic.jitter_ms) parts.push(ic.jitter_ms + 'ms jitter');
                    if (ic.packet_loss_pct) parts.push(ic.packet_loss_pct + '% loss');
                    if (ic.bandwidth_mbps) parts.push(ic.bandwidth_mbps + ' Mbps');
                    if (parts.length) tipLines.push('<span style="color:#d97706;font-size:11px">' + parts.join(' \u00b7 ') + '</span>');
                }
            } else {
                nodeImage = TOPO_ICONS.hop('#eff6ff', color);
                nodeSize = 16;
                tipLines = ['<strong style="font-size:13px">Hop ' + h.hop + '</strong>', '<span style="color:#6b7a8d">IP: ' + h.ip + '</span>'];
                if (h.rtt && h.rtt !== '--') tipLines.push('Latency: <strong>' + h.rtt + ' ms</strong>');
            }

            nodes.add({ id: sharedId, label: nodeLabel, shape: 'image', size: nodeSize,
                image: nodeImage,
                font: { size: 10, face: '-apple-system, sans-serif', color: '#1e2a3a', vadjust: 6 },
                level: i + 1,
                title: _topoTip(tipLines) });
            addedNodes[sharedId] = true;
            nodeChain.push(sharedId);
        }
        nodeChain.push('server');

        var roundness = pathIndex > 1 ? pathIndex * 0.12 : 0;
        for (var j = 0; j < nodeChain.length - 1; j++) {
            var edgeId = 'e_' + pathKey + '_' + j;
            edges.add({ id: edgeId, from: nodeChain[j], to: nodeChain[j + 1],
                arrows: { to: { enabled: true, scaleFactor: 0.5, type: 'arrow' } },
                color: { color: isRunning ? color : '#cbd5e1', highlight: color, hover: color },
                width: edgeWidth,
                dashes: isRunning ? [10, 5] : (isDefaultOnly ? [5, 5] : false),
                smooth: roundness > 0 ? { type: 'curvedCW', roundness: roundness } : { type: 'cubicBezier' },
                hoverWidth: 1.5, selectionWidth: 2 });
            if (isRunning) clientTopoActiveEdgeIds[clientName].push({ id: edgeId, color: color });
        }
    });

    if (pathKeys.length === 0) {
        container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-secondary);font-size:13px;padding:40px 0;">No active traffic flows \u2014 start a protocol to see topology</div>';
        if (clientTopoNetworks[clientName]) { clientTopoNetworks[clientName].destroy(); clientTopoNetworks[clientName] = null; }
        var _legendEl = document.getElementById('c-' + clientName + '-topo-legend');
        if (_legendEl) _legendEl.innerHTML = '';
        var _statsEl = document.getElementById('c-' + clientName + '-topo-stats');
        if (_statsEl) _statsEl.innerHTML = '<span style="color:var(--text-secondary)">\u25CB No active traffic flows</span>';
        return;
    }

    var options = {
        layout: { hierarchical: { direction: 'LR', sortMethod: 'directed', levelSeparation: 160, nodeSpacing: 60 } },
        physics: false,
        interaction: { hover: true, tooltipDelay: 80, dragNodes: true, zoomView: true, dragView: true }
    };

    // Protocol legend bar
    var legendId = 'c-' + clientName + '-topo-legend';
    var legendEl = document.getElementById(legendId);
    if (!legendEl) {
        legendEl = document.createElement('div');
        legendEl.id = legendId;
        legendEl.className = 'topo-legend';
        container.parentNode.insertBefore(legendEl, container.nextSibling);
    }
    if (legendItems.length > 0) {
        legendEl.innerHTML = legendItems.map(function(li) {
            var names = li.labels.join(', ');
            var opacity = li.running ? '1' : '0.5';
            return '<span class="topo-legend-item" style="opacity:' + opacity + '">' +
                '<span class="topo-legend-dot" style="background:' + li.color + '"></span>' +
                names + '</span>';
        }).join('');
    } else {
        legendEl.innerHTML = '';
    }

    // Stats bar
    var statsId = 'c-' + clientName + '-topo-stats';
    var statsEl = document.getElementById(statsId);
    if (!statsEl) {
        statsEl = document.createElement('div');
        statsEl.id = statsId;
        statsEl.className = 'topo-stats';
        container.parentNode.appendChild(statsEl);
    }
    if (hasTraffic) {
        var statParts = runningPaths.map(function(k) {
            var p = pathsObj[k];
            var s = p.stats || {};
            var sp = [p.label];
            if (s.bytes_sent) sp.push(fmtBytes(s.bytes_sent) + ' sent');
            if (s.bytes_recv) sp.push(fmtBytes(s.bytes_recv) + ' recv');
            if (s.requests) sp.push(s.requests + ' reqs');
            return sp.join(' \u00b7 ');
        });
        statsEl.innerHTML = '<strong style="color:#059669">\u25CF Active Flows:</strong> ' + statParts.join(' &nbsp;\u2502&nbsp; ');
    } else {
        statsEl.innerHTML = '<span style="color:var(--text-secondary)">\u25CB No active traffic flows</span>';
    }

    if (clientTopoNetworks[clientName]) {
        clientTopoNetworks[clientName].setData({ nodes: nodes, edges: edges });
    } else {
        clientTopoNetworks[clientName] = new vis.Network(container, { nodes: nodes, edges: edges }, options);
    }

    // Animation
    if (hasTraffic && !clientTopoAnimIntervals[clientName]) {
        clientTopoAnimState[clientName] = 0;
        clientTopoAnimIntervals[clientName] = setInterval(function() {
            var es = clientTopoEdges[clientName];
            var activeEdges = clientTopoActiveEdgeIds[clientName] || [];
            if (!es || !clientTopoHasTraffic[clientName]) return;
            var st = (clientTopoAnimState[clientName] + 1) % 4;
            clientTopoAnimState[clientName] = st;
            var dp = [[10,5],[8,7],[5,10],[7,8]];
            var wp = [3.5, 4, 3.5, 3];
            activeEdges.forEach(function(e) { es.update({ id: e.id, dashes: dp[st], width: wp[st], color: { color: e.color } }); });
        }, 600);
    } else if (!hasTraffic && clientTopoAnimIntervals[clientName]) {
        clearInterval(clientTopoAnimIntervals[clientName]);
        clientTopoAnimIntervals[clientName] = null;
    }
}

// ─── Client Status Polling ───────────────────────────────────
async function pollClientStatus(clientName) {
    try {
        const resp = await fetch('/api/client/' + clientName + '/status');
        const data = await resp.json();
        if (data.error) return;
        let totSent=0, totRecv=0, totReqs=0, totErrs=0;
        // Aggregate stats per base protocol (http_1, http_2 → http, ext_https_2 → ext_https)
        var protoAgg = {};
        for (const [jobKey, info] of Object.entries(data.jobs || {})) {
            var parts = jobKey.split('_');
            var base;
            if (parts.length >= 3 && !isNaN(parts[parts.length - 1])) {
                base = parts.slice(0, -1).join('_');
            } else if (parts.length === 2 && !isNaN(parts[1])) {
                base = parts[0];
            } else {
                base = jobKey;
            }
            if (!protoAgg[base]) protoAgg[base] = { running: false, flows: 0, remaining: -1, elapsed: 0,
                stats: {bytes_sent:0, bytes_recv:0, requests:0, errors:0} };
            var agg = protoAgg[base];
            if (info.running) { agg.running = true; agg.flows++; }
            agg.stats.bytes_sent += info.stats.bytes_sent;
            agg.stats.bytes_recv += info.stats.bytes_recv;
            agg.stats.requests += info.stats.requests;
            agg.stats.errors += info.stats.errors;
            if (info.remaining >= 0) agg.remaining = Math.max(agg.remaining, info.remaining);
            agg.elapsed = Math.max(agg.elapsed, info.elapsed);
            totSent += info.stats.bytes_sent; totRecv += info.stats.bytes_recv;
            totReqs += info.stats.requests; totErrs += info.stats.errors;
        }
        for (const [proto, agg] of Object.entries(protoAgg)) {
            const card = document.getElementById('c-' + clientName + '-proto-' + proto);
            const badge = document.getElementById('c-' + clientName + '-status-' + proto);
            const timer = document.getElementById('c-' + clientName + '-timer-' + proto);
            if (!card) continue;
            if (agg.running) {
                card.classList.add('running'); badge.classList.add('running');
                badge.textContent = agg.flows > 1 ? agg.flows + ' Flows' : 'Running';
                timer.style.display = '';
                timer.textContent = agg.remaining >= 0 ? fmtTime(agg.remaining) : fmtTime(agg.elapsed);
            } else {
                card.classList.remove('running'); badge.classList.remove('running');
                badge.textContent = 'Stopped'; timer.style.display = 'none';
            }
        }
        // Reset cards with no jobs
        for (const proto of Object.keys(PROTOCOLS)) {
            if (!protoAgg[proto]) {
                const card = document.getElementById('c-' + clientName + '-proto-' + proto);
                const badge = document.getElementById('c-' + clientName + '-status-' + proto);
                const timer = document.getElementById('c-' + clientName + '-timer-' + proto);
                if (card) card.classList.remove('running');
                if (badge) { badge.classList.remove('running'); badge.textContent = 'Stopped'; }
                if (timer) timer.style.display = 'none';
            }
        }
        // Collect logs from all protocols with timestamps for sorting
        let allLogs = [];
        for (const [proto, info] of Object.entries(data.jobs || {})) {
            if (info.logs) {
                for (const line of info.logs) {
                    allLogs.push('[' + proto.toUpperCase() + '] ' + line);
                }
            }
        }
        // Sort by embedded timestamp [HH:MM:SS]
        allLogs.sort(function(a, b) {
            var ta = a.match(/\[(\d{2}:\d{2}:\d{2})\]/);
            var tb = b.match(/\[(\d{2}:\d{2}:\d{2})\]/);
            if (ta && tb) return ta[1].localeCompare(tb[1]);
            return 0;
        });
        // Update activity log panel with remote logs
        const panel = document.getElementById('log-' + clientName);
        if (panel && allLogs.length > 0) {
            const lastN = allLogs.slice(-200);
            panel.innerHTML = lastN.map(l => {
                const cls = l.toLowerCase().includes('error') ? ' error' : '';
                const d = document.createElement('div');
                d.textContent = l;
                return '<div class="log-entry' + cls + '">' + d.innerHTML + '</div>';
            }).join('');
            panel.scrollTop = panel.scrollHeight;
        }
        const el = id => document.getElementById('c-' + clientName + '-' + id);
        if (el('sent')) el('sent').textContent = fmtBytes(totSent);
        if (el('recv')) el('recv').textContent = fmtBytes(totRecv);
        if (el('reqs')) el('reqs').textContent = totReqs.toLocaleString();
        if (el('errors')) el('errors').textContent = totErrs.toLocaleString();
    } catch(e) {}
}

// ─── Server Status Polling ───────────────────────────────────
async function pollServerStatus() {
    try {
        const resp = await fetch('/api/server-stats');
        const data = await resp.json();
        document.getElementById('total-recv').textContent = fmtBytes(data.aggregate.bytes_recv);
        document.getElementById('total-sent').textContent = fmtBytes(data.aggregate.bytes_sent);
        document.getElementById('total-reqs').textContent = data.aggregate.requests.toLocaleString();
        document.getElementById('total-conns').textContent = data.aggregate.active_connections;
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
                '<button class="btn btn-secondary" onclick="restartService(\'' + name + '\')" ' +
                'style="padding:2px 8px;font-size:10px;margin-left:auto">Restart</button>' +
                '</div>' + statsHtml + '</div>';
        }
        const tbody = document.getElementById('conn-table-body');
        if (!data.connections.length) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#94a3b8">No active connections</td></tr>';
        } else {
            tbody.innerHTML = data.connections.map(c =>
                '<tr><td>' + c.proto + '</td><td>' + c.local_port + '</td><td>' +
                c.remote + '</td><td>' + c.state + '</td></tr>').join('');
        }
        document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
    } catch(e) {}
}

// ─── FTP File Management ────────────────────────────────────
async function loadFtpFiles() {
    try {
        const resp = await fetch('/api/files');
        const data = await resp.json();
        const tbody = document.getElementById('ftp-files-body');
        if (!data.files || !data.files.length) {
            tbody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:#94a3b8">No files</td></tr>';
            return;
        }
        tbody.innerHTML = data.files.map(f =>
            '<tr><td>' + f.name + '</td><td>' + fmtBytes(f.size) + '</td>' +
            '<td><button class="btn btn-danger" style="padding:2px 8px;font-size:11px" ' +
            'onclick="deleteFtpFile(\'' + f.name + '\')">Delete</button></td></tr>').join('');
    } catch(e) {}
}

async function uploadFtpFile() {
    const input = document.getElementById('ftp-upload-input');
    if (!input.files.length) return;
    const file = input.files[0];
    const form = new FormData();
    form.append('file', file);
    const status = document.getElementById('upload-status');
    status.style.display = 'block';
    status.textContent = 'Uploading ' + file.name + '...';
    try {
        const resp = await fetch('/api/files/upload', { method: 'POST', body: form });
        const data = await resp.json();
        if (data.ok) {
            status.textContent = 'Uploaded ' + data.filename + ' (' + fmtBytes(data.size) + ')';
            loadFtpFiles();
        } else {
            status.style.background = '#7f1d1d';
            status.textContent = 'Error: ' + (data.error || 'Upload failed');
        }
    } catch(e) {
        status.style.background = '#7f1d1d';
        status.textContent = 'Upload error: ' + e;
    }
    input.value = '';
    setTimeout(() => { status.style.display = 'none'; status.style.background = '#065f46'; }, 5000);
}

async function deleteFtpFile(name) {
    if (!confirm('Delete file "' + name + '"?')) return;
    await fetch('/api/files/' + name, { method: 'DELETE' });
    loadFtpFiles();
}

// ─── Auto-refresh Toggle ─────────────────────────────────────
function toggleAutoRefresh() {
    const checkboxes = document.querySelectorAll('[id^="auto-refresh-"]');
    let enabled = true;
    checkboxes.forEach(cb => { if (cb.id === 'auto-refresh-' + activeTab) enabled = cb.checked; });
    if (enabled) {
        if (!pollInterval) { pollInterval = setInterval(pollAll, 2000); pollAll(); }
    } else {
        if (pollInterval) { clearInterval(pollInterval); pollInterval = null; }
    }
}

// ─── Polling Loop ────────────────────────────────────────────
async function pollAll() {
    if (activeTab === 'server') {
        await pollServerStatus();
        loadFtpFiles();
    } else if (clientList[activeTab]) {
        await pollClientStatus(activeTab);
        clientPollRouterStatus(activeTab);
    }
}

// ─── Client Management ──────────────────────────────────────
function showAddClient() { document.getElementById('add-client-modal').classList.add('show'); }
function hideAddClient() { document.getElementById('add-client-modal').classList.remove('show'); }

async function addClient() {
    const name = document.getElementById('client-name').value.trim();
    const url = document.getElementById('client-url').value.trim();
    if (!name || !url) return;
    const res = await apiPost('/api/clients', { name, url });
    if (res.ok) {
        clientList[name] = url;
        renderClientTab(name);
        rebuildTabs();
        hideAddClient();
        document.getElementById('client-name').value = '';
        document.getElementById('client-url').value = '';
        clientLoadRouters(name); clientLoadSourceIps(name); clientLoadProxy(name); clientRefreshTopology(name);
        switchTab(name);
    }
}

async function removeClient(name) {
    if (!confirm('Remove client "' + name + '"?')) return;
    await fetch('/api/clients/' + name, { method: 'DELETE' });
    delete clientList[name];
    const tab = document.getElementById('tab-' + name);
    if (tab) tab.remove();
    if (activeTab === name) activeTab = 'server';
    rebuildTabs();
    switchTab('server');
}

async function loadClients() {
    try {
        const resp = await fetch('/api/clients');
        const data = await resp.json();
        clientList = data;
        for (const name of Object.keys(data)) {
            renderClientTab(name);
            clientLoadRouters(name); clientLoadSourceIps(name); clientLoadProxy(name); clientRefreshTopology(name);
        }
        rebuildTabs();
    } catch(e) {}
}

// ─── Init ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadClients();
    loadFtpFiles();
    pollInterval = setInterval(pollAll, 2000);
    setInterval(function() {
        if (activeTab && activeTab !== 'server') clientRefreshTopology(activeTab);
    }, 10000);
    pollAll();
});
</script>
</body>
</html>
"""

# ─── Utility Functions ─────────────────────────────────────────


def read_json_file(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_connections_and_counts():
    """Single ss call returning (connections_list, port_counts_dict)."""
    ports = {
        80: 'HTTP', 443: 'HTTPS',
        5201: 'iperf3', 5202: 'iperf3', 5203: 'iperf3',
        9999: 'HTTP (9999)', 53: 'DNS (53)',
        21: 'FTP', 2222: 'SSH',
    }
    connections = []
    counts = {}
    try:
        result = subprocess.run(
            ['ss', '-tunp', '--no-header'],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) < 6:
                continue
            state = parts[1]
            local = parts[4]
            remote = parts[5]
            local_port = local.rsplit(':', 1)[-1] if ':' in local else ''
            try:
                port_num = int(local_port)
            except ValueError:
                continue
            counts[port_num] = counts.get(port_num, 0) + 1
            # Convert IPv6-mapped IPv4 (::ffff:10.0.0.1) to plain IPv4
            remote_display = remote
            if '::ffff:' in remote_display:
                remote_display = remote_display.replace('::ffff:', '')
            if port_num in ports:
                connections.append({
                    'proto': ports[port_num],
                    'local_port': port_num,
                    'remote': remote_display,
                    'state': state,
                })
    except Exception:
        pass
    return connections, counts


def proxy_to_client(name, path, method='GET', data=None):
    """Proxy a request to a registered client."""
    with clients_lock:
        url = clients.get(name)
    if not url:
        return {'error': f'Client {name} not found'}, 404
    target = url.rstrip('/') + path
    try:
        if method == 'POST':
            r = http_client.post(target, json=data, timeout=10)
        elif method == 'DELETE':
            r = http_client.delete(target, timeout=10)
        else:
            r = http_client.get(target, timeout=10)
        return r.json(), r.status_code
    except Exception as e:
        return {'error': f'Cannot reach client {name}: {e}'}, 502


# ─── Routes ──────────────────────────────────────────────────

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/server-stats')
def server_stats():
    http = read_json_file('/tmp/http_stats.json')
    echo = read_json_file('/tmp/echo_stats.json')
    ftp = read_json_file('/tmp/ftp_stats.json')
    ssh = read_json_file('/tmp/ssh_stats.json')
    connections, conn_counts = get_connections_and_counts()

    echo_http = echo.get('http', {})
    echo_dns = echo.get('dns', {})

    total_recv = (http.get('bytes_recv', 0) + echo_http.get('bytes_recv', 0) +
                  echo_dns.get('bytes_recv', 0) + ftp.get('bytes_recv', 0))
    total_sent = (http.get('bytes_sent', 0) + echo_http.get('bytes_sent', 0) +
                  echo_dns.get('bytes_sent', 0) + ftp.get('bytes_sent', 0))
    total_reqs = (http.get('requests', 0) + echo_http.get('requests', 0) +
                  echo_dns.get('queries', 0) + ftp.get('downloads', 0) +
                  ftp.get('uploads', 0) + ssh.get('sessions', 0))
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
        'HTTP (9999)': {
            'active_connections': conn_counts.get(9999, 0),
            'stats': {
                'requests': echo_http.get('requests', 0),
                'gets': echo_http.get('gets', 0),
                'posts': echo_http.get('posts', 0),
                'active': echo_http.get('active', 0),
                'bytes_recv': echo_http.get('bytes_recv', 0),
                'bytes_sent': echo_http.get('bytes_sent', 0),
            }
        },
        'DNS (53)': {
            'active_connections': max(conn_counts.get(53, 0), 1 if (time.time() - echo_dns.get('last_active', 0)) < 10 else 0),
            'stats': {
                'queries': echo_dns.get('queries', 0),
                'forwarded': echo_dns.get('forwarded', 0),
                'errors': echo_dns.get('errors', 0),
                'bytes_recv': echo_dns.get('bytes_recv', 0),
                'bytes_sent': echo_dns.get('bytes_sent', 0),
            }
        },
        'iperf3': {
            'active_connections': conn_counts.get(5201, 0) + conn_counts.get(5202, 0) + conn_counts.get(5203, 0),
            'stats': {}
        },
        'FTP': {
            'active_connections': conn_counts.get(21, 0),
            'stats': {
                'connections': ftp.get('connections', 0),
                'downloads': ftp.get('downloads', 0),
                'uploads': ftp.get('uploads', 0),
                'bytes_sent': ftp.get('bytes_sent', 0),
                'bytes_recv': ftp.get('bytes_recv', 0),
                'errors': ftp.get('errors', 0),
            }
        },
        'SSH': {
            'active_connections': conn_counts.get(2222, 0),
            'stats': {
                'sessions': ssh.get('sessions', 0),
                'active_sessions': ssh.get('active_sessions', 0),
                'failed_logins': ssh.get('failed_logins', 0),
            }
        },
    }

    return jsonify({
        'aggregate': {
            'bytes_recv': total_recv, 'bytes_sent': total_sent,
            'requests': total_reqs, 'active_connections': total_conns,
        },
        'services': services,
        'connections': connections,
    })


# Map display names to supervisord program names
SERVICE_PROGRAMS = {
    'HTTP/HTTPS': ['nginx'],
    'HTTP (9999)': ['echo_server'],
    'DNS (53)': ['echo_server'],
    'iperf3': ['iperf3_5201', 'iperf3_5202', 'iperf3_5203'],
    'FTP': ['vsftpd'],
    'SSH': ['sshd'],
}


@app.route('/api/service/restart', methods=['POST'])
def restart_service():
    d = request.get_json(force=True, silent=True) or {}
    service_name = d.get('service', '')
    if not service_name:
        return jsonify({"error": "service name required"}), 400

    programs = SERVICE_PROGRAMS.get(service_name)
    if not programs:
        return jsonify({"error": f"Unknown service: {service_name}"}), 400

    results = []
    for prog in programs:
        try:
            result = subprocess.run(
                ['supervisorctl', 'restart', prog],
                capture_output=True, text=True, timeout=15)
            results.append(f"{prog}: {result.stdout.strip() or result.stderr.strip()}")
        except Exception as e:
            results.append(f"{prog}: error — {e}")

    return jsonify({"ok": True, "service": service_name, "results": results,
                    "message": f"{service_name} restarted"})


@app.route('/api/service/restart-all', methods=['POST'])
def restart_all_services():
    try:
        result = subprocess.run(
            ['supervisorctl', 'restart', 'all'],
            capture_output=True, text=True, timeout=30)
        return jsonify({"ok": True, "message": "All services restarted",
                        "output": result.stdout.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Client Registry ────────────────────────────────────────

@app.route('/api/clients', methods=['GET'])
def list_clients():
    with clients_lock:
        return jsonify(dict(clients))


@app.route('/api/clients', methods=['POST'])
def register_client():
    data = request.json or {}
    name = data.get('name', '').strip()
    url = data.get('url', '').strip()
    if not name or not url:
        return jsonify({'ok': False, 'error': 'name and url required'}), 400
    with clients_lock:
        clients[name] = url
        save_clients()
    return jsonify({'ok': True, 'message': f'Client {name} added'})


@app.route('/api/clients/<name>', methods=['DELETE'])
def remove_client(name):
    with clients_lock:
        if name in clients:
            del clients[name]
            save_clients()
    return jsonify({'ok': True, 'message': f'Client {name} removed'})


# ─── Client Proxy Endpoints ─────────────────────────────────

@app.route('/api/client/<name>/status')
def client_status(name):
    result, code = proxy_to_client(name, '/api/status')
    return jsonify(result), code


@app.route('/api/client/<name>/start', methods=['POST'])
def client_start(name):
    result, code = proxy_to_client(name, '/api/start', 'POST', request.json or {})
    return jsonify(result), code


@app.route('/api/client/<name>/stop', methods=['POST'])
def client_stop(name):
    result, code = proxy_to_client(name, '/api/stop', 'POST', request.json or {})
    return jsonify(result), code


@app.route('/api/client/<name>/routers', methods=['GET'])
def client_list_routers(name):
    result, code = proxy_to_client(name, '/api/routers')
    return jsonify(result), code


@app.route('/api/client/<name>/routers', methods=['POST'])
def client_add_router(name):
    result, code = proxy_to_client(name, '/api/routers', 'POST', request.json or {})
    return jsonify(result), code


@app.route('/api/client/<name>/routers/<rid>', methods=['DELETE'])
def client_remove_router(name, rid):
    result, code = proxy_to_client(name, f'/api/routers/{rid}', 'DELETE')
    return jsonify(result), code


@app.route('/api/client/<name>/routers/<rid>/connect', methods=['POST'])
def client_connect_router(name, rid):
    result, code = proxy_to_client(name, f'/api/routers/{rid}/connect', 'POST', {})
    return jsonify(result), code


@app.route('/api/client/<name>/routers/<rid>/disconnect', methods=['POST'])
def client_disconnect_router(name, rid):
    result, code = proxy_to_client(name, f'/api/routers/{rid}/disconnect', 'POST', {})
    return jsonify(result), code


@app.route('/api/client/<name>/routers/<rid>/interfaces')
def client_router_interfaces(name, rid):
    result, code = proxy_to_client(name, f'/api/routers/{rid}/interfaces')
    return jsonify(result), code


@app.route('/api/client/<name>/routers/<rid>/select-interface', methods=['POST'])
def client_router_select_interface(name, rid):
    result, code = proxy_to_client(name, f'/api/routers/{rid}/select-interface', 'POST', request.json or {})
    return jsonify(result), code


@app.route('/api/client/<name>/routers/<rid>/mode', methods=['POST'])
def client_router_mode(name, rid):
    result, code = proxy_to_client(name, f'/api/routers/{rid}/mode', 'POST', request.json or {})
    return jsonify(result), code


@app.route('/api/client/<name>/routers/<rid>/status')
def client_router_status(name, rid):
    result, code = proxy_to_client(name, f'/api/routers/{rid}/status')
    return jsonify(result), code


@app.route('/api/client/<name>/server_host')
def client_server_host(name):
    result, code = proxy_to_client(name, '/api/server_host')
    return jsonify(result), code


@app.route('/api/client/<name>/source_ips', methods=['GET', 'POST'])
def client_source_ips(name):
    if request.method == 'POST':
        result, code = proxy_to_client(name, '/api/source_ips', 'POST', request.json or {})
    else:
        result, code = proxy_to_client(name, '/api/source_ips')
    return jsonify(result), code


@app.route('/api/client/<name>/proxy', methods=['GET', 'POST'])
def client_proxy(name):
    if request.method == 'POST':
        result, code = proxy_to_client(name, '/api/proxy', 'POST', request.json or {})
    else:
        result, code = proxy_to_client(name, '/api/proxy')
    return jsonify(result), code


@app.route('/api/client/<name>/proxy/test', methods=['POST'])
def client_proxy_test(name):
    result, code = proxy_to_client(name, '/api/proxy/test', 'POST', request.json or {})
    return jsonify(result), code


@app.route('/api/client/<name>/topology')
def client_topology(name):
    result, code = proxy_to_client(name, '/api/topology')
    return jsonify(result), code


@app.route('/api/client/<name>/clear_stats', methods=['POST'])
def client_clear_stats(name):
    result, code = proxy_to_client(name, '/api/clear_stats', 'POST', {})
    return jsonify(result), code


@app.route('/api/clear_stats', methods=['POST'])
def clear_server_stats():
    """Reset all server-side stats by creating signal files for each collector."""
    signals = ['/tmp/stats_reset_http', '/tmp/stats_reset_echo', '/tmp/stats_reset_collector']
    for sig in signals:
        try:
            open(sig, 'w').close()
        except Exception:
            pass
    return jsonify({"ok": True, "message": "Server stats cleared"})


FTP_DATA_DIR = '/data'


def _safe_ftp_path(filename):
    """Resolve a safe file path within FTP_DATA_DIR, preventing path traversal."""
    name = secure_filename(filename)
    if not name:
        return None
    resolved = os.path.realpath(os.path.join(FTP_DATA_DIR, name))
    if not resolved.startswith(os.path.realpath(FTP_DATA_DIR)):
        return None
    return resolved


@app.route('/api/files')
def list_files():
    files = []
    try:
        for name in sorted(os.listdir(FTP_DATA_DIR)):
            path = os.path.join(FTP_DATA_DIR, name)
            if os.path.isfile(path):
                files.append({"name": name, "size": os.path.getsize(path)})
    except FileNotFoundError:
        pass
    return jsonify({"files": files})


@app.route('/api/files/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({"error": "No filename"}), 400
    path = _safe_ftp_path(f.filename)
    if not path:
        return jsonify({"error": "Invalid filename"}), 400
    f.save(path)
    os.chmod(path, 0o644)
    return jsonify({"ok": True, "filename": os.path.basename(path), "size": os.path.getsize(path)})


@app.route('/api/files/<name>', methods=['DELETE'])
def delete_file(name):
    path = _safe_ftp_path(name)
    if not path or not os.path.isfile(path):
        return jsonify({"error": "File not found"}), 404
    os.remove(path)
    return jsonify({"ok": True, "message": f"Deleted {os.path.basename(path)}"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082)
