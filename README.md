# Traffic Generator

Docker-based network traffic generation and testing tool with a web UI. Supports multiple protocols with real-time bandwidth, latency, and packet loss control.

## Protocols

| Protocol | Description |
|----------|-------------|
| HTTPS | GET/POST with optional HTTP/2, SSL bypass, upload mode |
| iperf3 TCP | Bandwidth testing with parallel streams, reverse mode |
| iperf3 UDP | Bandwidth testing with parallel streams, reverse mode |
| hping3 | ICMP, TCP SYN/ACK/FIN, UDP, Traceroute with flood mode |
| TCP | Echo client with configurable message size |
| UDP | Echo client with configurable message size |
| FTP | Continuous file download with progress logging |
| SSH | Repeated command execution over SSH |
| External HTTPS | Multi-URL round-robin to external sites (Google, Cloudflare, etc.) |

## Architecture

- **Server**: Single container running nginx (HTTP/HTTPS with HTTP/2), iperf3 (3 instances for concurrency), TCP/UDP echo servers, vsftpd (FTP), openssh (SSH on port 2222), server dashboard — managed by supervisord
- **Client**: Web UI (Flask) with traffic engine, tc/netem network shaping, and source IP simulation
- **Server Dashboard**: Unified multi-client control panel with tabs — monitor server stats and control multiple clients from a single UI

## Deployment

### Separate VMs (Recommended)

**Server VM:**

```bash
docker compose -f docker-compose.server.yml up -d
```

**Client VM:**

```bash
SERVER_HOST=<server-vm-ip> docker compose -f docker-compose.client.yml up -d
```

- Client dashboard: `https://<client-vm-ip>:8443` (or `http://<client-vm-ip>:8080`)
- Server dashboard: `https://<server-vm-ip>:8443` (or `http://<server-vm-ip>:8082`)

### Same Server

Run both containers on a single machine for local testing:

```bash
docker compose up -d
```

- Client dashboard: `https://<server-ip>:8443` (or `http://<server-ip>:8080`)
- Server dashboard: `https://<server-ip>:18443` (or `http://<server-ip>:8082`)

## Features

### Traffic Control
- **Duration control**: Default 15-minute test duration, configurable per protocol
- **Rate control (pps)**: Set target packets-per-second instead of manual interval
- **Burst mode**: Send N requests rapidly, pause for X seconds, repeat (configurable burst size and pause)
- **Multiple flows**: Run up to 20 parallel flows per protocol
- **DSCP marking**: Set QoS markings (EF, AF, CS classes) on all protocols
- **Auto-refresh toggle**: Enable/disable live dashboard polling
- **Random data sizes**: Toggle random packet/file sizes for HTTPS, TCP, UDP, FTP
- **Select all / bulk actions**: Start or stop multiple protocols at once

### Network Impairment
- **Latency**: 0–500ms with jitter (0–200ms, normal distribution)
- **Packet loss**: 0–50%
- **Bandwidth limit**: 0–1000 Mbps
- **Random bandwidth**: Cycles bandwidth limit randomly between 20 Mbps and 1 Gbps every 10 seconds

### Source IP Simulation
- **Random source IPs**: Simulate multiple clients from a single container using IP aliases
- **X-Forwarded-For**: When random source IPs are enabled, alias IPs are used in X-Forwarded-For headers for all L7 HTTP traffic

### External HTTPS
- **Multi-URL support**: Enter multiple target URLs (one per line) in the textarea
- **Round-robin**: Requests cycle through all configured URLs in order
- **Per-request logging**: Activity logs show which URL each request targeted

### Monitoring
- **Live stats**: Real-time bytes sent/received, request count, error tracking with 2-second auto-refresh
- **Activity logs**: Detailed per-request logs for every protocol showing request/response details
- **Countdown timer**: Shows remaining time for each running traffic flow
- **Docker healthchecks**: Both containers report health status via `docker ps`

### Protocol-Specific
- **HTTPS with HTTP/2**: Toggle HTTP/2 checkbox for true HTTP/2 traffic using httpx with h2, or use standard HTTPS/1.1
- **iperf3 bandwidth testing**: Dedicated TCP/UDP cards with port 5201 default; configurable bandwidth, parallel streams, reverse mode; 3 server instances (ports 5201–5203) for concurrent clients with auto-port selection
- **hping3**: Advanced packet crafting — ICMP ping, TCP SYN/ACK/FIN scans, UDP probes, traceroute with flood mode, custom TTL, data size, and DSCP
- **FTP file management**: Upload custom files to the server via dashboard, download with 1MB progress logging
- **HTTPS SSL bypass**: Toggle to ignore SSL certificate validation
- **HTTPS upload/download**: Stream up to 1GB data via `/generate/<size_mb>` endpoint
- **Multi-client control**: Server dashboard (port 8082) with tabs to manage multiple clients

## Activity Log Examples

Each protocol logs detailed per-request information:

| Protocol | Example Log |
|----------|-------------|
| HTTPS | `GET https://server/ → 200 \| sent=0B recv=104857600B` |
| HTTPS (HTTP/2) | `GET https://server/ → 200 (HTTP/2) \| sent=0B recv=1234B` |
| iperf3 | `iperf3 :5201 \| [5] 0.00-1.00 sec 11.8 MBytes 98.9 Mbits/sec` |
| hping3 | `hping3 server → len=46 ip=10.0.0.2 ttl=64 rtt=0.5 ms` |
| TCP | `TCP server:9999 → sent=1024B recv=1024B` |
| UDP | `UDP server:9998 → sent=1024B recv=1024B` |
| FTP | `FTP testfile_1gb.bin ← recv=52428800B (5%)` |
| SSH | `SSH testuser@server $ uptime → exit=0 \| recv=42B \| 14:23 up 3 days` |
| Ext HTTPS | `GET https://www.google.com → 200 \| sent=0B recv=14523B` |

## Server Ports

| Port | Service |
|------|---------|
| 80 | HTTP (nginx) |
| 443 | HTTPS (self-signed cert, HTTP/2 enabled) |
| 5201–5203 | iperf3 (3 instances for concurrent clients) |
| 9999 | TCP echo |
| 9998/udp | UDP echo |
| 21 | FTP |
| 21100–21110 | FTP passive |
| 2222 | SSH (testuser/testpass) |
| 8082 | Server Dashboard (HTTP) |
| 8443 | Dashboard HTTPS (self-signed cert) |

## Default Credentials

- **SSH**: `testuser` / `testpass`
- **FTP**: `anonymous` (no password) or `ftpuser` / `ftppass`

## Run from Docker Hub (No Build Required)

Images (amd64) are available on Docker Hub.

### Separate VMs (Recommended)

**Server VM:**

```bash
docker run -d --name traffic-server \
  -p 80:80 -p 443:443 \
  -p 5201:5201 -p 5201:5201/udp \
  -p 5202:5202 -p 5202:5202/udp \
  -p 5203:5203 -p 5203:5203/udp \
  -p 9999:9999 -p 9998:9998/udp \
  -p 21:21 -p 21100-21110:21100-21110 \
  -p 2222:2222 \
  -p 8082:8082 \
  -p 8443:8443 \
  --restart unless-stopped \
  ajaymare/traffic-gen-server:latest
```

**Client VM:**

```bash
docker run -d --name traffic-client \
  --cap-add NET_ADMIN \
  -p 8080:8080 \
  -p 8443:8443 \
  -e SERVER_HOST=<server-vm-ip> \
  --restart unless-stopped \
  ajaymare/traffic-gen-client:latest
```

- Client dashboard: `https://<client-vm-ip>:8443` (or `http://<client-vm-ip>:8080`)
- Server dashboard: `https://<server-vm-ip>:8443` (or `http://<server-vm-ip>:8082`)

### Same Server

```bash
# Create a docker network
docker network create traffic-net

# Start server
docker run -d --name traffic-server \
  --network traffic-net \
  -p 80:80 -p 443:443 \
  -p 5201:5201 -p 5201:5201/udp \
  -p 5202:5202 -p 5202:5202/udp \
  -p 5203:5203 -p 5203:5203/udp \
  -p 9999:9999 -p 9998:9998/udp \
  -p 21:21 -p 21100-21110:21100-21110 \
  -p 2222:2222 \
  -p 8082:8082 \
  -p 18443:8443 \
  --restart unless-stopped \
  ajaymare/traffic-gen-server:latest

# Start client (points to server container by name)
docker run -d --name traffic-client \
  --network traffic-net \
  --cap-add NET_ADMIN \
  -p 8080:8080 \
  -p 8443:8443 \
  -e SERVER_HOST=traffic-server \
  --restart unless-stopped \
  ajaymare/traffic-gen-client:latest
```

- Client dashboard: `https://<server-ip>:8443` (or `http://<server-ip>:8080`)
- Server dashboard: `https://<server-ip>:18443` (or `http://<server-ip>:8082`)

### Stop and Remove

```bash
docker stop traffic-client traffic-server
docker rm traffic-client traffic-server
docker network rm traffic-net  # if using same-server setup
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
4. All L7 HTTP traffic automatically uses alias IPs in the `X-Forwarded-For` header

Requires `NET_ADMIN` capability (already included in docker run commands above).
