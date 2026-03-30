const SRV = (typeof SERVER_HOST !== 'undefined') ? SERVER_HOST : 'server';

const PROTOCOLS = {
    http: {
        name: 'HTTP',
        fields: [
            { key: 'url', label: 'URL', type: 'text', get default() { return `http://${SRV}/generate/100`; } },
            { key: 'method', label: 'Method', type: 'select', options: ['GET', 'POST'], default: 'GET' },
            { key: 'data_size_kb', label: 'Data KB', type: 'number', default: 0 },
            { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
            { key: 'upload', label: 'Upload Mode', type: 'checkbox', default: false },
            { key: 'random_size', label: 'Random Size', type: 'checkbox', default: false },
            { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
        ]
    },
    https: {
        name: 'HTTPS',
        fields: [
            { key: 'url', label: 'URL', type: 'text', get default() { return `https://${SRV}/`; } },
            { key: 'method', label: 'Method', type: 'select', options: ['GET', 'POST'], default: 'GET' },
            { key: 'data_size_kb', label: 'Data KB', type: 'number', default: 0 },
            { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
            { key: 'ignore_ssl', label: 'Ignore SSL', type: 'checkbox', default: true },
            { key: 'upload', label: 'Upload Mode', type: 'checkbox', default: false },
            { key: 'random_size', label: 'Random Size', type: 'checkbox', default: false },
            { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
        ]
    },
    http2: {
        name: 'HTTP/2',
        fields: [
            { key: 'url', label: 'URL', type: 'text', get default() { return `https://${SRV}/`; } },
            { key: 'method', label: 'Method', type: 'select', options: ['GET', 'POST'], default: 'GET' },
            { key: 'data_size_kb', label: 'Data KB', type: 'number', default: 0 },
            { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
            { key: 'ignore_ssl', label: 'Ignore SSL', type: 'checkbox', default: true },
            { key: 'upload', label: 'Upload Mode', type: 'checkbox', default: false },
            { key: 'random_size', label: 'Random Size', type: 'checkbox', default: false },
            { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
        ]
    },
    tcp: {
        name: 'TCP',
        fields: [
            { key: 'host', label: 'Host', type: 'text', get default() { return SRV; } },
            { key: 'port', label: 'Port', type: 'number', default: 9999 },
            { key: 'msg_size', label: 'Msg Size (B)', type: 'number', default: 1024 },
            { key: 'interval', label: 'Interval (s)', type: 'number', default: 0.5, step: 0.1 },
            { key: 'use_iperf', label: 'Use iperf3', type: 'checkbox', default: false },
            { key: 'bandwidth', label: 'iperf BW', type: 'text', default: '100M' },
            { key: 'random_size', label: 'Random Size', type: 'checkbox', default: false },
            { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
        ]
    },
    udp: {
        name: 'UDP',
        fields: [
            { key: 'host', label: 'Host', type: 'text', get default() { return SRV; } },
            { key: 'port', label: 'Port', type: 'number', default: 9998 },
            { key: 'msg_size', label: 'Msg Size (B)', type: 'number', default: 1024 },
            { key: 'interval', label: 'Interval (s)', type: 'number', default: 0.5, step: 0.1 },
            { key: 'use_iperf', label: 'Use iperf3', type: 'checkbox', default: false },
            { key: 'bandwidth', label: 'iperf BW', type: 'text', default: '100M' },
            { key: 'random_size', label: 'Random Size', type: 'checkbox', default: false },
            { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
        ]
    },
    ftp: {
        name: 'FTP',
        fields: [
            { key: 'host', label: 'Host', type: 'text', get default() { return SRV; } },
            { key: 'port', label: 'Port', type: 'number', default: 21 },
            { key: 'username', label: 'Username', type: 'text', default: 'anonymous' },
            { key: 'password', label: 'Password', type: 'text', default: '' },
            { key: 'filename', label: 'Filename', type: 'select', options: ['testfile_100mb.bin', 'testfile_1gb.bin'], default: 'testfile_1gb.bin' },
            { key: 'random_size', label: 'Random File', type: 'checkbox', default: false },
            { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
        ]
    },
    ssh: {
        name: 'SSH',
        fields: [
            { key: 'host', label: 'Host', type: 'text', get default() { return SRV; } },
            { key: 'port', label: 'Port', type: 'number', default: 22 },
            { key: 'username', label: 'Username', type: 'text', default: 'testuser' },
            { key: 'password', label: 'Password', type: 'text', default: 'testpass' },
            { key: 'command', label: 'Command', type: 'text', default: 'uptime' },
            { key: 'interval', label: 'Interval (s)', type: 'number', default: 5 },
            { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
        ]
    },
    ext_https: {
        name: 'External HTTPS',
        fields: [
            { key: 'url', label: 'Target URL', type: 'text', default: 'https://www.google.com' },
            { key: 'method', label: 'Method', type: 'select', options: ['GET', 'POST', 'HEAD'], default: 'GET' },
            { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
            { key: 'ignore_ssl', label: 'Ignore SSL', type: 'checkbox', default: false },
            { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
        ]
    },
    ext_tcp: {
        name: 'External TCP',
        fields: [
            { key: 'host', label: 'Target Host', type: 'text', default: '1.1.1.1' },
            { key: 'port', label: 'Target Port', type: 'number', default: 443 },
            { key: 'msg_size', label: 'Msg Size (B)', type: 'number', default: 1024 },
            { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
            { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
        ]
    },
    ext_udp: {
        name: 'External UDP',
        fields: [
            { key: 'host', label: 'Target Host', type: 'text', default: '1.1.1.1' },
            { key: 'port', label: 'Target Port', type: 'number', default: 53 },
            { key: 'msg_size', label: 'Msg Size (B)', type: 'number', default: 512 },
            { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
            { key: 'dns_mode', label: 'DNS Query Mode', type: 'checkbox', default: true },
            { key: 'dns_domain', label: 'DNS Domain', type: 'text', default: 'example.com' },
            { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
        ]
    },
    icmp: {
        name: 'ICMP (Ping)',
        fields: [
            { key: 'host', label: 'Host', type: 'text', get default() { return SRV; } },
            { key: 'packet_size', label: 'Pkt Size', type: 'number', default: 64 },
            { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.5 },
            { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
        ]
    },
};

// ─── Render ────────────────────────────────────────────────

function renderProtocolCards() {
    const grid = document.getElementById('protocol-grid');
    grid.innerHTML = '';

    for (const [proto, def] of Object.entries(PROTOCOLS)) {
        let fieldsHtml = '';
        for (const f of def.fields) {
            let input;
            if (f.type === 'select') {
                const opts = f.options.map(o =>
                    `<option value="${o}" ${o === f.default ? 'selected' : ''}>${o}</option>`).join('');
                input = `<select id="cfg-${proto}-${f.key}">${opts}</select>`;
            } else if (f.type === 'checkbox') {
                input = `<input type="checkbox" id="cfg-${proto}-${f.key}" ${f.default ? 'checked' : ''}>`;
            } else {
                const step = f.step ? `step="${f.step}"` : '';
                input = `<input type="${f.type}" id="cfg-${proto}-${f.key}" value="${f.default}" ${step}>`;
            }
            fieldsHtml += `<div class="field-row"><label>${f.label}</label>${input}</div>`;
        }

        grid.innerHTML += `
            <div class="proto-card" id="proto-${proto}">
                <div class="proto-header">
                    <span class="proto-select">
                        <input type="checkbox" id="select-${proto}" class="proto-checkbox">
                        <span class="proto-name">${def.name}</span>
                    </span>
                    <span>
                        <span class="proto-badge" id="status-${proto}">Stopped</span>
                        <span class="proto-badge countdown" id="timer-${proto}" style="display:none"></span>
                    </span>
                </div>
                <div class="proto-fields">${fieldsHtml}</div>
                <div class="proto-actions">
                    <button class="btn btn-start" onclick="startProto('${proto}')">Start</button>
                    <button class="btn btn-stop" onclick="stopProto('${proto}')">Stop</button>
                </div>
            </div>`;
    }
}

// ─── API ───────────────────────────────────────────────────

async function apiPost(url, body) {
    const r = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    return r.json();
}

function getConfig(proto) {
    const cfg = {};
    for (const f of PROTOCOLS[proto].fields) {
        const el = document.getElementById(`cfg-${proto}-${f.key}`);
        if (f.type === 'checkbox') cfg[f.key] = el.checked;
        else if (f.type === 'number') cfg[f.key] = parseFloat(el.value);
        else cfg[f.key] = el.value;
    }
    return cfg;
}

async function startProto(proto) {
    const config = getConfig(proto);
    const res = await apiPost('/api/start', { protocol: proto, config });
    addLog(`[${proto.toUpperCase()}] ${res.message}`);
}

async function stopProto(proto) {
    const res = await apiPost('/api/stop', { protocol: proto });
    addLog(`[${proto.toUpperCase()}] ${res.message}`);
}

async function stopAll() {
    await apiPost('/api/stop', { protocol: 'all' });
    addLog('[ALL] Stopping all traffic');
}

function getSelectedProtos() {
    return Object.keys(PROTOCOLS).filter(p =>
        document.getElementById(`select-${p}`).checked
    );
}

function selectAll() {
    Object.keys(PROTOCOLS).forEach(p =>
        document.getElementById(`select-${p}`).checked = true
    );
}

function deselectAll() {
    Object.keys(PROTOCOLS).forEach(p =>
        document.getElementById(`select-${p}`).checked = false
    );
}

async function startSelected() {
    const selected = getSelectedProtos();
    if (selected.length === 0) { addLog('[WARN] No protocols selected'); return; }
    for (const proto of selected) {
        const config = getConfig(proto);
        const res = await apiPost('/api/start', { protocol: proto, config });
        addLog(`[${proto.toUpperCase()}] ${res.message}`);
    }
}

async function stopSelected() {
    const selected = getSelectedProtos();
    if (selected.length === 0) { addLog('[WARN] No protocols selected'); return; }
    for (const proto of selected) {
        const res = await apiPost('/api/stop', { protocol: proto });
        addLog(`[${proto.toUpperCase()}] ${res.message}`);
    }
}

// ─── Shaping ───────────────────────────────────────────────

function updateSlider(id) {
    document.getElementById(id + '-val').textContent = document.getElementById(id).value;
}

async function applyShaping() {
    const body = {
        latency_ms: parseInt(document.getElementById('latency').value),
        jitter_ms: parseInt(document.getElementById('jitter').value),
        packet_loss_pct: parseFloat(document.getElementById('loss').value),
        bandwidth_mbps: parseInt(document.getElementById('bandwidth').value),
    };
    const res = await apiPost('/api/shaping', body);
    addLog(`[SHAPING] ${res.message}`);
}

async function clearShaping() {
    await apiPost('/api/shaping/clear', {});
    ['latency', 'jitter', 'loss', 'bandwidth'].forEach(id => {
        document.getElementById(id).value = 0;
        updateSlider(id);
    });
    addLog('[SHAPING] Cleared');
}

// ─── Status polling ────────────────────────────────────────

function fmtBytes(b) {
    if (b < 1024) return b + ' B';
    if (b < 1048576) return (b / 1024).toFixed(1) + ' KB';
    if (b < 1073741824) return (b / 1048576).toFixed(1) + ' MB';
    return (b / 1073741824).toFixed(2) + ' GB';
}

function fmtTime(s) {
    if (s < 0) return '--';
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
}

async function pollStatus() {
    try {
        const resp = await fetch('/api/status');
        const data = await resp.json();
        let totSent = 0, totRecv = 0, totReqs = 0, totErrs = 0;

        for (const [proto, info] of Object.entries(data.jobs)) {
            const card = document.getElementById(`proto-${proto}`);
            const badge = document.getElementById(`status-${proto}`);
            const timer = document.getElementById(`timer-${proto}`);
            if (!card) continue;

            if (info.running) {
                card.classList.add('running');
                badge.classList.add('running');
                badge.textContent = 'Running';
                if (info.remaining >= 0) {
                    timer.style.display = '';
                    timer.textContent = fmtTime(info.remaining);
                } else {
                    timer.style.display = '';
                    timer.textContent = fmtTime(info.elapsed);
                }
            } else {
                card.classList.remove('running');
                badge.classList.remove('running');
                badge.textContent = 'Stopped';
                timer.style.display = 'none';
            }

            totSent += info.stats.bytes_sent;
            totRecv += info.stats.bytes_recv;
            totReqs += info.stats.requests;
            totErrs += info.stats.errors;
        }

        document.getElementById('stat-sent').textContent = fmtBytes(totSent);
        document.getElementById('stat-recv').textContent = fmtBytes(totRecv);
        document.getElementById('stat-reqs').textContent = totReqs.toLocaleString();
        document.getElementById('stat-errors').textContent = totErrs.toLocaleString();
    } catch (e) { /* ignore */ }
}

// ─── Logs ──────────────────────────────────────────────────

const logBuf = [];

function addLog(msg) {
    logBuf.push(`[${new Date().toLocaleTimeString()}] ${msg}`);
    if (logBuf.length > 300) logBuf.splice(0, 150);
    const panel = document.getElementById('log-panel');
    panel.innerHTML = logBuf.map(l => {
        const cls = l.includes('rror') ? ' error' : '';
        const d = document.createElement('div');
        d.textContent = l;
        return `<div class="log-entry${cls}">${d.innerHTML}</div>`;
    }).join('');
    panel.scrollTop = panel.scrollHeight;
}

// ─── Random Bandwidth ───────────────────────────────────────

async function toggleRandomBandwidth() {
    const enabled = document.getElementById('random-bw-toggle').checked;
    const res = await apiPost('/api/shaping/random_bandwidth', {
        enabled, min_mbps: 20, max_mbps: 1000, interval: 10
    });
    addLog('[SHAPING] ' + res.message);
    updateRandomBwStatus(enabled);
}

function updateRandomBwStatus(running) {
    const el = document.getElementById('random-bw-status');
    if (el) el.textContent = running ? 'Active' : '';
    const toggle = document.getElementById('random-bw-toggle');
    if (toggle) toggle.checked = running;
}

// ─── Source IPs ─────────────────────────────────────────────

function toggleSourceIpConfig() {
    const enabled = document.getElementById('source-ip-toggle').checked;
    document.getElementById('source-ip-config').style.display = enabled ? 'block' : 'none';
    if (!enabled) {
        apiPost('/api/source_ips', { enabled: false });
        document.getElementById('source-ip-list').textContent = '';
        addLog('[SOURCE IP] Disabled');
    }
}

async function applySourceIps() {
    const base_ip = document.getElementById('source-ip-base').value.trim();
    const count = parseInt(document.getElementById('source-ip-count').value);
    const res = await apiPost('/api/source_ips', { enabled: true, base_ip, count });
    addLog('[SOURCE IP] ' + res.message);
    if (res.ips && res.ips.length) {
        document.getElementById('source-ip-list').textContent = 'Active: ' + res.ips.join(', ');
    }
}

async function loadSourceIps() {
    try {
        const resp = await fetch('/api/source_ips');
        const data = await resp.json();
        const toggle = document.getElementById('source-ip-toggle');
        if (toggle) toggle.checked = data.enabled;
        document.getElementById('source-ip-config').style.display = data.enabled ? 'block' : 'none';
        if (data.ips && data.ips.length) {
            document.getElementById('source-ip-list').textContent = 'Active: ' + data.ips.join(', ');
        }
    } catch(e) {}
}

// ─── Shaping restore ────────────────────────────────────────

async function loadShaping() {
    try {
        const resp = await fetch('/api/shaping/current');
        const data = await resp.json();
        document.getElementById('latency').value = data.latency_ms;
        document.getElementById('jitter').value = data.jitter_ms;
        document.getElementById('loss').value = data.packet_loss_pct;
        document.getElementById('bandwidth').value = data.bandwidth_mbps;
        ['latency', 'jitter', 'loss', 'bandwidth'].forEach(updateSlider);
        if (data.random_bandwidth) updateRandomBwStatus(true);
    } catch (e) { /* ignore */ }
}

// ─── FTP File List ──────────────────────────────────────────

async function loadFtpFileList() {
    try {
        const resp = await fetch('http://' + SRV + ':5000/api/files');
        const data = await resp.json();
        const sel = document.getElementById('cfg-ftp-filename');
        if (!sel || !data.files) return;
        const current = sel.value;
        sel.innerHTML = data.files.map(f =>
            '<option value="' + f.name + '"' + (f.name === current ? ' selected' : '') + '>' +
            f.name + ' (' + fmtBytes(f.size) + ')</option>').join('');
    } catch(e) { /* server may not be reachable */ }
}

// ─── Init ──────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    renderProtocolCards();
    loadShaping();
    loadSourceIps();
    loadFtpFileList();
    document.getElementById('random-bw-toggle').addEventListener('change', toggleRandomBandwidth);
    document.getElementById('source-ip-toggle').addEventListener('change', toggleSourceIpConfig);
    setInterval(pollStatus, 2000);
    setInterval(loadFtpFileList, 10000);
    pollStatus();
    addLog('Dashboard ready.');
});
