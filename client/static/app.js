const SRV = (typeof SERVER_HOST !== 'undefined') ? SERVER_HOST : 'server';

const DSCP_OPTIONS = ['BE','CS1','AF11','AF12','AF13','CS2','AF21','AF22','AF23','CS3','AF31','AF32','AF33','CS4','AF41','AF42','AF43','CS5','VA','EF','CS6','CS7'];
const ADVANCED_KEYS = ['dscp', 'rate_pps', 'burst_enabled', 'burst_count', 'burst_pause'];

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

// ─── Section Toggle ─────────────────────────────────────────

function toggleSection(name) {
    const body = document.getElementById('section-' + name);
    const chevron = document.getElementById('chevron-' + name);
    if (!body) return;
    body.classList.toggle('collapsed');
    if (chevron) chevron.classList.toggle('collapsed');
}

// ─── Protocol Card Toggle ───────────────────────────────────

function toggleProtoDetails(proto) {
    const el = document.getElementById('details-' + proto);
    if (el) el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

function toggleAdvanced(proto) {
    const el = document.getElementById('adv-' + proto);
    const toggle = document.getElementById('adv-toggle-' + proto);
    if (el) {
        const show = el.style.display === 'none';
        el.style.display = show ? 'block' : 'none';
        if (toggle) toggle.textContent = show ? 'Advanced Settings \u25BE' : 'Advanced Settings \u25B8';
    }
}

// ─── Render ────────────────────────────────────────────────

function renderProtocolCards() {
    const grid = document.getElementById('protocol-grid');
    grid.innerHTML = '';

    for (const [proto, def] of Object.entries(PROTOCOLS)) {
        // Basic fields
        let basicHtml = '';
        let advancedHtml = '';
        let hasAdvanced = false;

        for (const f of def.fields) {
            if (f.key === 'flows') continue;
            const isAdv = ADVANCED_KEYS.includes(f.key);
            let input;
            if (f.type === 'select') {
                const opts = f.options.map(o =>
                    `<option value="${o}" ${o === f.default ? 'selected' : ''}>${o}</option>`).join('');
                input = `<select id="cfg-${proto}-${f.key}">${opts}</select>`;
            } else if (f.type === 'textarea') {
                input = `<textarea id="cfg-${proto}-${f.key}" rows="3" style="width:100%;padding:6px 8px;font-size:11px;background:var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:4px;resize:vertical;font-family:inherit">${f.default}</textarea>`;
            } else if (f.type === 'checkbox') {
                input = `<input type="checkbox" id="cfg-${proto}-${f.key}" ${f.default ? 'checked' : ''}>`;
            } else {
                const step = f.step ? `step="${f.step}"` : '';
                input = `<input type="${f.type}" id="cfg-${proto}-${f.key}" value="${f.default}" ${step}>`;
            }
            const row = `<div class="field-row"><label>${f.label}</label>${input}</div>`;
            if (isAdv) { advancedHtml += row; hasAdvanced = true; }
            else basicHtml += row;
        }

        const appIdHtml = def.appId ? `<div class="proto-appid">App-ID: ${def.appId}</div>` : '';

        let advSection = '';
        if (hasAdvanced) {
            advSection = `<div class="advanced-toggle" id="adv-toggle-${proto}" onclick="event.stopPropagation();toggleAdvanced('${proto}')">Advanced Settings \u25B8</div>
                <div class="advanced-fields" id="adv-${proto}" style="display:none">${advancedHtml}</div>`;
        }

        grid.innerHTML += `
            <div class="proto-card" id="proto-${proto}">
                <div class="proto-header" onclick="toggleProtoDetails('${proto}')">
                    <span class="proto-select" onclick="event.stopPropagation()">
                        <input type="checkbox" id="select-${proto}" class="proto-checkbox">
                        <span class="proto-name">${def.name}</span>
                    </span>
                    <span class="proto-header-right">
                        <span class="proto-badge" id="status-${proto}">Stopped</span>
                        <span class="proto-badge countdown" id="timer-${proto}" style="display:none"></span>
                        <button class="btn btn-start" onclick="event.stopPropagation();startProto('${proto}')" style="padding:3px 10px;font-size:10px">Start</button>
                        <button class="btn btn-stop" onclick="event.stopPropagation();stopProto('${proto}')" style="padding:3px 10px;font-size:10px">Stop</button>
                    </span>
                </div>
                <div class="proto-details" id="details-${proto}" style="display:none">
                    ${appIdHtml}
                    <div class="proto-fields">${basicHtml}</div>
                    ${advSection}
                    <div class="proto-actions" style="margin-top:6px">
                        <label style="font-size:10px;color:var(--text-secondary);display:flex;align-items:center;gap:4px">
                            Flows <input type="number" id="cfg-${proto}-flows" value="1" min="1" max="20" style="width:42px;padding:2px 4px;font-size:10px;background:var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:3px">
                        </label>
                    </div>
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
        if (f.key === 'flows') continue;
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

async function clearStats() {
    await apiPost('/api/clear_stats', {});
    addLog('[STATS] Stats cleared');
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

function toggleRouterInterfaces(id) {
    const el = document.getElementById('rtr-ifaces-' + id);
    const toggle = document.getElementById('rtr-ifaces-toggle-' + id);
    if (el) {
        const show = el.style.display === 'none';
        el.style.display = show ? 'block' : 'none';
        if (toggle) toggle.textContent = show ? 'Hide Interfaces' : 'Show Interfaces';
    }
}

function renderRouterCard(r) {
    const id = r.router_id;
    const connColor = r.connected ? 'var(--success)' : 'var(--danger)';
    const connText = r.connected ? 'Connected' : 'Disconnected';

    let ifaceRows = '';
    let selectedIfaceDisplay = r.selected_interface || 'None';
    if (r.interfaces && r.interfaces.length) {
        for (const iface of r.interfaces) {
            const checked = iface.name === r.selected_interface ? 'checked' : '';
            const stateColor = iface.state === 'up' ? 'var(--success)' : 'var(--danger)';
            const ipStr = iface.ip_address ? iface.ip_address + (iface.subnet || '') : '--';
            const descStr = iface.description ? ` — ${iface.description}` : '';
            ifaceRows += `<label style="display:flex;align-items:center;gap:8px;padding:3px 0;font-size:11px;cursor:pointer;color:var(--text-primary)">
                <input type="radio" name="rtr-${id}-iface" value="${iface.name}" ${checked}
                    onchange="selectInterface('${id}','${iface.name}')">
                <strong>${iface.name}</strong>
                <span style="color:var(--text-secondary);font-style:italic">${descStr}</span>
                <span style="color:var(--text-secondary)">${ipStr}</span>
                <span style="color:${stateColor};font-weight:600;font-size:10px">${iface.state.toUpperCase()}</span>
            </label>`;
        }
    } else {
        ifaceRows = '<div style="color:var(--text-secondary);font-size:11px">No interfaces discovered</div>';
    }

    // Mode indicator
    let modeHtml = '';
    if (r.current_mode === 'healthy') {
        modeHtml = `<div style="padding:6px 10px;background:rgba(39,174,96,0.1);border:1px solid rgba(39,174,96,0.3);border-radius:6px;font-size:12px;margin-bottom:8px;color:var(--success)">
            <strong>HEALTHY</strong> — ${r.selected_interface || '?'} up, no impairment</div>`;
    } else if (r.current_mode === 'impaired') {
        const cfg = r.impairment_config || {};
        const parts = [];
        if (cfg.latency_ms) parts.push(cfg.latency_ms + 'ms latency');
        if (cfg.jitter_ms) parts.push(cfg.jitter_ms + 'ms jitter');
        if (cfg.packet_loss_pct) parts.push(cfg.packet_loss_pct + '% loss');
        if (cfg.bandwidth_mbps) parts.push(cfg.bandwidth_mbps + ' Mbps');
        modeHtml = `<div style="padding:6px 10px;background:rgba(231,76,60,0.1);border:1px solid rgba(231,76,60,0.3);border-radius:6px;font-size:12px;margin-bottom:8px;color:var(--danger)">
            <strong>IMPAIRED</strong> — ${r.selected_interface || '?'} | ${parts.join(', ') || 'custom'}</div>`;
    } else if (r.current_mode === 'link_down') {
        modeHtml = `<div style="padding:6px 10px;background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.4);border-radius:6px;font-size:12px;margin-bottom:8px;color:#ff6b6b">
            <strong>LINK DOWN</strong> — ${r.selected_interface || '?'} is shut down</div>`;
    }

    const inputStyle = 'width:60px;padding:3px 6px;font-size:11px;background:var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:3px';

    return `<div style="background:var(--bg-sub);border:1px solid var(--border);border-radius:6px;padding:10px;margin-bottom:8px">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
            <div style="display:flex;align-items:center;gap:8px">
                <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${connColor}"></span>
                <strong style="font-size:13px;color:var(--text-primary)">${r.name}</strong>
                <span style="color:var(--text-secondary);font-size:11px">${r.ip}</span>
                <span style="color:${connColor};font-size:10px;font-weight:600">${connText}</span>
            </div>
            <div style="display:flex;gap:4px">
                ${!r.connected ? '<button class="btn btn-start" onclick="reconnectRouter(\'' + id + '\')" style="padding:2px 8px;font-size:10px">Reconnect</button>' : ''}
                <button class="btn btn-danger" onclick="removeRouter('${id}')" style="padding:2px 8px;font-size:10px">Remove</button>
            </div>
        </div>
        ${r.connected ? `
        ${modeHtml}
        <!-- Interface toggle -->
        <div style="margin-bottom:8px">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                <span style="font-size:11px;color:var(--text-secondary)">Interface: <strong style="color:var(--text-primary)">${selectedIfaceDisplay}</strong></span>
                <button class="btn btn-secondary" id="rtr-ifaces-toggle-${id}" onclick="toggleRouterInterfaces('${id}')" style="padding:2px 8px;font-size:10px">Show Interfaces</button>
                <button class="btn btn-secondary" onclick="refreshInterfaces('${id}')" style="padding:2px 8px;font-size:10px">Refresh</button>
            </div>
            <div id="rtr-ifaces-${id}" style="display:none;padding:6px 8px;background:var(--bg-card);border:1px solid var(--border);border-radius:4px;margin-top:4px">
                ${ifaceRows}
            </div>
        </div>
        <!-- Presets + Impairment in compact row -->
        <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:8px">
            <span style="font-size:10px;color:var(--text-secondary)">Presets:</span>
            <button class="btn btn-secondary" onclick="applyRouterPreset('${id}','degraded_wan')" style="padding:2px 8px;font-size:10px">Degraded WAN</button>
            <button class="btn btn-secondary" onclick="applyRouterPreset('${id}','voice_sla')" style="padding:2px 8px;font-size:10px">Voice SLA</button>
            <button class="btn btn-secondary" onclick="applyRouterPreset('${id}','video_sla')" style="padding:2px 8px;font-size:10px">Video SLA</button>
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:8px">
            <label style="font-size:10px;color:var(--text-secondary)">Latency</label>
            <input type="number" id="rtr-${id}-latency" value="${(r.impairment_config||{}).latency_ms||0}" min="0" max="5000" style="${inputStyle}"><span style="font-size:10px;color:var(--text-secondary)">ms</span>
            <label style="font-size:10px;color:var(--text-secondary);margin-left:4px">Jitter</label>
            <input type="number" id="rtr-${id}-jitter" value="${(r.impairment_config||{}).jitter_ms||0}" min="0" max="2000" style="${inputStyle}"><span style="font-size:10px;color:var(--text-secondary)">ms</span>
            <label style="font-size:10px;color:var(--text-secondary);margin-left:4px">Loss</label>
            <input type="number" id="rtr-${id}-loss" value="${(r.impairment_config||{}).packet_loss_pct||0}" min="0" max="100" step="0.5" style="${inputStyle}"><span style="font-size:10px;color:var(--text-secondary)">%</span>
            <label style="font-size:10px;color:var(--text-secondary);margin-left:4px">BW</label>
            <input type="number" id="rtr-${id}-bw" value="${(r.impairment_config||{}).bandwidth_mbps||0}" min="0" max="10000" step="10" style="width:70px;padding:3px 6px;font-size:11px;background:var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:3px"><span style="font-size:10px;color:var(--text-secondary)">Mbps</span>
        </div>
        <!-- Mode Buttons -->
        <div style="display:flex;gap:6px">
            <button class="btn btn-start" onclick="applyRouterMode('${id}','healthy')" style="padding:4px 12px;font-size:11px">Healthy</button>
            <button class="btn btn-primary" onclick="applyRouterMode('${id}','impaired')" style="padding:4px 12px;font-size:11px">Apply Impaired</button>
            <button class="btn btn-danger" onclick="applyRouterMode('${id}','link_down')" style="padding:4px 12px;font-size:11px">Link Down</button>
        </div>
        ` : '<div style="color:var(--text-secondary);font-size:11px;padding:6px 0">Router disconnected. Click Reconnect to restore.</div>'}
    </div>`;
}

async function loadRouters() {
    try {
        const resp = await fetch('/api/routers');
        const routers = await resp.json();
        const container = document.getElementById('router-cards-container');
        if (!container) return;
        if (!routers.length) {
            container.innerHTML = '<div style="color:var(--text-secondary);font-size:12px;text-align:center;padding:12px">No routers added. Add a router above to start link simulation.</div>';
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
            container.innerHTML = '<div style="color:var(--text-secondary);font-size:12px;text-align:center;padding:12px">No routers added. Add a router above to start link simulation.</div>';
            return;
        }
        const savedValues = {};
        const expandedIfaces = {};
        for (const r of routers) {
            const rid = r.router_id;
            for (const f of ['latency','jitter','loss','bw']) {
                const el = document.getElementById('rtr-' + rid + '-' + f);
                if (el) savedValues[rid + '-' + f] = el.value;
            }
            const ifaceEl = document.getElementById('rtr-ifaces-' + rid);
            if (ifaceEl && ifaceEl.style.display !== 'none') expandedIfaces[rid] = true;
        }
        container.innerHTML = routers.map(r => renderRouterCard(r)).join('');
        for (const [key, val] of Object.entries(savedValues)) {
            const el = document.getElementById('rtr-' + key);
            if (el) el.value = val;
        }
        for (const rid of Object.keys(expandedIfaces)) {
            const ifaceEl = document.getElementById('rtr-ifaces-' + rid);
            const toggleBtn = document.getElementById('rtr-ifaces-toggle-' + rid);
            if (ifaceEl) ifaceEl.style.display = 'block';
            if (toggleBtn) toggleBtn.textContent = 'Hide Interfaces';
        }
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

        const protoAgg = {};
        for (const [jobKey, info] of Object.entries(data.jobs)) {
            const baseParts = jobKey.split('_');
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

// ─── Topology ───────────────────────────────────────────────

let topoNetwork = null;
let topoAnimInterval = null;
let topoEdges = null;
let topoAnimState = 0;
let topoHasTraffic = false;
let topoActiveEdgeIds = [];  // edges belonging to running protocols (animated)

const TOPO_COLORS = [
    '#0066cc', '#00a67e', '#e67e22', '#8e44ad', '#2980b9',
    '#c0392b', '#16a085', '#d35400', '#2c3e50', '#27ae60'
];

async function refreshTopology() {
    try {
        const resp = await fetch('/api/topology');
        const data = await resp.json();
        renderTopology(data);
    } catch(e) {
        const container = document.getElementById('topology-container');
        if (container) container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-secondary)">Failed to load topology</div>';
    }
}

function renderTopology(data) {
    const container = document.getElementById('topology-container');
    if (!container) return;

    const nodes = new vis.DataSet();
    const edges = new vis.DataSet();
    topoEdges = edges;
    topoActiveEdgeIds = [];

    const pathsObj = data.paths || {};
    const routers = data.routers || [];

    // Build router IP lookup
    const routerByIp = {};
    routers.forEach(r => { routerByIp[r.ip] = r; });

    // Separate running paths from default
    const pathKeys = Object.keys(pathsObj);
    const runningPaths = pathKeys.filter(k => k !== 'default' && pathsObj[k].running);
    topoHasTraffic = runningPaths.length > 0;

    // Group paths by hop signature for merging
    const hopSigMap = {};
    pathKeys.forEach(k => {
        const p = pathsObj[k];
        const sig = (p.hops || []).map(h => h.ip).join(',');
        if (!hopSigMap[sig]) hopSigMap[sig] = [];
        hopSigMap[sig].push(k);
    });

    // CLIENT node
    nodes.add({
        id: 'client', label: 'CLIENT\n' + data.client_ip, shape: 'box',
        color: { background: '#e6f4ee', border: '#00a67e' },
        font: { size: 13, face: 'monospace', bold: true, multi: true }, borderWidth: 2, margin: 12,
        level: 0,
    });

    // SERVER node (rightmost)
    const maxHops = Math.max(1, ...pathKeys.map(k => (pathsObj[k].hops || []).length));
    nodes.add({
        id: 'server', label: 'SERVER\n' + data.server_host, shape: 'box',
        color: { background: '#e8f0fe', border: '#0066cc' },
        font: { size: 13, face: 'monospace', bold: true, multi: true }, borderWidth: 2, margin: 12,
        level: maxHops + 1,
    });

    // Track which unique paths we've rendered (by hop signature)
    const renderedSigs = new Set();
    let pathIndex = 0;
    const addedNodes = new Set(['client', 'server']);

    // Render each unique path
    pathKeys.forEach(pathKey => {
        const path = pathsObj[pathKey];
        const hops = path.hops || [];
        const sig = hops.map(h => h.ip).join(',');

        // Check if this signature was already rendered by a merged group
        if (renderedSigs.has(sig)) return;
        renderedSigs.add(sig);

        // Find all protocols sharing this path
        const mergedKeys = hopSigMap[sig] || [pathKey];
        const labels = mergedKeys.map(k => pathsObj[k].label);
        const isRunning = mergedKeys.some(k => k !== 'default' && pathsObj[k].running);
        const isDefaultOnly = mergedKeys.length === 1 && mergedKeys[0] === 'default';

        const color = isDefaultOnly ? '#aab4c2' : TOPO_COLORS[pathIndex % TOPO_COLORS.length];
        if (!isDefaultOnly) pathIndex++;

        const pathLabel = labels.join(', ');
        const edgeWidth = isRunning ? 3 : 2;

        // Create hop nodes for this path
        const nodeChain = ['client'];
        hops.forEach((h, i) => {
            const isLast = i === hops.length - 1;
            const isTimeout = h.ip === '*';
            // Unique node ID per path to allow divergent paths
            const hopId = 'hop_' + pathKey + '_' + h.hop;

            // Skip last hop if it matches server
            if (isLast && !isTimeout && (h.ip === data.server_host || h.ip === data.client_ip)) {
                return;
            }

            // Reuse node if same IP already exists at same level from another path
            const sharedId = 'hop_shared_' + h.hop + '_' + h.ip;
            if (addedNodes.has(sharedId)) {
                nodeChain.push(sharedId);
                return;
            }

            const router = routerByIp[h.ip];
            let bg = '#e8f0fe', border = color, label = '';

            if (isTimeout) {
                bg = '#fde8e8'; border = '#dc3545';
                label = 'HOP ' + h.hop + '\n* (timeout)';
            } else if (router) {
                const mc = { healthy: { bg: '#e6f4ee', b: '#00a67e' }, impaired: { bg: '#fff3e0', b: '#ff9800' }, link_down: { bg: '#fde8e8', b: '#dc3545' } };
                const c = mc[router.current_mode] || { bg: '#e8f0fe', b: color };
                bg = c.bg; border = c.b;
                const mode = router.current_mode ? router.current_mode.toUpperCase().replace('_', ' ') : '';
                label = router.name + '\n' + h.ip + '\n' + mode;
                if (router.current_mode === 'impaired' && router.impairment_config) {
                    const ic = router.impairment_config;
                    const parts = [];
                    if (ic.latency_ms) parts.push(ic.latency_ms + 'ms');
                    if (ic.jitter_ms) parts.push('j' + ic.jitter_ms + 'ms');
                    if (ic.packet_loss_pct) parts.push(ic.packet_loss_pct + '%loss');
                    if (ic.bandwidth_mbps) parts.push(ic.bandwidth_mbps + 'Mbps');
                    if (parts.length) label += '\n' + parts.join(' / ');
                }
            } else {
                label = 'HOP ' + h.hop + '\n' + h.ip + (h.rtt !== '--' ? '\n' + h.rtt + ' ms' : '');
            }

            const useId = sharedId;
            nodes.add({
                id: useId, label: label, shape: 'box',
                color: { background: bg, border: border },
                font: { size: 11, face: 'monospace', multi: true }, borderWidth: 2, margin: 10,
                level: i + 1,
            });
            addedNodes.add(useId);
            nodeChain.push(useId);
        });
        nodeChain.push('server');

        // Create edges for this path
        const roundness = pathIndex * 0.15;
        for (let i = 0; i < nodeChain.length - 1; i++) {
            const edgeId = 'e_' + pathKey + '_' + i;
            const isFirst = i === 0;
            edges.add({
                id: edgeId, from: nodeChain[i], to: nodeChain[i + 1], arrows: 'to',
                color: { color: isRunning ? color : '#aab4c2' },
                width: edgeWidth,
                dashes: isRunning ? [8, 4] : (isDefaultOnly ? [4, 4] : false),
                label: isFirst ? pathLabel : '',
                font: { size: 9, color: color, strokeWidth: 0, background: 'rgba(255,255,255,0.7)' },
                smooth: pathIndex > 1 ? { type: 'curvedCW', roundness: roundness } : { type: 'dynamic' },
            });
            if (isRunning) topoActiveEdgeIds.push({ id: edgeId, color: color });
        }
    });

    // If no paths at all, direct client → server edge
    if (pathKeys.length === 0) {
        edges.add({
            id: 'e_direct', from: 'client', to: 'server', arrows: 'to',
            color: { color: '#aab4c2' }, width: 2, dashes: [4, 4],
            label: 'No path data', font: { size: 9, color: '#aab4c2', strokeWidth: 0 },
        });
    }

    const options = {
        layout: { hierarchical: { direction: 'LR', sortMethod: 'directed', levelSeparation: 180, nodeSpacing: 60 } },
        physics: false,
        interaction: { dragNodes: true, zoomView: true, dragView: true },
        edges: { font: { align: 'top' } },
    };

    // Stats bar below topology
    let statsEl = document.getElementById('topology-stats');
    if (!statsEl) {
        statsEl = document.createElement('div');
        statsEl.id = 'topology-stats';
        statsEl.style.cssText = 'padding:8px 12px;font-size:11px;color:var(--text-secondary);border-top:1px solid var(--border);background:var(--bg-card)';
        container.parentNode.appendChild(statsEl);
    }
    if (topoHasTraffic) {
        const statParts = runningPaths.map(k => {
            const p = pathsObj[k];
            return p.label + ' (' + fmtBytes((p.stats || {}).bytes_sent || 0) + ' sent)';
        });
        statsEl.innerHTML = '<strong style="color:var(--accent-teal)">Active:</strong> ' + statParts.join(' | ');
    } else {
        statsEl.innerHTML = '<span style="color:var(--text-secondary)">No active traffic flows</span>';
    }

    if (topoNetwork) {
        topoNetwork.setData({ nodes, edges });
    } else {
        topoNetwork = new vis.Network(container, { nodes, edges }, options);
    }

    // Start/stop animation
    if (topoHasTraffic && !topoAnimInterval) {
        topoAnimInterval = setInterval(animateTopology, 800);
    } else if (!topoHasTraffic && topoAnimInterval) {
        clearInterval(topoAnimInterval);
        topoAnimInterval = null;
    }
}

function animateTopology() {
    if (!topoEdges || !topoHasTraffic) return;
    topoAnimState = (topoAnimState + 1) % 3;
    const dashPatterns = [[8, 4], [6, 6], [4, 8]];
    topoActiveEdgeIds.forEach(e => {
        // Lighten the base color for animation effect
        const shade = topoAnimState === 0 ? e.color : (topoAnimState === 1 ? e.color + 'cc' : e.color + '99');
        topoEdges.update({ id: e.id, dashes: dashPatterns[topoAnimState], color: { color: e.color } });
    });
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
    setInterval(refreshTopology, 10000);
    pollStatus();
    refreshTopology();
    addLog('Dashboard ready.');
});
