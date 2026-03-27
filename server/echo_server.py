import json
import socket
import threading
import signal
import sys
import time

STATS_FILE = '/tmp/echo_stats.json'
stats_lock = threading.Lock()
stats = {
    'tcp': {'connections': 0, 'active': 0, 'bytes_recv': 0, 'bytes_sent': 0},
    'udp': {'packets': 0, 'bytes_recv': 0, 'bytes_sent': 0},
}


def save_stats():
    while True:
        with stats_lock:
            with open(STATS_FILE, 'w') as f:
                json.dump(stats, f)
        time.sleep(1)


def tcp_echo_server(port=9999):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('0.0.0.0', port))
    srv.listen(100)
    print(f"[TCP] Echo server on port {port}")

    def handle(conn, addr):
        with stats_lock:
            stats['tcp']['connections'] += 1
            stats['tcp']['active'] += 1
        try:
            while True:
                data = conn.recv(65536)
                if not data:
                    break
                with stats_lock:
                    stats['tcp']['bytes_recv'] += len(data)
                    stats['tcp']['bytes_sent'] += len(data)
                conn.sendall(data)
        except Exception:
            pass
        finally:
            with stats_lock:
                stats['tcp']['active'] -= 1
            conn.close()

    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()


def udp_echo_server(port=9998):
    srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    srv.bind(('0.0.0.0', port))
    print(f"[UDP] Echo server on port {port}")
    while True:
        data, addr = srv.recvfrom(65536)
        with stats_lock:
            stats['udp']['packets'] += 1
            stats['udp']['bytes_recv'] += len(data)
            stats['udp']['bytes_sent'] += len(data)
        srv.sendto(data, addr)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    threading.Thread(target=save_stats, daemon=True).start()
    threading.Thread(target=tcp_echo_server, daemon=True).start()
    threading.Thread(target=udp_echo_server, daemon=True).start()
    print("[NET] Echo servers started")
    threading.Event().wait()
