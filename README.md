# Traffic Generator

Docker-based network traffic generation and testing tool with a web UI. Supports multiple protocols with real-time bandwidth, latency, and packet loss control.

## Protocols

| Protocol | Description |
|----------|-------------|
| HTTP | GET/POST with configurable data size, upload mode |
| HTTPS | Same as HTTP with optional SSL verification skip |
| HTTP/2 | True HTTP/2 traffic using httpx with h2 |
| TCP | Echo client or iperf3 bandwidth test |
| UDP | Echo client or iperf3 bandwidth test |
| FTP | Continuous file download, upload custom files via dashboard |
| SSH | Repeated command execution |
| ICMP | Ping with configurable packet size |

## Architecture

- **Server**: Single container running nginx (HTTP/HTTPS), iperf3, TCP/UDP echo servers, vsftpd (FTP), openssh (SSH), server dashboard — managed by supervisord
- **Client**: Web UI (Flask) with traffic engine, tc/netem network shaping, and source IP simulation
- **Server Dashboard**: Unified multi-client control panel with tabs — monitor server stats and control multiple clients from a single UI

## Deployment

### Server VM

```bash
# Copy the server/ directory and docker-compose.server.yml
docker compose -f docker-compose.server.yml up -d
```

### Client VM

```bash
# Copy the client/ directory and docker-compose.client.yml
SERVER_HOST=<server-vm-ip> docker compose -f docker-compose.client.yml up -d
```

- Client dashboard: `http://<client-vm-ip>:8080`
- Server dashboard: `http://<server-vm-ip>:8082`

## Features

- **Duration control**: Default 15-minute test duration, configurable per protocol
- **Random data sizes**: Toggle random packet/file sizes for HTTP, HTTPS, TCP, UDP, FTP
- **Random bandwidth**: Cycles bandwidth limit randomly between 20 Mbps and 1 Gbps every 10 seconds
- **Random source IPs**: Simulate multiple clients from a single container using IP aliases (configurable base IP and count)
- **Network impairment**: Live sliders for latency (0-500ms), jitter (0-200ms), packet loss (0-50%), bandwidth limit (0-100 Mbps)
- **Select all / bulk actions**: Start or stop multiple protocols at once
- **HTTP/2 support**: True HTTP/2 traffic generation using httpx with h2
- **iperf3 bandwidth testing**: TCP/UDP with configurable bandwidth target, parallel streams, and reverse (download) mode
- **FTP file management**: Upload custom files to the server via dashboard, download them from client
- **HTTPS SSL bypass**: Toggle to ignore SSL certificate validation
- **HTTP upload/download**: Stream up to 1GB data via `/generate/<size_mb>` endpoint
- **Multi-client control**: Server dashboard (port 8082) with tabs to manage multiple clients from a single UI
- **Live stats**: Real-time bytes sent/received, request count, error tracking with 2-second auto-refresh
- **Countdown timer**: Shows remaining time for each running traffic flow
- **Activity logs**: Per-protocol logs visible on both client and server dashboards
- **Persistent settings**: Network shaping and source IP settings survive page refreshes

## Server Ports

| Port | Service |
|------|---------|
| 80 | HTTP |
| 443 | HTTPS (self-signed cert) |
| 5201 | iperf3 |
| 9999 | TCP echo |
| 9998/udp | UDP echo |
| 21 | FTP |
| 21100-21110 | FTP passive |
| 22 (map to 2222 if 22 is in use) | SSH (testuser/testpass) |
| 8082 | Server Dashboard |

## Default Credentials

- **SSH**: `testuser` / `testpass`
- **FTP**: `anonymous` (no password) or `ftpuser` / `ftppass`

## Run from Docker Hub (No Build Required)

Multi-platform images (amd64 + arm64) are available on Docker Hub.

**Server VM:**

```bash
docker run -d --name traffic-server \
  -p 80:80 -p 443:443 -p 5201:5201 -p 5201:5201/udp \
  -p 9999:9999 -p 9998:9998/udp \
  -p 21:21 -p 21100-21110:21100-21110 -p 2222:22 \
  -p 8082:8082 \
  --restart unless-stopped \
  ajaymare/traffic-gen-server:latest
```

**Client VM:**

```bash
docker run -d --name traffic-client \
  --cap-add NET_ADMIN \
  -p 8080:8080 \
  -e SERVER_HOST=<server-vm-ip> \
  --restart unless-stopped \
  ajaymare/traffic-gen-client:latest
```

- Client dashboard: `http://<client-vm-ip>:8080`
- Server dashboard: `http://<server-vm-ip>:8082`

### Stop and Remove

```bash
docker stop traffic-client traffic-server
docker rm traffic-client traffic-server
```

## Server Dashboard — Multi-Client Control

The server dashboard (`http://<server>:8082`) provides a unified control panel:

1. **Server tab**: Aggregate traffic stats, per-service status, active connections, FTP file management (upload/delete)
2. **Client tabs**: Click "+" to register clients by name and URL (e.g., `http://192.168.1.10:8080`). Each tab provides full protocol controls, network shaping, random source IP configuration, and live activity logs — all proxied through the server.

## Random Source IPs

Simulate traffic from multiple clients using a single container:

1. Open client dashboard → Network Impairment → check **Random Source IPs**
2. Set Base IP (must be in the container's subnet) and Count → click **Apply**
3. Each connection binds to a random alias IP

Requires `NET_ADMIN` capability (already included in docker run commands above).
