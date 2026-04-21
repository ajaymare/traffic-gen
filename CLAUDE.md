# CLAUDE.md

## Project Overview

Docker-based network traffic generator with web UI dashboards for generating, monitoring, and controlling multi-protocol traffic between client and server containers. Used for SD-WAN demos, network testing, and firewall App-ID validation.

## Architecture

- **Client** (`client/`): Flask web app (port 8080) + traffic engine + router shaper + network shaper
- **Server** (`server/`): nginx + iperf3 + DNS + FTP + SSH + server dashboard (port 8082), managed by supervisord
- Both containers serve HTTPS dashboards on port 8443 via nginx reverse proxy with self-signed certs

## Key Files

### Client
- `client/app.py` — Flask routes and REST API endpoints
- `client/traffic_engine.py` — Protocol handlers (HTTPS, iperf3, hping3, HTTP, DNS, FTP, SSH, ext_https), job management with threading
- `client/router_shaper.py` — SSH-based router link simulation (tc/netem impairment via SSH)
- `client/network_shaper.py` — Local tc/netem shaping, source IP aliases
- `client/static/app.js` — Frontend JS: protocol cards, topology (vis.js), router management, polling
- `client/static/style.css` — Blue/corporate theme CSS variables
- `client/templates/dashboard.html` — Client dashboard HTML template (Jinja2)

### Server
- `server/dashboard.py` — Server dashboard with inline HTML/CSS/JS (~1400 lines). Contains `DASHBOARD_HTML` string with full client tab rendering, protocol controls, topology, and router management (all mirrored from client)
- `server/app.py` — nginx config server, echo server
- `server/stats_collector.py` — Server-side stats collection

## Build & Deploy

```bash
# Build and push amd64 images
docker buildx build --platform linux/amd64 -t ajaymare/traffic-server:latest -f server/Dockerfile server/ --push
docker buildx build --platform linux/amd64 -t ajaymare/traffic-client:latest -f client/Dockerfile client/ --push

# Local testing (both containers)
docker compose up -d

# Separate VMs
docker compose -f docker-compose.server.yml up -d  # server VM
SERVER_HOST=<server-ip> docker compose -f docker-compose.client.yml up -d  # client VM
```

## Development Notes

### Dual Dashboard Pattern
Every UI feature must be implemented in **both** dashboards:
1. Client dashboard: `client/templates/dashboard.html` + `client/static/app.js` + `client/static/style.css`
2. Server dashboard: `server/dashboard.py` inline `DASHBOARD_HTML` string (uses ES5-compatible JS with `var`, string concatenation instead of template literals)

The server dashboard proxies client API calls via `/api/client/<name>/...` routes.

### CSS Theming
Uses CSS custom properties in `:root` — blue/corporate palette with white cards. Both dashboards must have matching `:root` blocks.

### Auto-Refresh Considerations
- Status polling runs every 2s — any re-rendered UI must preserve user state (expanded sections, input values, interface toggles)
- Pattern: save state before innerHTML replacement, restore after (see `pollRouterStatus()`)

### Protocol Definitions
Protocols are defined as JS objects in both `app.js` (`PROTOCOLS`) and `dashboard.py` (`PROTOCOLS`). Fields include type, default values, and advanced keys (DSCP, rate_pps, burst). Keep both in sync.

### Topology
Uses vis.js Network library (CDN) for live topology visualization. Backend runs `traceroute` to discover hops, caches for 30s. Shows animated edges when traffic flows are active.

## Git Conventions

- Contributor: Ajay Mare
- Docker images: `ajaymare/traffic-server:latest`, `ajaymare/traffic-client:latest` (amd64 only)
- Remote: `https://github.com/ajaymare/traffic-gen.git`
