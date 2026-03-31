const SRV = (typeof SERVER_HOST !== 'undefined') ? SERVER_HOST : 'server';

const DSCP_OPTIONS = ['BE','CS1','AF11','AF12','AF13','CS2','AF21','AF22','AF23','CS3','AF31','AF32','AF33','CS4','AF41','AF42','AF43','CS5','VA','EF','CS6','CS7'];

const PROTOCOLS = {
    https: {
        name: 'HTTPS',
        fields: [
            { key: 'url', label: 'URL', type: 'text', get default() { return `https://${SRV}/`; } },
            { key: 'method', label: 'Method', type: 'select', options: ['GET', 'POST'], default: 'GET' },
            { key: 'data_size_kb', label: 'Data KB', type: 'number', default: 0 },
            { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
            { key: 'http2', label: 'HTTP/2', type: 'checkbox', default: false },
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
        ]
    },
    iperf_tcp: {
        name: 'iperf3 TCP',
        fields: [
            { key: 'host', label: 'Host', type: 'text', get default() { return SRV; } },
            { key: 'port', label: 'Port', type: 'number', default: 5201 },
            { key: 'bandwidth', label: 'Bandwidth', type: 'text', default: '100M' },
            { key: 'parallel', label: 'Parallel Streams', type: 'number', default: 1 },
            { key: 'reverse', label: 'Reverse (download)', type: 'checkbox', default: false },
            { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
            { key: 'flows', label: 'Flows', type: 'number', default: 1 },
            { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
        ]
    },
    iperf_udp: {
        name: 'iperf3 UDP',
        fields: [
            { key: 'host', label: 'Host', type: 'text', get default() { return SRV; } },
            { key: 'port', label: 'Port', type: 'number', default: 5201 },
            { key: 'bandwidth', label: 'Bandwidth', type: 'text', default: '100M' },
            { key: 'parallel', label: 'Parallel Streams', type: 'number', default: 1 },
            { key: 'reverse', label: 'Reverse (download)', type: 'checkbox', default: false },
            { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
            { key: 'flows', label: 'Flows', type: 'number', default: 1 },
            { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
        ]
    },
    hping3: {
        name: 'hping3',
        fields: [
            { key: 'host', label: 'Host', type: 'text', get default() { return SRV; } },
            { key: 'mode', label: 'Mode', type: 'select', options: ['ICMP', 'TCP SYN', 'TCP ACK', 'TCP FIN', 'UDP', 'Traceroute'], default: 'ICMP' },
            { key: 'port', label: 'Dest Port', type: 'number', default: 0 },
            { key: 'packet_size', label: 'Data Size (B)', type: 'number', default: 64 },
            { key: 'count', label: 'Count (0=cont)', type: 'number', default: 0 },
            { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
            { key: 'flood', label: 'Flood Mode', type: 'checkbox', default: false },
            { key: 'ttl', label: 'TTL', type: 'number', default: 64 },
            { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
            { key: 'flows', label: 'Flows', type: 'number', default: 1 },
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
            { key: 'random_size', label: 'Random Size', type: 'checkbox', default: false },
            { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
            { key: 'rate_pps', label: 'Rate (pps)', type: 'number', default: 0, step: 1 },
            { key: 'burst_enabled', label: 'Burst Mode', type: 'checkbox', default: false },
            { key: 'burst_count', label: 'Burst Size', type: 'number', default: 5 },
            { key: 'burst_pause', label: 'Burst Pause (s)', type: 'number', default: 2, step: 0.5 },
            { key: 'flows', label: 'Flows', type: 'number', default: 1 },
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
            { key: 'random_size', label: 'Random Size', type: 'checkbox', default: false },
            { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
            { key: 'rate_pps', label: 'Rate (pps)', type: 'number', default: 0, step: 1 },
            { key: 'burst_enabled', label: 'Burst Mode', type: 'checkbox', default: false },
            { key: 'burst_count', label: 'Burst Size', type: 'number', default: 5 },
            { key: 'burst_pause', label: 'Burst Pause (s)', type: 'number', default: 2, step: 0.5 },
            { key: 'flows', label: 'Flows', type: 'number', default: 1 },
            { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
        ]
    },
    ftp: {
        name: 'FTP',
        fields: [
            { key: 'host', label: 'Host', type: 'text', get default() { return SRV; } },
            { key: 'port', label: 'Port', type: 'number', default: 21 },
            { key: 'username', label: 'Username', type: 'text', default: 'anonymous' },
            { key: 'password', label: 'Password', type: 'password', default: '' },
            { key: 'filename', label: 'Filename', type: 'select', options: ['testfile_100mb.bin', 'testfile_1gb.bin'], default: 'testfile_1gb.bin' },
            { key: 'random_size', label: 'Random File', type: 'checkbox', default: false },
            { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
            { key: 'rate_pps', label: 'Rate (pps)', type: 'number', default: 0, step: 1 },
            { key: 'burst_enabled', label: 'Burst Mode', type: 'checkbox', default: false },
            { key: 'burst_count', label: 'Burst Size', type: 'number', default: 5 },
            { key: 'burst_pause', label: 'Burst Pause (s)', type: 'number', default: 2, step: 0.5 },
            { key: 'flows', label: 'Flows', type: 'number', default: 1 },
            { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
        ]
    },
    ssh: {
        name: 'SSH',
        fields: [
            { key: 'host', label: 'Host', type: 'text', get default() { return SRV; } },
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
        ]
    },
    ext_https: {
        name: 'External HTTPS',
        fields: [
            { key: 'urls', label: 'Target URLs (one per line)', type: 'textarea', default: 'https://www.google.com' },
            { key: 'method', label: 'Method', type: 'select', options: ['GET', 'POST', 'HEAD'], default: 'GET' },
            { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
            { key: 'ignore_ssl', label: 'Ignore SSL', type: 'checkbox', default: false },
            { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
            { key: 'rate_pps', label: 'Rate (pps)', type: 'number', default: 0, step: 1 },
            { key: 'burst_enabled', label: 'Burst Mode', type: 'checkbox', default: false },
            { key: 'burst_count', label: 'Burst Size', type: 'number', default: 5 },
            { key: 'burst_pause', label: 'Burst Pause (s)', type: 'number', default: 2, step: 0.5 },
            { key: 'flows', label: 'Flows', type: 'number', default: 1 },
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
            if (f.key === 'flows') continue; // rendered separately
            let input;
            if (f.type === 'select') {
                const opts = f.options.map(o =>
                    `<option value="${o}" ${o === f.default ? 'selected' : ''}>${o}</option>`).join('');
                input = `<select id="cfg-${proto}-${f.key}">${opts}</select>`;
            } else if (f.type === 'textarea') {
                input = `<textarea id="cfg-${proto}-${f.key}" rows="3" style="width:100%;padding:6px 8px;font-size:12px;border:1px solid #d0d0d0;border-radius:4px;resize:vertical;font-family:inherit">${f.default}</textarea>`;
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
                    <label style="font-size:11px;color:#666;display:flex;align-items:center;gap:4px;margin-left:8px">
                        Flows <input type="number" id="cfg-${proto}-flows" value="1" min="1" max="20" style="width:45px;padding:2px 4px;font-size:11px">
                    </label>
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
        if (f.key === 'flows') continue; // handled separately
        const el = document.getElementById(`cfg-${proto}-${f.key}`);
        if (f.type === 'checkbox') cfg[f.key] = el.checked;
        else if (f.type === 'number') cfg[f.key] = parseFloat(el.value);
        else cfg[f.key] = el.value;
    }
    return cfg;
}

function getFlowCount(proto) {
    const el = document.getElementById(`cfg-${proto}-flows`);
    return el ? Math.max(1, Math.min(20, parseInt(el.value) || 1)) : 1;
}

async function startProto(proto) {
    const config = getConfig(proto);
    const flows = getFlowCount(proto);
    if (flows === 1) {
        const res = await apiPost('/api/start', { protocol: proto, config });
        addLog(`[${proto.toUpperCase()}] ${res.message}`);
    } else {
        for (let i = 1; i <= flows; i++) {
            const cfg = {...config, flow_id: String(i)};
            const res = await apiPost('/api/start', { protocol: proto, config: cfg });
            addLog(`[${proto.toUpperCase()}] ${res.message}`);
        }
    }
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
        await startProto(proto);
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

        // Aggregate stats per base protocol (http_1, http_2 → http)
        const protoAgg = {};
        for (const [jobKey, info] of Object.entries(data.jobs)) {
            const baseParts = jobKey.split('_');
            // Determine base protocol: "ext_https_2" → "ext_https", "http_2" → "http", "http" → "http"
            let base;
            if (baseParts.length >= 3 && !isNaN(baseParts[baseParts.length - 1])) {
                base = baseParts.slice(0, -1).join('_');
            } else if (baseParts.length === 2 && !isNaN(baseParts[1])) {
                base = baseParts[0];
            } else {
                base = jobKey;
            }

            if (!protoAgg[base]) protoAgg[base] = { running: false, flows: 0, remaining: -1, elapsed: 0, stats: {bytes_sent:0,bytes_recv:0,requests:0,errors:0} };
            const agg = protoAgg[base];
            if (info.running) { agg.running = true; agg.flows++; }
            agg.stats.bytes_sent += info.stats.bytes_sent;
            agg.stats.bytes_recv += info.stats.bytes_recv;
            agg.stats.requests += info.stats.requests;
            agg.stats.errors += info.stats.errors;
            if (info.remaining >= 0) agg.remaining = Math.max(agg.remaining, info.remaining);
            agg.elapsed = Math.max(agg.elapsed, info.elapsed);

            totSent += info.stats.bytes_sent;
            totRecv += info.stats.bytes_recv;
            totReqs += info.stats.requests;
            totErrs += info.stats.errors;
        }

        for (const [proto, agg] of Object.entries(protoAgg)) {
            const card = document.getElementById(`proto-${proto}`);
            const badge = document.getElementById(`status-${proto}`);
            const timer = document.getElementById(`timer-${proto}`);
            if (!card) continue;

            if (agg.running) {
                card.classList.add('running');
                badge.classList.add('running');
                badge.textContent = agg.flows > 1 ? `${agg.flows} Flows` : 'Running';
                if (agg.remaining >= 0) {
                    timer.style.display = '';
                    timer.textContent = fmtTime(agg.remaining);
                } else {
                    timer.style.display = '';
                    timer.textContent = fmtTime(agg.elapsed);
                }
            } else {
                card.classList.remove('running');
                badge.classList.remove('running');
                badge.textContent = 'Stopped';
                timer.style.display = 'none';
            }
        }

        // Reset cards with no jobs
        for (const proto of Object.keys(PROTOCOLS)) {
            if (!protoAgg[proto]) {
                const card = document.getElementById(`proto-${proto}`);
                const badge = document.getElementById(`status-${proto}`);
                const timer = document.getElementById(`timer-${proto}`);
                if (card) card.classList.remove('running');
                if (badge) { badge.classList.remove('running'); badge.textContent = 'Stopped'; }
                if (timer) timer.style.display = 'none';
            }
        }

        document.getElementById('stat-sent').textContent = fmtBytes(totSent);
        document.getElementById('stat-recv').textContent = fmtBytes(totRecv);
        document.getElementById('stat-reqs').textContent = totReqs.toLocaleString();
        document.getElementById('stat-errors').textContent = totErrs.toLocaleString();
    } catch (e) { /* ignore */ }
}

// ─── Logs ──────────────────────────────────────────────────

const logBuf = [];
let autoRefreshInterval = null;

function addLog(msg) {
    logBuf.push(`[${new Date().toLocaleTimeString()}] ${msg}`);
    if (logBuf.length > 1000) logBuf.splice(0, 500);
    const panel = document.getElementById('log-panel');
    panel.innerHTML = logBuf.map(l => {
        const cls = l.toLowerCase().includes('error') ? ' error' : '';
        const d = document.createElement('div');
        d.textContent = l;
        return `<div class="log-entry${cls}">${d.innerHTML}</div>`;
    }).join('');
    panel.scrollTop = panel.scrollHeight;
}

function toggleAutoRefresh() {
    const enabled = document.getElementById('auto-refresh-toggle').checked;
    if (enabled) {
        if (!autoRefreshInterval) {
            autoRefreshInterval = setInterval(pollStatus, 2000);
            pollStatus();
        }
    } else {
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
    }
    addLog(enabled ? 'Auto-refresh enabled' : 'Auto-refresh paused');
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
    autoRefreshInterval = setInterval(pollStatus, 2000);
    setInterval(loadFtpFileList, 10000);
    pollStatus();
    addLog('Dashboard ready.');
});
