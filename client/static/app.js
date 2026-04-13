const SRV = (typeof SERVER_HOST !== 'undefined') ? SERVER_HOST : 'server';

const DSCP_OPTIONS = ['BE','CS1','AF11','AF12','AF13','CS2','AF21','AF22','AF23','CS3','AF31','AF32','AF33','CS4','AF41','AF42','AF43','CS5','VA','EF','CS6','CS7'];

const PROTOCOLS = {
    https: {
        name: 'HTTPS',
        appId: 'ssl, web-browsing',
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
    iperf: {
        name: 'iperf3',
        appId: 'iperf',
        fields: [
            { key: 'host', label: 'Host', type: 'text', get default() { return SRV; } },
            { key: 'port', label: 'Port', type: 'number', default: 5201 },
            { key: 'protocol', label: 'Protocol', type: 'select', options: ['TCP', 'UDP'], default: 'TCP' },
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
        appId: 'ping, ip-protocol-custom',
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
    http_plain: {
        name: 'HTTP (Plain)',
        appId: 'web-browsing',
        fields: [
            { key: 'host', label: 'Host', type: 'text', get default() { return SRV; } },
            { key: 'port', label: 'Port', type: 'number', default: 9999 },
            { key: 'method', label: 'Method', type: 'select', options: ['GET', 'POST'], default: 'GET' },
            { key: 'data_size_kb', label: 'Data Size (KB)', type: 'number', default: 1 },
            { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
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
    dns: {
        name: 'DNS',
        appId: 'dns',
        fields: [
            { key: 'host', label: 'Host', type: 'text', get default() { return SRV; } },
            { key: 'port', label: 'Port', type: 'number', default: 53 },
            { key: 'domains', label: 'Domains (one per line)', type: 'textarea', default: 'google.com\namazon.com\nmicrosoft.com\ngithub.com\ncloudflare.com' },
            { key: 'interval', label: 'Interval (s)', type: 'number', default: 1, step: 0.1 },
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
        appId: 'ftp',
        maxFlows: 1,
        fields: [
            { key: 'host', label: 'Host', type: 'text', get default() { return SRV; } },
            { key: 'port', label: 'Port', type: 'number', default: 21 },
            { key: 'username', label: 'Username', type: 'text', default: 'anonymous' },
            { key: 'password', label: 'Password', type: 'password', default: '' },
            { key: 'filename', label: 'Filename', type: 'select', options: ['testfile_100mb.bin'], default: 'testfile_100mb.bin' },
            { key: 'random_size', label: 'Random File', type: 'checkbox', default: false },
            { key: 'dscp', label: 'DSCP', type: 'select', options: DSCP_OPTIONS, default: 'BE' },
            { key: 'duration', label: 'Duration (s)', type: 'number', default: 900 },
        ]
    },
    ssh: {
        name: 'SSH',
        appId: 'ssh',
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
        appId: 'ssl, web-browsing',
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

        const appIdHtml = def.appId ? `<div class="proto-appid">App-ID: ${def.appId}</div>` : '';

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
                ${appIdHtml}
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
    const maxFlows = PROTOCOLS[proto].maxFlows || 20;
    const flows = Math.min(getFlowCount(proto), maxFlows);
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

// ─── Router Link Simulation ─────────────────────────────────

const ROUTER_PRESETS = {
    degraded_wan: { latency_ms: 300, jitter_ms: 50, packet_loss_pct: 5, bandwidth_mbps: 0 },
    voice_sla: { latency_ms: 200, jitter_ms: 40, packet_loss_pct: 2, bandwidth_mbps: 0 },
    video_sla: { latency_ms: 150, jitter_ms: 30, packet_loss_pct: 3, bandwidth_mbps: 0 },
};

async function addRouter() {
    const name = document.getElementById('router-add-name').value.trim();
    const ip = document.getElementById('router-add-ip').value.trim();
    const username = document.getElementById('router-add-user').value.trim();
    const password = document.getElementById('router-add-pass').value;
    const errEl = document.getElementById('router-add-error');
    if (!name || !ip || !username) {
        errEl.textContent = 'Name, IP, and username are required';
        errEl.style.display = 'block';
        return;
    }
    errEl.style.display = 'none';
    const res = await apiPost('/api/routers', { name, ip, username, password });
    if (res.ok) {
        document.getElementById('router-add-name').value = '';
        document.getElementById('router-add-ip').value = '';
        document.getElementById('router-add-user').value = '';
        document.getElementById('router-add-pass').value = '';
        addLog(`[ROUTER] ${res.message}`);
        loadRouters();
    } else {
        errEl.textContent = res.error || 'Failed to add router';
        errEl.style.display = 'block';
        addLog(`[ROUTER] Error: ${res.error}`);
    }
}

async function removeRouter(id) {
    if (!confirm('Remove this router?')) return;
    const res = await fetch('/api/routers/' + id, { method: 'DELETE' });
    const data = await res.json();
    addLog(`[ROUTER] ${data.message}`);
    loadRouters();
}

async function reconnectRouter(id) {
    const res = await apiPost('/api/routers/' + id + '/connect', {});
    addLog(`[ROUTER] ${res.message}`);
    loadRouters();
}

async function refreshInterfaces(id) {
    const resp = await fetch('/api/routers/' + id + '/interfaces');
    const data = await resp.json();
    addLog(`[ROUTER] Refreshed interfaces`);
    loadRouters();
}

async function selectInterface(id, iface) {
    const res = await apiPost('/api/routers/' + id + '/select-interface', { interface: iface });
    if (!res.ok) addLog(`[ROUTER] ${res.error || res.message}`);
}

function applyRouterPreset(id, presetName) {
    const p = ROUTER_PRESETS[presetName];
    if (!p) return;
    const el = (field) => document.getElementById('rtr-' + id + '-' + field);
    if (el('latency')) el('latency').value = p.latency_ms;
    if (el('jitter')) el('jitter').value = p.jitter_ms;
    if (el('loss')) el('loss').value = p.packet_loss_pct;
    if (el('bw')) el('bw').value = p.bandwidth_mbps;
}

async function applyRouterMode(id, mode) {
    const body = { mode };
    if (mode === 'impaired') {
        const el = (field) => document.getElementById('rtr-' + id + '-' + field);
        body.latency_ms = parseInt(el('latency')?.value) || 0;
        body.jitter_ms = parseInt(el('jitter')?.value) || 0;
        body.packet_loss_pct = parseFloat(el('loss')?.value) || 0;
        body.bandwidth_mbps = parseInt(el('bw')?.value) || 0;
    }
    const res = await apiPost('/api/routers/' + id + '/mode', body);
    addLog(`[ROUTER] ${res.message || res.error}`);
    loadRouters();
}

function renderRouterCard(r) {
    const id = r.router_id;
    const connColor = r.connected ? '#27ae60' : '#e74c3c';
    const connText = r.connected ? 'Connected' : 'Disconnected';

    let ifaceRows = '';
    if (r.interfaces && r.interfaces.length) {
        for (const iface of r.interfaces) {
            const checked = iface.name === r.selected_interface ? 'checked' : '';
            const stateColor = iface.state === 'up' ? '#27ae60' : '#e74c3c';
            const ipStr = iface.ip_address ? iface.ip_address + (iface.subnet || '') : '--';
            const descStr = iface.description ? ' — ' + iface.description : '';
            ifaceRows += `<label style="display:flex;align-items:center;gap:8px;padding:4px 0;font-size:12px;cursor:pointer">
                <input type="radio" name="rtr-${id}-iface" value="${iface.name}" ${checked}
                    onchange="selectInterface('${id}','${iface.name}')">
                <strong>${iface.name}</strong>
                <span style="color:#666">${ipStr}${descStr}</span>
                <span style="color:${stateColor};font-weight:600;font-size:11px">${iface.state.toUpperCase()}</span>
            </label>`;
        }
    } else {
        ifaceRows = '<div style="color:#888;font-size:12px">No interfaces discovered</div>';
    }

    // Mode indicator
    let modeHtml = '';
    if (r.current_mode === 'healthy') {
        modeHtml = `<div style="padding:8px 12px;background:#eafaf1;border:2px solid #27ae60;border-radius:8px;font-size:13px;margin-bottom:12px">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#27ae60;margin-right:6px"></span>
            <strong style="color:#1e8449">HEALTHY</strong> — ${r.selected_interface || '?'} up, no impairment</div>`;
    } else if (r.current_mode === 'impaired') {
        const cfg = r.impairment_config || {};
        const parts = [];
        if (cfg.latency_ms) parts.push('Latency: ' + cfg.latency_ms + 'ms');
        if (cfg.jitter_ms) parts.push('Jitter: ' + cfg.jitter_ms + 'ms');
        if (cfg.packet_loss_pct) parts.push('Loss: ' + cfg.packet_loss_pct + '%');
        if (cfg.bandwidth_mbps) parts.push('BW: ' + cfg.bandwidth_mbps + ' Mbps');
        modeHtml = `<div style="padding:8px 12px;background:#fdecea;border:2px solid #e74c3c;border-radius:8px;font-size:13px;margin-bottom:12px">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#e74c3c;margin-right:6px"></span>
            <strong style="color:#c0392b">IMPAIRED</strong> — ${r.selected_interface || '?'} | ${parts.join(' | ') || 'custom'}</div>`;
    } else if (r.current_mode === 'link_down') {
        modeHtml = `<div style="padding:8px 12px;background:#1a1a2e;border:2px solid #ef4444;border-radius:8px;font-size:13px;margin-bottom:12px;color:#fff">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#ef4444;margin-right:6px"></span>
            <strong>LINK DOWN</strong> — ${r.selected_interface || '?'} is shut down</div>`;
    }

    return `<div style="background:#f7f8fa;border:1px solid #e0e0e0;border-radius:8px;padding:14px;margin-bottom:12px">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
            <div style="display:flex;align-items:center;gap:10px">
                <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${connColor}"></span>
                <strong style="font-size:14px">${r.name}</strong>
                <span style="color:#666;font-size:12px">${r.ip}</span>
                <span style="color:${connColor};font-size:11px;font-weight:600">${connText}</span>
            </div>
            <div style="display:flex;gap:6px">
                ${!r.connected ? '<button class="btn btn-start" onclick="reconnectRouter(\'' + id + '\')" style="padding:3px 10px;font-size:11px">Reconnect</button>' : ''}
                <button class="btn btn-danger" onclick="removeRouter('${id}')" style="padding:3px 10px;font-size:11px">Remove</button>
            </div>
        </div>
        ${r.connected ? `
        <!-- Interfaces -->
        <div style="margin-bottom:12px">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">
                <label style="font-size:12px;font-weight:600">Interfaces</label>
                <button class="btn btn-secondary" onclick="refreshInterfaces('${id}')" style="padding:2px 10px;font-size:11px">Refresh</button>
            </div>
            <div style="padding:6px 10px;background:#fff;border:1px solid #e0e0e0;border-radius:6px">
                ${ifaceRows}
            </div>
        </div>
        <!-- Presets -->
        <div style="margin-bottom:10px">
            <label style="font-size:12px;font-weight:600;margin-bottom:4px;display:block">Presets</label>
            <div style="display:flex;flex-wrap:wrap;gap:6px">
                <button class="btn btn-secondary" onclick="applyRouterPreset('${id}','degraded_wan')" style="padding:3px 10px;font-size:11px">Degraded WAN</button>
                <button class="btn btn-secondary" onclick="applyRouterPreset('${id}','voice_sla')" style="padding:3px 10px;font-size:11px">Voice SLA</button>
                <button class="btn btn-secondary" onclick="applyRouterPreset('${id}','video_sla')" style="padding:3px 10px;font-size:11px">Video SLA</button>
            </div>
        </div>
        <!-- Impairment Values -->
        <div style="margin-bottom:12px">
            <label style="font-size:12px;font-weight:600;margin-bottom:4px;display:block">Impairment Values</label>
            <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center">
                <label style="font-size:12px">Latency</label>
                <input type="number" id="rtr-${id}-latency" value="${(r.impairment_config||{}).latency_ms||0}" min="0" max="5000" style="width:70px;padding:4px 8px;font-size:12px;border:1px solid #d0d0d0;border-radius:4px"><span style="font-size:12px">ms</span>
                <label style="font-size:12px;margin-left:6px">Jitter</label>
                <input type="number" id="rtr-${id}-jitter" value="${(r.impairment_config||{}).jitter_ms||0}" min="0" max="2000" style="width:70px;padding:4px 8px;font-size:12px;border:1px solid #d0d0d0;border-radius:4px"><span style="font-size:12px">ms</span>
                <label style="font-size:12px;margin-left:6px">Loss</label>
                <input type="number" id="rtr-${id}-loss" value="${(r.impairment_config||{}).packet_loss_pct||0}" min="0" max="100" step="0.5" style="width:70px;padding:4px 8px;font-size:12px;border:1px solid #d0d0d0;border-radius:4px"><span style="font-size:12px">%</span>
                <label style="font-size:12px;margin-left:6px">BW</label>
                <input type="number" id="rtr-${id}-bw" value="${(r.impairment_config||{}).bandwidth_mbps||0}" min="0" max="10000" step="10" style="width:80px;padding:4px 8px;font-size:12px;border:1px solid #d0d0d0;border-radius:4px"><span style="font-size:12px">Mbps</span>
            </div>
        </div>
        ${modeHtml}
        <!-- Mode Buttons -->
        <div style="display:flex;gap:8px">
            <button class="btn btn-start" onclick="applyRouterMode('${id}','healthy')" style="padding:6px 16px">Healthy</button>
            <button class="btn btn-primary" onclick="applyRouterMode('${id}','impaired')" style="padding:6px 16px">Apply Impaired</button>
            <button class="btn btn-danger" onclick="applyRouterMode('${id}','link_down')" style="padding:6px 16px">Link Down</button>
        </div>
        ` : '<div style="color:#888;font-size:12px;padding:8px 0">Router disconnected. Click Reconnect to restore.</div>'}
    </div>`;
}

async function loadRouters() {
    try {
        const resp = await fetch('/api/routers');
        const routers = await resp.json();
        const container = document.getElementById('router-cards-container');
        if (!container) return;
        if (!routers.length) {
            container.innerHTML = '<div style="color:#888;font-size:13px;text-align:center;padding:16px">No routers added. Add a router above to start link simulation.</div>';
            return;
        }
        container.innerHTML = routers.map(r => renderRouterCard(r)).join('');
    } catch(e) {}
}

async function pollRouterStatus() {
    try {
        const resp = await fetch('/api/routers');
        const routers = await resp.json();
        const container = document.getElementById('router-cards-container');
        if (!container) return;
        if (!routers.length) {
            container.innerHTML = '<div style="color:#888;font-size:13px;text-align:center;padding:16px">No routers added. Add a router above to start link simulation.</div>';
            return;
        }
        // Preserve impairment input values during re-render
        const savedValues = {};
        for (const r of routers) {
            const id = r.router_id;
            for (const f of ['latency','jitter','loss','bw']) {
                const el = document.getElementById('rtr-' + id + '-' + f);
                if (el) savedValues[id + '-' + f] = el.value;
            }
        }
        container.innerHTML = routers.map(r => renderRouterCard(r)).join('');
        // Restore saved input values
        for (const [key, val] of Object.entries(savedValues)) {
            const el = document.getElementById('rtr-' + key);
            if (el) el.value = val;
        }
        // Merge router logs into activity log
        for (const r of routers) {
            if (r.logs) {
                for (const line of r.logs) {
                    const key = 'rtr:' + r.router_id + ':' + line;
                    if (!_seenEngineLogs.has(key)) {
                        _seenEngineLogs.add(key);
                        logBuf.push('[ROUTER:' + r.name + '] ' + line);
                    }
                }
            }
        }
        renderLogPanel();
    } catch(e) {}
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

        // Merge engine logs into the unified log buffer
        for (const [proto, info] of Object.entries(data.jobs)) {
            if (info.logs) {
                for (const line of info.logs) {
                    const key = proto + ':' + line;
                    if (!_seenEngineLogs.has(key)) {
                        _seenEngineLogs.add(key);
                        logBuf.push('[' + proto.toUpperCase() + '] ' + line);
                    }
                }
            }
        }
        // Cap dedup set to prevent memory growth
        if (_seenEngineLogs.size > 5000) {
            const arr = Array.from(_seenEngineLogs);
            _seenEngineLogs = new Set(arr.slice(arr.length - 2000));
        }
        renderLogPanel();
    } catch (e) { /* ignore */ }
}

// ─── Logs ──────────────────────────────────────────────────

const logBuf = [];
let autoRefreshInterval = null;
let _seenEngineLogs = new Set();

function renderLogPanel() {
    if (logBuf.length > 1000) logBuf.splice(0, logBuf.length - 500);
    const panel = document.getElementById('log-panel');
    const last150 = logBuf.slice(-150);
    panel.innerHTML = last150.map(l => {
        const cls = l.toLowerCase().includes('error') ? ' error' : '';
        const d = document.createElement('div');
        d.textContent = l;
        return `<div class="log-entry${cls}">${d.innerHTML}</div>`;
    }).join('');
    panel.scrollTop = panel.scrollHeight;
}

function addLog(msg) {
    logBuf.push(`[${new Date().toLocaleTimeString()}] ${msg}`);
    renderLogPanel();
}

function toggleAutoRefresh() {
    const enabled = document.getElementById('auto-refresh-toggle').checked;
    if (enabled) {
        if (!autoRefreshInterval) {
            autoRefreshInterval = setInterval(() => { pollStatus(); pollRouterStatus(); }, 2000);
            pollStatus();
            pollRouterStatus();
        }
    } else {
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
    }
    addLog(enabled ? 'Auto-refresh enabled' : 'Auto-refresh paused');
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


// ─── FTP File List ──────────────────────────────────────────

async function loadFtpFileList() {
    try {
        const resp = await fetch('http://' + SRV + ':5000/api/files');
        const data = await resp.json();
        const sel = document.getElementById('cfg-ftp-filename');
        if (!sel || !data.files) return;
        const current = sel.value;
        const defaultFile = 'testfile_100mb.bin';
        sel.innerHTML = data.files.map(f => {
            const isSelected = current ? f.name === current : f.name === defaultFile;
            return '<option value="' + f.name + '"' + (isSelected ? ' selected' : '') + '>' +
                f.name + ' (' + fmtBytes(f.size) + ')</option>';
        }).join('');
    } catch(e) { /* server may not be reachable */ }
}

// ─── Init ──────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    renderProtocolCards();
    loadRouters();
    loadSourceIps();
    loadFtpFileList();
    document.getElementById('source-ip-toggle').addEventListener('change', toggleSourceIpConfig);
    autoRefreshInterval = setInterval(() => { pollStatus(); pollRouterStatus(); }, 2000);
    setInterval(loadFtpFileList, 10000);
    pollStatus();
    addLog('Dashboard ready.');
});
