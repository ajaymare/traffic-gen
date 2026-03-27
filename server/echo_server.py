import socket
import threading
import signal
import sys


def tcp_echo_server(port=9999):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('0.0.0.0', port))
    srv.listen(100)
    print(f"[TCP] Echo server on port {port}")

    def handle(conn, addr):
        try:
            while True:
                data = conn.recv(65536)
                if not data:
                    break
                conn.sendall(data)
        except Exception:
            pass
        finally:
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
        srv.sendto(data, addr)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    threading.Thread(target=tcp_echo_server, daemon=True).start()
    threading.Thread(target=udp_echo_server, daemon=True).start()
    print("[NET] Echo servers started")
    threading.Event().wait()
