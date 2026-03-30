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
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f0f2f5; color: #1a1a2e; min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #1a1a2e, #2d2d44);
            padding: 16px 24px; border-bottom: 2px solid #FA582D;
            display: flex; align-items: center; justify-content: space-between;
        }
        .header h1 { font-size: 20px; font-weight: 600; color: #FA582D; }
        .header .status { font-size: 12px; color: #ccc; }

        /* Tabs */
        .tab-bar {
            background: #ffffff; border-bottom: 1px solid #e0e0e0;
            display: flex; align-items: center; padding: 0 16px; gap: 0;
            overflow-x: auto; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }
        .tab {
            padding: 10px 20px; cursor: pointer; font-size: 13px; font-weight: 500;
            color: #666; border-bottom: 2px solid transparent;
            white-space: nowrap; transition: all 0.2s;
        }
        .tab:hover { color: #1a1a2e; background: #f5f5f5; }
        .tab.active { color: #FA582D; border-bottom-color: #FA582D; }
        .tab.server-tab { color: #00C4B3; }
        .tab.server-tab.active { color: #00C4B3; border-bottom-color: #00C4B3; }
        .tab-add {
            padding: 6px 14px; cursor: pointer; font-size: 16px; font-weight: 700;
            color: #00C4B3; border: 1px solid #00C4B3; border-radius: 4px;
            background: transparent; margin-left: 8px;
        }
        .tab-add:hover { background: #00C4B3; color: #fff; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        .container {
            max-width: 1400px; margin: 0 auto; padding: 20px;
            display: flex; flex-direction: column; gap: 20px;
        }
        .card {
            background: #ffffff; border: 1px solid #e0e0e0;
            border-radius: 8px; overflow: hidden;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        }
        .card-header {
            padding: 12px 16px; background: #f7f8fa;
            font-weight: 600; font-size: 14px; color: #1a1a2e;
            display: flex; align-items: center; justify-content: space-between;
            border-bottom: 1px solid #e0e0e0;
        }
        .card-body { padding: 16px; }

        /* Stats */
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
        .stat-box {
            background: #f7f8fa; border: 1px solid #e0e0e0;
            border-radius: 6px; padding: 10px; text-align: center;
        }
        .stat-label { font-size: 11px; color: #666; margin-bottom: 4px; }
        .stat-value { font-size: 16px; font-weight: 700; color: #FA582D; }
        .stat-value.client-val { color: #00C4B3; }

        /* Services grid */
        .services-grid {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px;
        }
        .service-card {
            background: #f7f8fa; border: 1px solid #e0e0e0;
            border-radius: 6px; padding: 12px;
        }
        .service-header {
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 8px;
        }
        .service-name { font-weight: 600; font-size: 14px; color: #FA582D; text-transform: uppercase; }
        .service-badge { font-size: 11px; padding: 2px 8px; border-radius: 10px; }
        .service-badge.active { background: #d4f5e9; color: #0d7a4f; }
        .service-badge.idle { background: #e8e8e8; color: #888; }
        .service-stat {
            display: flex; justify-content: space-between;
            font-size: 12px; padding: 3px 0; border-bottom: 1px solid #eee;
        }
        .service-stat-label { color: #888; }
        .service-stat-value { color: #1a1a2e; font-weight: 500; }

        /* Connections table */
        .connections-table { width: 100%; border-collapse: collapse; font-size: 12px; }
        .connections-table th {
            text-align: left; padding: 6px 8px; background: #f7f8fa;
            color: #666; font-weight: 500; border-bottom: 1px solid #e0e0e0;
        }
        .connections-table td {
            padding: 5px 8px; border-bottom: 1px solid #eee; color: #1a1a2e;
        }
        .connections-table tr:hover td { background: #f0f2f5; }

        /* Protocol cards (client tabs) */
        .protocol-grid {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px;
        }
        .proto-card {
            background: #f7f8fa; border: 1px solid #e0e0e0;
            border-radius: 6px; padding: 12px;
        }
        .proto-card.running { border-color: #00C4B3; border-width: 2px; }
        .proto-header {
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 10px;
        }
        .proto-select { display: flex; align-items: center; gap: 8px; }
        .proto-checkbox { width: 16px; height: 16px; accent-color: #FA582D; cursor: pointer; }
        .proto-name { font-weight: 600; font-size: 14px; text-transform: uppercase; color: #1a1a2e; }
        .proto-badge { font-size: 11px; padding: 2px 8px; border-radius: 10px; background: #e8e8e8; color: #888; }
        .proto-badge.running { background: #d4f5e9; color: #0d7a4f; }
        .proto-badge.countdown { background: #fff3e0; color: #e65100; font-variant-numeric: tabular-nums; }
        .proto-fields { display: flex; flex-direction: column; gap: 6px; margin-bottom: 10px; }
        .field-row { display: flex; align-items: center; gap: 8px; }
        .field-row label { font-size: 12px; color: #666; min-width: 90px; }
        .field-row input, .field-row select {
            flex: 1; padding: 4px 8px; background: #ffffff;
            border: 1px solid #d0d0d0; border-radius: 4px;
            color: #1a1a2e; font-size: 12px;
        }
        .field-row input[type="checkbox"] { flex: none; width: 16px; height: 16px; accent-color: #FA582D; }
        .proto-actions { display: flex; gap: 6px; }
        .bulk-actions { display: flex; gap: 6px; }

        /* Shaping */
        .shaping-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
        .slider-group { display: flex; flex-direction: column; gap: 4px; }
        .slider-group label {
            font-size: 12px; color: #666;
            display: flex; justify-content: space-between;
        }
        .slider-group input[type="range"] { width: 100%; accent-color: #FA582D; }
        .slider-value { color: #FA582D; font-weight: 600; }
        .shaping-actions { display: flex; gap: 8px; justify-content: flex-end; padding-top: 12px; }

        /* Buttons */
        .btn {
            padding: 6px 14px; border: none; border-radius: 4px;
            cursor: pointer; font-size: 12px; font-weight: 500;
        }
        .btn-start { background: #00C4B3; color: #fff; }
        .btn-start:hover { background: #00a89a; }
        .btn-stop { background: #ef4444; color: #fff; }
        .btn-stop:hover { background: #dc2626; }
        .btn-primary { background: #FA582D; color: #fff; }
        .btn-primary:hover { background: #e04a20; }
        .btn-secondary { background: #e0e0e0; color: #1a1a2e; }
        .btn-secondary:hover { background: #d0d0d0; }
        .btn-danger { background: #ef4444; color: #fff; }

        /* Log panel */
        .log-panel {
            background: #1a1a2e; border: 1px solid #e0e0e0; border-radius: 4px;
            padding: 8px; font-family: 'Monaco', 'Menlo', monospace;
            font-size: 11px; max-height: 300px; overflow-y: auto; line-height: 1.6;
        }
        .log-entry { color: #b0b8c8; white-space: pre-wrap; word-break: break-all; }
        .log-entry.error { color: #ef4444; }

        /* Modal */
        .modal-overlay {
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.4); z-index: 100; align-items: center; justify-content: center;
        }
        .modal-overlay.show { display: flex; }
        .modal {
            background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px;
            padding: 24px; width: 400px; max-width: 90vw;
            box-shadow: 0 8px 32px rgba(0,0,0,0.15);
        }
        .modal h3 { margin-bottom: 16px; color: #FA582D; }
        .modal-field { margin-bottom: 12px; }
        .modal-field label { display: block; font-size: 12px; color: #666; margin-bottom: 4px; }
        .modal-field input {
            width: 100%; padding: 8px; background: #f7f8fa; border: 1px solid #d0d0d0;
            border-radius: 4px; color: #1a1a2e; font-size: 13px;
        }
        .modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }

        @media (max-width: 900px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .shaping-grid { grid-template-columns: 1fr 1fr; }
        }
    </style>
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
    <div class="card">
        <div class="card-header">Services</div>
        <div class="card-body"><div class="services-grid" id="services-grid"></div></div>
    </div>
    <div class="card">
        <div class="card-header">Active Connections</div>
        <div class="card-body">
            <table class="connections-table">
                <thead><tr><th>Protocol</th><th>Local Port</th><th>Remote Address</th><th>State</th></tr></thead>
                <tbody id="conn-table-body">
                    <tr><td colspan="4" style="text-align:center;color:#94a3b8">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    <div class="card">
        <div class="card-header">
            <span>FTP Files</span>
            <label class="btn btn-start" style="cursor:pointer;margin:0">
                Upload File <input type="file" id="ftp-upload-input" style="display:none" onchange="uploadFtpFile()">
            </label>
        </div>
        <div class="card-body">
            <div id="upload-status" style="display:none;padding:8px;margin-bottom:8px;border-radius:4px;background:#065f46;color:#6ee7b7"></div>
            <table class="connections-table">
                <thead><tr><th>Filename</th><th>Size</th><th>Action</th></tr></thead>
                <tbody id="ftp-files-body">
                    <tr><td colspan="3" style="text-align:center;color:#94a3b8">Loading...</td></tr>
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
// ─── Protocol Definitions ────────────────────────────────────
const DSCP_OPTIONS = ['BE','CS1','AF11','AF12','AF13','CS2','AF21','AF22','AF23','CS3','AF31','AF32','AF33','CS4','AF41','AF42','AF43','CS5','VA','EF','CS6','CS7'];

const PROTOCOLS = {
    http: { name: 'HTTP', fields: [
        { key: 'url', label: 'URL', type: 'text', default: 'http://server/generate/100' },
        { key: 'method', label: 'Method', type: 'select', options: ['GET','POST'], default: 'GET' },
        { key: 'data_size_kb', label: 'Data KB', type: 'number', default: 0 },
        { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
        { key: 'upload', label: 'Upload Mode', type: 'checkbox', default: false },
        { key: 'random_size', label: 'Random Size', type: 'checkbox', default: false },
        { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
        { key: 'rate_pps', label: 'Rate (pps)', type: 'number', default: 0, step: 1 },
        { key: 'burst_enabled', label: 'Burst Mode', type: 'checkbox', default: false },
        { key: 'burst_count', label: 'Burst Size', type: 'number', default: 5 },
        { key: 'burst_pause', label: 'Burst Pause (s)', type: 'number', default: 2, step: 0.5 },
        { key: 'flows', label: 'Flows', type: 'number', default: 1 },
        { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
    ]},
    https: { name: 'HTTPS', fields: [
        { key: 'url', label: 'URL', type: 'text', default: 'https://server/' },
        { key: 'method', label: 'Method', type: 'select', options: ['GET','POST'], default: 'GET' },
        { key: 'data_size_kb', label: 'Data KB', type: 'number', default: 0 },
        { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
        { key: 'ignore_ssl', label: 'Ignore SSL', type: 'checkbox', default: true },
        { key: 'upload', label: 'Upload Mode', type: 'checkbox', default: false },
        { key: 'random_size', label: 'Random Size', type: 'checkbox', default: false },
        { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
        { key: 'rate_pps', label: 'Rate (pps)', type: 'number', default: 0, step: 1 },
        { key: 'burst_enabled', label: 'Burst Mode', type: 'checkbox', default: false },
        { key: 'burst_count', label: 'Burst Size', type: 'number', default: 5 },
        { key: 'burst_pause', label: 'Burst Pause (s)', type: 'number', default: 2, step: 0.5 },
        { key: 'flows', label: 'Flows', type: 'number', default: 1 },
        { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
    ]},
    http2: { name: 'HTTP/2', fields: [
        { key: 'url', label: 'URL', type: 'text', default: 'https://server/' },
        { key: 'method', label: 'Method', type: 'select', options: ['GET','POST'], default: 'GET' },
        { key: 'data_size_kb', label: 'Data KB', type: 'number', default: 0 },
        { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
        { key: 'ignore_ssl', label: 'Ignore SSL', type: 'checkbox', default: true },
        { key: 'upload', label: 'Upload Mode', type: 'checkbox', default: false },
        { key: 'random_size', label: 'Random Size', type: 'checkbox', default: false },
        { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
        { key: 'rate_pps', label: 'Rate (pps)', type: 'number', default: 0, step: 1 },
        { key: 'burst_enabled', label: 'Burst Mode', type: 'checkbox', default: false },
        { key: 'burst_count', label: 'Burst Size', type: 'number', default: 5 },
        { key: 'burst_pause', label: 'Burst Pause (s)', type: 'number', default: 2, step: 0.5 },
        { key: 'flows', label: 'Flows', type: 'number', default: 1 },
        { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
    ]},
    tcp: { name: 'TCP', fields: [
        { key: 'host', label: 'Host', type: 'text', default: 'server' },
        { key: 'port', label: 'Port', type: 'number', default: 9999 },
        { key: 'msg_size', label: 'Msg Size (B)', type: 'number', default: 1024 },
        { key: 'interval', label: 'Interval (s)', type: 'number', default: 0.5, step: 0.1 },
        { key: 'use_iperf', label: 'Use iperf3', type: 'checkbox', default: false },
        { key: 'bandwidth', label: 'iperf BW', type: 'text', default: '100M' },
        { key: 'random_size', label: 'Random Size', type: 'checkbox', default: false },
        { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
        { key: 'rate_pps', label: 'Rate (pps)', type: 'number', default: 0, step: 1 },
        { key: 'burst_enabled', label: 'Burst Mode', type: 'checkbox', default: false },
        { key: 'burst_count', label: 'Burst Size', type: 'number', default: 5 },
        { key: 'burst_pause', label: 'Burst Pause (s)', type: 'number', default: 2, step: 0.5 },
        { key: 'flows', label: 'Flows', type: 'number', default: 1 },
        { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
    ]},
    udp: { name: 'UDP', fields: [
        { key: 'host', label: 'Host', type: 'text', default: 'server' },
        { key: 'port', label: 'Port', type: 'number', default: 9998 },
        { key: 'msg_size', label: 'Msg Size (B)', type: 'number', default: 1024 },
        { key: 'interval', label: 'Interval (s)', type: 'number', default: 0.5, step: 0.1 },
        { key: 'use_iperf', label: 'Use iperf3', type: 'checkbox', default: false },
        { key: 'bandwidth', label: 'iperf BW', type: 'text', default: '100M' },
        { key: 'random_size', label: 'Random Size', type: 'checkbox', default: false },
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
        { key: 'filename', label: 'Filename', type: 'select', options: ['testfile_100mb.bin','testfile_1gb.bin'], default: 'testfile_1gb.bin' },
        { key: 'random_size', label: 'Random File', type: 'checkbox', default: false },
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
        { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
        { key: 'rate_pps', label: 'Rate (pps)', type: 'number', default: 0, step: 1 },
        { key: 'burst_enabled', label: 'Burst Mode', type: 'checkbox', default: false },
        { key: 'burst_count', label: 'Burst Size', type: 'number', default: 5 },
        { key: 'burst_pause', label: 'Burst Pause (s)', type: 'number', default: 2, step: 0.5 },
        { key: 'flows', label: 'Flows', type: 'number', default: 1 },
        { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
    ]},
    icmp: { name: 'ICMP (Ping)', fields: [
        { key: 'host', label: 'Host', type: 'text', default: 'server' },
        { key: 'packet_size', label: 'Pkt Size', type: 'number', default: 64 },
        { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.5 },
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

// ─── Helpers ──────────────────────────────────────────────────
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

    // Fetch the client's SERVER_HOST so defaults point to the right server
    let serverHost = 'server';
    try {
        const resp = await fetch('/api/client/' + name + '/server_host');
        const data = await resp.json();
        if (data.server_host) serverHost = data.server_host;
    } catch(e) {}

    const div = document.createElement('div');
    div.className = 'tab-content';
    div.id = 'tab-' + name;

    let protoCardsHtml = '';
    for (const [proto, def] of Object.entries(PROTOCOLS)) {
        let fieldsHtml = '';
        for (const f of def.fields) {
            if (f.key === 'flows') continue; // rendered in proto-actions
            let input;
            const id = 'c-' + name + '-' + proto + '-' + f.key;
            // Replace 'server' in defaults with client's actual server host
            let defVal = f.default;
            if (typeof defVal === 'string') defVal = defVal.replace(/server/g, serverHost);
            if (f.type === 'select') {
                const opts = f.options.map(o =>
                    '<option value="' + o + '"' + (o === f.default ? ' selected' : '') + '>' + o + '</option>').join('');
                input = '<select id="' + id + '">' + opts + '</select>';
            } else if (f.type === 'textarea') {
                input = '<textarea id="' + id + '" rows="3" style="width:100%;padding:6px 8px;font-size:12px;border:1px solid #d0d0d0;border-radius:4px;resize:vertical;font-family:inherit">' + defVal + '</textarea>';
            } else if (f.type === 'checkbox') {
                input = '<input type="checkbox" id="' + id + '"' + (f.default ? ' checked' : '') + '>';
            } else {
                const step = f.step ? ' step="' + f.step + '"' : '';
                input = '<input type="' + f.type + '" id="' + id + '" value="' + defVal + '"' + step + '>';
            }
            fieldsHtml += '<div class="field-row"><label>' + f.label + '</label>' + input + '</div>';
        }
        protoCardsHtml += '<div class="proto-card" id="c-' + name + '-proto-' + proto + '">' +
            '<div class="proto-header"><span class="proto-select">' +
            '<input type="checkbox" id="c-' + name + '-select-' + proto + '" class="proto-checkbox">' +
            '<span class="proto-name">' + def.name + '</span></span>' +
            '<span><span class="proto-badge" id="c-' + name + '-status-' + proto + '">Stopped</span>' +
            '<span class="proto-badge countdown" id="c-' + name + '-timer-' + proto + '" style="display:none"></span>' +
            '</span></div>' +
            '<div class="proto-fields">' + fieldsHtml + '</div>' +
            '<div class="proto-actions">' +
            '<button class="btn btn-start" onclick="clientStartProto(\'' + name + '\',\'' + proto + '\')">Start</button>' +
            '<button class="btn btn-stop" onclick="clientStopProto(\'' + name + '\',\'' + proto + '\')">Stop</button>' +
            '<label style="font-size:11px;color:#666;display:flex;align-items:center;gap:4px;margin-left:8px">' +
            'Flows <input type="number" id="c-' + name + '-' + proto + '-flows" value="1" min="1" max="20" style="width:45px;padding:2px 4px;font-size:11px">' +
            '</label>' +
            '</div></div>';
    }

    div.innerHTML = '<div class="container">' +
        // Client header with remove button
        '<div class="card"><div class="card-header">' +
        '<span>Client: ' + name + ' (' + clientList[name] + ')</span>' +
        '<button class="btn btn-danger" onclick="removeClient(\'' + name + '\')">Remove Client</button>' +
        '</div></div>' +
        // Stats
        '<div class="card"><div class="card-header">Live Statistics</div><div class="card-body">' +
        '<div class="stats-grid">' +
        '<div class="stat-box"><div class="stat-label">Bytes Sent</div><div class="stat-value client-val" id="c-' + name + '-sent">0 B</div></div>' +
        '<div class="stat-box"><div class="stat-label">Bytes Received</div><div class="stat-value client-val" id="c-' + name + '-recv">0 B</div></div>' +
        '<div class="stat-box"><div class="stat-label">Requests</div><div class="stat-value client-val" id="c-' + name + '-reqs">0</div></div>' +
        '<div class="stat-box"><div class="stat-label">Errors</div><div class="stat-value client-val" id="c-' + name + '-errors">0</div></div>' +
        '</div></div></div>' +
        // Shaping
        '<div class="card"><div class="card-header">Network Impairment (tc/netem)</div><div class="card-body">' +
        '<div class="shaping-grid">' +
        '<div class="slider-group"><label>Latency <span class="slider-value" id="c-' + name + '-latency-val">0</span> ms</label>' +
        '<input type="range" id="c-' + name + '-latency" min="0" max="500" value="0" oninput="clientUpdateSlider(\'' + name + '\',\'latency\')"></div>' +
        '<div class="slider-group"><label>Jitter <span class="slider-value" id="c-' + name + '-jitter-val">0</span> ms</label>' +
        '<input type="range" id="c-' + name + '-jitter" min="0" max="200" value="0" oninput="clientUpdateSlider(\'' + name + '\',\'jitter\')"></div>' +
        '<div class="slider-group"><label>Packet Loss <span class="slider-value" id="c-' + name + '-loss-val">0</span> %</label>' +
        '<input type="range" id="c-' + name + '-loss" min="0" max="50" value="0" step="0.5" oninput="clientUpdateSlider(\'' + name + '\',\'loss\')"></div>' +
        '<div class="slider-group"><label>Bandwidth <span class="slider-value" id="c-' + name + '-bandwidth-val">0</span> Mbps (0=unlimited)</label>' +
        '<input type="range" id="c-' + name + '-bandwidth" min="0" max="1000" step="10" value="0" oninput="clientUpdateSlider(\'' + name + '\',\'bandwidth\')"></div>' +
        '</div>' +
        '<div style="margin-top:12px;padding:10px;background:#f0f2f5;border-radius:8px">' +
        '<label style="display:flex;align-items:center;gap:8px">' +
        '<input type="checkbox" id="c-' + name + '-random-bw" onchange="clientToggleRandomBw(\'' + name + '\')">' +
        '<strong>Random Bandwidth</strong> (20 Mbps – 1 Gbps, cycles every 10s)' +
        '<span id="c-' + name + '-random-bw-status" style="color:#888;margin-left:8px"></span>' +
        '</label></div>' +
        '<div style="margin-top:8px;padding:10px;background:#f0f2f5;border-radius:8px">' +
        '<label style="display:flex;align-items:center;gap:8px;margin-bottom:8px">' +
        '<input type="checkbox" id="c-' + name + '-source-ip-toggle" onchange="clientToggleSourceIp(\'' + name + '\')">' +
        '<strong>Random Source IPs</strong> (simulate multiple clients)</label>' +
        '<div id="c-' + name + '-source-ip-config" style="display:none;margin-top:8px">' +
        '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' +
        '<label style="font-size:12px">Base IP</label>' +
        '<input type="text" id="c-' + name + '-source-ip-base" value="172.18.0.100" style="width:140px;padding:4px 8px;background:#ffffff;color:#1a1a2e;border:1px solid #d0d0d0;border-radius:4px">' +
        '<label style="font-size:12px">Count</label>' +
        '<input type="number" id="c-' + name + '-source-ip-count" value="5" min="1" max="50" style="width:60px;padding:4px 8px;background:#ffffff;color:#1a1a2e;border:1px solid #d0d0d0;border-radius:4px">' +
        '<button class="btn btn-primary" onclick="clientApplySourceIps(\'' + name + '\')" style="padding:4px 12px">Apply</button>' +
        '</div><div id="c-' + name + '-source-ip-list" style="margin-top:8px;font-size:11px;color:#94a3b8"></div></div></div>' +
        '<div class="shaping-actions">' +
        '<button class="btn btn-primary" onclick="clientApplyShaping(\'' + name + '\')">Apply Shaping</button>' +
        '<button class="btn btn-secondary" onclick="clientClearShaping(\'' + name + '\')">Clear All</button>' +
        '</div></div></div>' +
        // Protocol cards
        '<div class="card"><div class="card-header"><span>Traffic Generators</span>' +
        '<div class="bulk-actions">' +
        '<button class="btn btn-secondary" onclick="clientSelectAll(\'' + name + '\')">Select All</button>' +
        '<button class="btn btn-secondary" onclick="clientDeselectAll(\'' + name + '\')">Deselect All</button>' +
        '<button class="btn btn-start" onclick="clientStartSelected(\'' + name + '\')">Start Selected</button>' +
        '<button class="btn btn-stop" onclick="clientStopSelected(\'' + name + '\')">Stop Selected</button>' +
        '<button class="btn btn-danger" onclick="clientStopAll(\'' + name + '\')">Stop All</button>' +
        '</div></div><div class="card-body"><div class="protocol-grid">' + protoCardsHtml + '</div></div></div>' +
        // Log
        '<div class="card"><div class="card-header">Activity Log ' +
        '<div style="display:flex;align-items:center;gap:8px">' +
        '<label style="display:flex;align-items:center;gap:4px;font-size:12px;font-weight:normal;cursor:pointer">' +
        '<input type="checkbox" id="auto-refresh-' + name + '" checked onchange="toggleAutoRefresh()"> Auto-refresh</label>' +
        '<button class="btn btn-secondary" onclick="clientLogs[\'' + name + '\']=[];document.getElementById(\'log-' + name + '\').innerHTML=\'\'">Clear</button>' +
        '</div></div><div class="card-body"><div class="log-panel" id="log-' + name + '"></div></div></div>' +
        '</div>';

    document.body.appendChild(div);
}

// ─── Client Actions ──────────────────────────────────────────
function clientGetConfig(clientName, proto) {
    const cfg = {};
    for (const f of PROTOCOLS[proto].fields) {
        if (f.key === 'flows') continue;
        const el = document.getElementById('c-' + clientName + '-' + proto + '-' + f.key);
        if (!el) continue;
        if (f.type === 'checkbox') cfg[f.key] = el.checked;
        else if (f.type === 'number') cfg[f.key] = parseFloat(el.value);
        else cfg[f.key] = el.value;
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

function clientUpdateSlider(clientName, id) {
    const el = document.getElementById('c-' + clientName + '-' + id);
    const val = document.getElementById('c-' + clientName + '-' + id + '-val');
    if (el && val) val.textContent = el.value;
}

async function clientApplyShaping(clientName) {
    const body = {
        latency_ms: parseInt(document.getElementById('c-' + clientName + '-latency').value),
        jitter_ms: parseInt(document.getElementById('c-' + clientName + '-jitter').value),
        packet_loss_pct: parseFloat(document.getElementById('c-' + clientName + '-loss').value),
        bandwidth_mbps: parseInt(document.getElementById('c-' + clientName + '-bandwidth').value),
    };
    const res = await apiPost('/api/client/' + clientName + '/shaping', body);
    addClientLog(clientName, '[SHAPING] ' + (res.message || ''));
}

async function clientClearShaping(clientName) {
    await apiPost('/api/client/' + clientName + '/shaping/clear', {});
    ['latency','jitter','loss','bandwidth'].forEach(id => {
        const el = document.getElementById('c-' + clientName + '-' + id);
        if (el) { el.value = 0; clientUpdateSlider(clientName, id); }
    });
    addClientLog(clientName, '[SHAPING] Cleared');
}

async function clientLoadShaping(clientName) {
    try {
        const resp = await fetch('/api/client/' + clientName + '/shaping/current');
        const data = await resp.json();
        if (data.latency_ms !== undefined) {
            document.getElementById('c-' + clientName + '-latency').value = data.latency_ms;
            document.getElementById('c-' + clientName + '-jitter').value = data.jitter_ms;
            document.getElementById('c-' + clientName + '-loss').value = data.packet_loss_pct;
            document.getElementById('c-' + clientName + '-bandwidth').value = data.bandwidth_mbps;
            ['latency','jitter','loss','bandwidth'].forEach(id => clientUpdateSlider(clientName, id));
        }
        if (data.random_bandwidth) {
            const el = document.getElementById('c-' + clientName + '-random-bw');
            if (el) el.checked = true;
            const st = document.getElementById('c-' + clientName + '-random-bw-status');
            if (st) st.textContent = 'Active';
        }
    } catch(e) {}
}

async function clientToggleRandomBw(clientName) {
    const enabled = document.getElementById('c-' + clientName + '-random-bw').checked;
    const res = await apiPost('/api/client/' + clientName + '/shaping/random_bandwidth',
        { enabled, min_mbps: 20, max_mbps: 1000, interval: 10 });
    addClientLog(clientName, '[SHAPING] ' + (res.message || ''));
    const st = document.getElementById('c-' + clientName + '-random-bw-status');
    if (st) st.textContent = enabled ? 'Active' : '';
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
        // Collect logs from all protocols
        let allLogs = [];
        for (const [proto, info] of Object.entries(data.jobs || {})) {
            if (info.logs) {
                for (const line of info.logs) {
                    allLogs.push('[' + proto.toUpperCase() + '] ' + line);
                }
            }
        }
        // Update activity log panel with remote logs
        const panel = document.getElementById('log-' + clientName);
        if (panel && allLogs.length > 0) {
            const last50 = allLogs.slice(-50);
            panel.innerHTML = last50.map(l => {
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
        clientLoadShaping(name); clientLoadSourceIps(name);
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
            clientLoadShaping(name); clientLoadSourceIps(name);
        }
        rebuildTabs();
    } catch(e) {}
}

// ─── Init ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadClients();
    loadFtpFiles();
    pollInterval = setInterval(pollAll, 2000);
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
        80: 'HTTP', 443: 'HTTPS', 5201: 'iperf3',
        9999: 'TCP Echo', 9998: 'UDP Echo',
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
            if port_num in ports:
                connections.append({
                    'proto': ports[port_num],
                    'local_port': port_num,
                    'remote': remote,
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

    tcp_echo = echo.get('tcp', {})
    udp_echo = echo.get('udp', {})

    total_recv = (http.get('bytes_recv', 0) + tcp_echo.get('bytes_recv', 0) +
                  udp_echo.get('bytes_recv', 0) + ftp.get('bytes_recv', 0))
    total_sent = (http.get('bytes_sent', 0) + tcp_echo.get('bytes_sent', 0) +
                  udp_echo.get('bytes_sent', 0) + ftp.get('bytes_sent', 0))
    total_reqs = (http.get('requests', 0) + tcp_echo.get('connections', 0) +
                  udp_echo.get('packets', 0) + ftp.get('downloads', 0) +
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
            'active_connections': max(conn_counts.get(9998, 0), 1 if (time.time() - udp_echo.get('last_active', 0)) < 10 else 0),
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


@app.route('/api/client/<name>/shaping', methods=['POST'])
def client_shaping(name):
    result, code = proxy_to_client(name, '/api/shaping', 'POST', request.json or {})
    return jsonify(result), code


@app.route('/api/client/<name>/shaping/clear', methods=['POST'])
def client_shaping_clear(name):
    result, code = proxy_to_client(name, '/api/shaping/clear', 'POST', {})
    return jsonify(result), code


@app.route('/api/client/<name>/shaping/current')
def client_shaping_current(name):
    result, code = proxy_to_client(name, '/api/shaping/current')
    return jsonify(result), code


@app.route('/api/client/<name>/server_host')
def client_server_host(name):
    result, code = proxy_to_client(name, '/api/server_host')
    return jsonify(result), code


@app.route('/api/client/<name>/shaping/random_bandwidth', methods=['POST'])
def client_random_bandwidth(name):
    result, code = proxy_to_client(name, '/api/shaping/random_bandwidth', 'POST', request.json or {})
    return jsonify(result), code


@app.route('/api/client/<name>/source_ips', methods=['GET', 'POST'])
def client_source_ips(name):
    if request.method == 'POST':
        result, code = proxy_to_client(name, '/api/source_ips', 'POST', request.json or {})
    else:
        result, code = proxy_to_client(name, '/api/source_ips')
    return jsonify(result), code


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
