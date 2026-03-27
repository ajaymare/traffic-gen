# Traffic Generator

Docker-based network traffic generation and testing tool with a web UI. Supports multiple protocols with real-time bandwidth, latency, and packet loss control.

## Protocols

| Protocol | Description |
|----------|-------------|
| HTTP | GET/POST with configurable data size, upload mode |
| HTTPS | Same as HTTP with optional SSL verification skip |
| TCP | Echo client or iperf3 bandwidth test |
| UDP | Echo client or iperf3 bandwidth test |
| FTP | Continuous file download for specified duration |
| SSH | Repeated command execution |
| ICMP | Ping with configurable packet size |

## Architecture

- **Server**: Single container running nginx (HTTP/HTTPS), iperf3, TCP/UDP echo servers, vsftpd (FTP), openssh (SSH) — managed by supervisord
- **Client**: Web UI (Flask) with traffic engine and tc/netem network shaping

## Quick Start — Same Machine

```bash
docker compose up -d
```

Open `http://localhost:8080` for the dashboard.

## Deployment — Separate VMs

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

Open `http://<client-vm-ip>:8080` for the dashboard.

## Features

- **Duration control**: Set how long each traffic flow should run (in seconds)
- **Network impairment**: Live sliders for latency (0-500ms), jitter (0-200ms), packet loss (0-50%), bandwidth limit (0-100 Mbps)
- **iperf3 bandwidth testing**: TCP/UDP with configurable bandwidth target, parallel streams, and reverse (download) mode
- **FTP continuous download**: Downloads large files (1GB) in a loop for the specified duration
- **HTTPS SSL bypass**: Toggle to ignore SSL certificate validation
- **HTTP upload/download**: Stream up to 1GB data via `/generate/<size_mb>` endpoint
- **Multi-client**: Server handles concurrent connections across all protocols
- **Live stats**: Real-time bytes sent/received, request count, error tracking
- **Countdown timer**: Shows remaining time for each running traffic flow

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
| 22 | SSH (testuser/testpass) |

## Default Credentials

- **SSH**: `testuser` / `testpass`
- **FTP**: `anonymous` (no password) or `ftpuser` / `ftppass`

## Run from Docker Hub (No Build Required)

Multi-platform images (amd64 + arm64) are available on Docker Hub.

### Same Machine

```bash
docker network create traffic-net

docker run -d --name traffic-server \
  --network traffic-net \
  --restart unless-stopped \
  ajaymare/traffic-gen-server:latest

docker run -d --name traffic-client \
  --network traffic-net \
  --cap-add NET_ADMIN \
  -p 8080:8080 \
  -e SERVER_HOST=traffic-server \
  --restart unless-stopped \
  ajaymare/traffic-gen-client:latest
```

Open `http://localhost:8080` for the dashboard.

### Separate VMs

**Server VM:**

```bash
docker run -d --name traffic-server \
  -p 80:80 -p 443:443 -p 5201:5201 -p 5201:5201/udp \
  -p 9999:9999 -p 9998:9998/udp \
  -p 21:21 -p 21100-21110:21100-21110 -p 22:22 \
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

Open `http://<client-vm-ip>:8080` for the dashboard.

### Stop and Remove

```bash
docker stop traffic-client traffic-server
docker rm traffic-client traffic-server
docker network rm traffic-net  # if using same machine setup
```
