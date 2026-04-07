"""
Network services: HTTP server (port 9999) and DNS forwarder (port 9998).
Replaces raw echo with recognizable App-ID protocols for Palo Alto firewalls.
"""
import json
import os
import socket
import struct
import threading
import signal
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

STATS_FILE = '/tmp/echo_stats.json'
stats_lock = threading.Lock()
stats = {
    'http': {'requests': 0, 'bytes_recv': 0, 'bytes_sent': 0, 'active': 0,
             'gets': 0, 'posts': 0},
    'dns': {'queries': 0, 'bytes_recv': 0, 'bytes_sent': 0, 'last_active': 0,
            'forwarded': 0, 'errors': 0},
}

# ─── HTTP Server (port 9999) ─────────────────────────────────

class TrafficHTTPHandler(BaseHTTPRequestHandler):
    """Simple HTTP server for generating web-browsing App-ID traffic."""

    def log_message(self, format, *args):
        pass  # Suppress default logging

    def do_GET(self):
        with stats_lock:
            stats['http']['requests'] += 1
            stats['http']['gets'] += 1
            stats['http']['active'] += 1
        try:
            if self.path.startswith('/download'):
                # Parse size parameter (KB)
                size_kb = 1
                if '?' in self.path:
                    params = dict(p.split('=') for p in self.path.split('?')[1].split('&') if '=' in p)
                    size_kb = int(params.get('size', 1))
                size_kb = max(1, min(size_kb, 102400))  # Cap at 100MB
                data = os.urandom(size_kb * 1024)
                self.send_response(200)
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                with stats_lock:
                    stats['http']['bytes_sent'] += len(data)
            else:
                body = (
                    '<html><head><title>Traffic Generator</title></head>'
                    '<body><h1>Traffic Generator HTTP Server</h1>'
                    '<p>Port 9999 — App-ID: web-browsing</p>'
                    f'<p>Requests served: {stats["http"]["requests"]}</p>'
                    '</body></html>'
                ).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                with stats_lock:
                    stats['http']['bytes_sent'] += len(body)
        finally:
            with stats_lock:
                stats['http']['active'] -= 1

    def do_POST(self):
        with stats_lock:
            stats['http']['requests'] += 1
            stats['http']['posts'] += 1
            stats['http']['active'] += 1
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b''
            with stats_lock:
                stats['http']['bytes_recv'] += len(body)
            response = json.dumps({
                'status': 'ok',
                'bytes_received': len(body),
            }).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
            with stats_lock:
                stats['http']['bytes_sent'] += len(response)
        finally:
            with stats_lock:
                stats['http']['active'] -= 1


def http_server(port=9999):
    server = HTTPServer(('0.0.0.0', port), TrafficHTTPHandler)
    print(f"[HTTP] Server on port {port}")
    server.serve_forever()


# ─── DNS Forwarder (port 9998) ───────────────────────────────

UPSTREAM_DNS = '8.8.8.8'
UPSTREAM_DNS_PORT = 53


def dns_forwarder(port=9998):
    """Forward DNS queries to upstream resolver.
    Receives standard DNS query packets, forwards to 8.8.8.8, returns response.
    """
    srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('0.0.0.0', port))
    print(f"[DNS] Forwarder on port {port} → {UPSTREAM_DNS}:{UPSTREAM_DNS_PORT}")

    while True:
        try:
            data, client_addr = srv.recvfrom(4096)
            with stats_lock:
                stats['dns']['queries'] += 1
                stats['dns']['bytes_recv'] += len(data)
                stats['dns']['last_active'] = time.time()

            # Forward to upstream DNS
            fwd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            fwd_sock.settimeout(5)
            try:
                fwd_sock.sendto(data, (UPSTREAM_DNS, UPSTREAM_DNS_PORT))
                response, _ = fwd_sock.recvfrom(4096)
                srv.sendto(response, client_addr)
                with stats_lock:
                    stats['dns']['bytes_sent'] += len(response)
                    stats['dns']['forwarded'] += 1
            except socket.timeout:
                with stats_lock:
                    stats['dns']['errors'] += 1
            finally:
                fwd_sock.close()
        except Exception:
            with stats_lock:
                stats['dns']['errors'] += 1


# ─── Stats & Main ────────────────────────────────────────────

def save_stats():
    while True:
        with stats_lock:
            with open(STATS_FILE, 'w') as f:
                json.dump(stats, f)
        time.sleep(1)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    threading.Thread(target=save_stats, daemon=True).start()
    threading.Thread(target=http_server, daemon=True).start()
    threading.Thread(target=dns_forwarder, daemon=True).start()
    print("[NET] HTTP + DNS servers started")
    threading.Event().wait()
