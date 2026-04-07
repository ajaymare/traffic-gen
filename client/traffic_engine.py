"""
Traffic engine — protocol handlers for HTTP/HTTPS, TCP, UDP, FTP, SSH, ICMP.
Each job runs in a background thread with a configurable duration.
"""
import os
import time
import random
import socket
import struct
import ftplib
import logging
import threading
import subprocess
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
import httpx
import paramiko
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

# DSCP name → value mapping
DSCP_VALUES = {
    'BE': 0, 'CS1': 8, 'AF11': 10, 'AF12': 12, 'AF13': 14,
    'CS2': 16, 'AF21': 18, 'AF22': 20, 'AF23': 22,
    'CS3': 24, 'AF31': 26, 'AF32': 28, 'AF33': 30,
    'CS4': 32, 'AF41': 34, 'AF42': 36, 'AF43': 38,
    'CS5': 40, 'VA': 44, 'EF': 46, 'CS6': 48, 'CS7': 56,
}


def _dscp_to_tos(dscp):
    """Convert DSCP value or name to TOS byte. DSCP occupies upper 6 bits."""
    if isinstance(dscp, str):
        dscp = DSCP_VALUES.get(dscp.upper(), int(dscp) if dscp.isdigit() else 0)
    return int(dscp) << 2


def _set_tos(sock, tos):
    """Set IP_TOS on a socket."""
    if tos > 0:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, tos)


class DscpHTTPAdapter(HTTPAdapter):
    """HTTPAdapter that sets IP_TOS/DSCP on the underlying socket."""

    def __init__(self, tos=0, **kwargs):
        self.tos = tos
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        if self.tos > 0:
            kwargs['socket_options'] = [
                (socket.IPPROTO_IP, socket.IP_TOS, self.tos),
                (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
            ]
        super().init_poolmanager(*args, **kwargs)


def _random_xff():
    """Return an alias source IP if configured, otherwise a random IP."""
    import network_shaper
    alias_ip = network_shaper.get_random_source_ip()
    if alias_ip:
        return alias_ip
    return f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


@dataclass
class TrafficJob:
    protocol: str
    thread: Optional[threading.Thread] = None
    running: bool = False
    start_time: float = 0
    duration: int = 0  # seconds, 0 = indefinite
    stats: dict = field(default_factory=lambda: {
        "bytes_sent": 0, "bytes_recv": 0, "requests": 0, "errors": 0})
    config: dict = field(default_factory=dict)
    logs: deque = field(default_factory=lambda: deque(maxlen=1000))

    def log(self, msg):
        ts = time.strftime('%H:%M:%S')
        entry = f"[{ts}] {msg}"
        self.logs.append(entry)
        logger.info(f"[{self.protocol}] {msg}")

    def should_stop(self):
        if not self.running:
            return True
        if self.duration > 0 and (time.time() - self.start_time) >= self.duration:
            self.running = False
            self.log(f"Duration {self.duration}s reached — stopping")
            return True
        return False

    def elapsed(self):
        return int(time.time() - self.start_time) if self.start_time else 0

    def remaining(self):
        if self.duration <= 0:
            return -1  # indefinite
        left = self.duration - self.elapsed()
        return max(0, left)


class TrafficEngine:
    def __init__(self):
        self.jobs: dict[str, TrafficJob] = {}
        self._lock = threading.Lock()

    def get_status(self):
        with self._lock:
            result = {}
            for proto, job in self.jobs.items():
                result[proto] = {
                    "running": job.running,
                    "stats": dict(job.stats),
                    "config": dict(job.config),
                    "logs": list(job.logs)[-50:],
                    "elapsed": job.elapsed(),
                    "remaining": job.remaining(),
                    "duration": job.duration,
                }
            return result

    def start_job(self, protocol, config):
        # Support flow IDs: "http_2" → handler "_run_http", job key "http_2"
        flow_id = config.pop('flow_id', None)
        job_key = f"{protocol}_{flow_id}" if flow_id else protocol

        with self._lock:
            if job_key in self.jobs and self.jobs[job_key].running:
                return False, f"{job_key} already running"

            duration = int(config.pop('duration', 0))
            job = TrafficJob(protocol=job_key, config=config,
                             duration=duration, start_time=time.time())
            job.running = True
            self.jobs[job_key] = job

        # Look up handler by base protocol name (strip _N suffix)
        handler = getattr(self, f'_run_{protocol}', None)
        if not handler:
            job.running = False
            return False, f"Unknown protocol: {protocol}"

        thread = threading.Thread(target=self._wrapped_run,
                                  args=(handler, job), daemon=True, name=f"traffic-{job_key}")
        job.thread = thread
        thread.start()
        dur_str = f" for {duration}s" if duration > 0 else " (indefinite)"
        label = f"{protocol} (flow {flow_id})" if flow_id else protocol
        return True, f"{label} started{dur_str}"

    def _get_timing(self, cfg):
        """Return (interval, burst_count, burst_pause) from config."""
        rate_pps = float(cfg.get('rate_pps', 0))
        if rate_pps > 0:
            interval = 1.0 / rate_pps
        else:
            interval = float(cfg.get('interval', 1))
        burst_enabled = cfg.get('burst_enabled', False)
        burst_count = int(cfg.get('burst_count', 5)) if burst_enabled else 1
        burst_pause = float(cfg.get('burst_pause', 2)) if burst_enabled else interval
        return interval, burst_count, burst_pause

    def _wrapped_run(self, handler, job):
        try:
            handler(job)
        except Exception as e:
            job.log(f"Fatal error: {e}")
            job.stats['errors'] += 1
        finally:
            job.running = False

    def stop_job(self, protocol):
        with self._lock:
            # Direct match (e.g., "http" or "http_2")
            if protocol in self.jobs and self.jobs[protocol].running:
                self.jobs[protocol].running = False
                return True, f"{protocol} stopping"
            # Stop all flows of a base protocol (e.g., "http" stops "http_1", "http_2")
            stopped = []
            for key, job in self.jobs.items():
                if key.startswith(protocol + '_') and job.running:
                    job.running = False
                    stopped.append(key)
            if stopped:
                return True, f"Stopping {', '.join(stopped)}"
            return False, f"{protocol} not running"

    def stop_all(self):
        with self._lock:
            for job in self.jobs.values():
                job.running = False

    # ─── HTTP / HTTPS ───────────────────────────────────────

    def _run_https(self, job: TrafficJob):
        cfg = job.config
        url = cfg.get('url', 'https://server/')
        if not url.startswith('https'):
            url = url.replace('http://', 'https://')
        method = cfg.get('method', 'GET').upper()
        interval, burst_count, burst_pause = self._get_timing(cfg)
        verify_ssl = not cfg.get('ignore_ssl', False)
        data_size_kb = int(cfg.get('data_size_kb', 0))
        upload = cfg.get('upload', False)
        random_size = cfg.get('random_size', False)
        use_http2 = cfg.get('http2', False)
        dscp = cfg.get('dscp', 'BE')
        tos = _dscp_to_tos(dscp)

        proto_label = "HTTP/2" if use_http2 else "HTTPS"
        burst_str = f" burst={burst_count}x pause={burst_pause}s" if burst_count > 1 else ""
        job.log(f"{proto_label} {method} {url} interval={interval:.3f}s{burst_str} DSCP={dscp}(TOS={tos})")

        if use_http2:
            sock_opts = []
            if tos > 0:
                sock_opts = [(socket.IPPROTO_IP, socket.IP_TOS, tos)]
            client = httpx.Client(http2=True, verify=verify_ssl, timeout=60,
                                  transport=httpx.HTTPTransport(socket_options=sock_opts) if sock_opts else None)
            try:
                while not job.should_stop():
                    for _ in range(burst_count):
                        if job.should_stop():
                            break
                        sent_bytes = 0
                        recv_bytes = 0
                        req_url = url
                        try:
                            cur_size_kb = random.randint(1, max(data_size_kb, 1024)) if random_size else data_size_kb
                            headers = {'X-Forwarded-For': _random_xff()}

                            if upload and cur_size_kb > 0:
                                data = os.urandom(cur_size_kb * 1024)
                                resp = client.post(url, content=data, headers=headers)
                                sent_bytes = len(data)
                                recv_bytes = len(resp.content)
                                job.stats['bytes_sent'] += sent_bytes
                            elif method == 'GET':
                                if random_size:
                                    rand_mb = random.randint(1, 100)
                                    base = url.rsplit('/generate/', 1)[0] if '/generate/' in url else url.rstrip('/')
                                    req_url = f"{base}/generate/{rand_mb}"
                                resp = client.get(req_url, headers=headers)
                                recv_bytes = len(resp.content)
                                job.stats['bytes_recv'] += recv_bytes
                            else:
                                data = os.urandom(cur_size_kb * 1024) if cur_size_kb > 0 else b''
                                resp = client.request(method, url, content=data, headers=headers)
                                sent_bytes = len(data)
                                recv_bytes = len(resp.content)
                                job.stats['bytes_sent'] += sent_bytes
                                job.stats['bytes_recv'] += recv_bytes

                            job.stats['requests'] += 1
                            job.log(f"{method} {req_url} → {resp.status_code} ({resp.http_version}) | sent={sent_bytes}B recv={recv_bytes}B")
                        except Exception as e:
                            job.stats['errors'] += 1
                            job.log(f"Error: {req_url} — {e}")

                        if burst_count == 1:
                            time.sleep(interval)
                    if burst_count > 1:
                        job.log(f"Burst of {burst_count} complete, pausing {burst_pause}s")
                        time.sleep(burst_pause)
            finally:
                client.close()
        else:
            session = requests.Session()
            if tos > 0:
                adapter = DscpHTTPAdapter(tos=tos)
                session.mount('https://', adapter)

            while not job.should_stop():
                for _ in range(burst_count):
                    if job.should_stop():
                        break
                    sent_bytes = 0
                    recv_bytes = 0
                    req_url = url
                    try:
                        cur_size_kb = random.randint(1, max(data_size_kb, 1024)) if random_size else data_size_kb
                        headers = {'X-Forwarded-For': _random_xff()}

                        if upload and cur_size_kb > 0:
                            data = os.urandom(cur_size_kb * 1024)
                            resp = session.post(url, data=data, headers=headers, verify=verify_ssl, timeout=30)
                            sent_bytes = len(data)
                            recv_bytes = len(resp.content)
                            job.stats['bytes_sent'] += sent_bytes
                        elif method == 'GET':
                            if random_size:
                                rand_mb = random.randint(1, 100)
                                base = url.rsplit('/generate/', 1)[0] if '/generate/' in url else url.rstrip('/')
                                req_url = f"{base}/generate/{rand_mb}"
                            resp = session.get(req_url, headers=headers, verify=verify_ssl, timeout=60, stream=True)
                            recv_bytes = len(resp.content)
                            job.stats['bytes_recv'] += recv_bytes
                        else:
                            data = os.urandom(cur_size_kb * 1024) if cur_size_kb > 0 else b''
                            resp = session.request(method, url, data=data, headers=headers, verify=verify_ssl, timeout=30)
                            sent_bytes = len(data)
                            recv_bytes = len(resp.content)
                            job.stats['bytes_sent'] += sent_bytes
                            job.stats['bytes_recv'] += recv_bytes

                        job.stats['requests'] += 1
                        job.log(f"{method} {req_url} → {resp.status_code} | sent={sent_bytes}B recv={recv_bytes}B")
                    except Exception as e:
                        job.stats['errors'] += 1
                        job.log(f"Error: {req_url} — {e}")

                    if burst_count == 1:
                        time.sleep(interval)
                if burst_count > 1:
                    job.log(f"Burst of {burst_count} complete, pausing {burst_pause}s")
                    time.sleep(burst_pause)
        job.log("Stopped")

    # ─── HTTP Plain (port 9999) ────────────────────────────

    def _run_http_plain(self, job: TrafficJob):
        """HTTP requests to the plain HTTP server on port 9999 (App-ID: web-browsing)."""
        cfg = job.config
        host = cfg.get('host', 'server')
        port = int(cfg.get('port', 9999))
        method = cfg.get('method', 'GET').upper()
        data_size_kb = int(cfg.get('data_size_kb', 1))
        interval, burst_count, burst_pause = self._get_timing(cfg)
        random_size = cfg.get('random_size', False)
        dscp = cfg.get('dscp', 'BE')
        tos = _dscp_to_tos(dscp)

        base_url = f"http://{host}:{port}"
        burst_str = f" burst={burst_count}x pause={burst_pause}s" if burst_count > 1 else ""
        job.log(f"HTTP {method} {base_url} data_size={data_size_kb}KB interval={interval:.3f}s{burst_str} DSCP={dscp}(TOS={tos})")

        session = requests.Session()
        if tos > 0:
            adapter = DscpHTTPAdapter(tos=tos)
            session.mount('http://', adapter)

        while not job.should_stop():
            for _ in range(burst_count):
                if job.should_stop():
                    break
                sent_bytes = 0
                recv_bytes = 0
                try:
                    cur_size_kb = random.randint(1, max(data_size_kb, 100)) if random_size else data_size_kb
                    headers = {'X-Forwarded-For': _random_xff()}

                    if method == 'POST':
                        data = os.urandom(cur_size_kb * 1024)
                        resp = session.post(f"{base_url}/upload", data=data, headers=headers, timeout=30)
                        sent_bytes = len(data)
                        recv_bytes = len(resp.content)
                        job.stats['bytes_sent'] += sent_bytes
                    elif method == 'GET' and cur_size_kb > 0:
                        resp = session.get(f"{base_url}/download?size={cur_size_kb}", headers=headers, timeout=60)
                        recv_bytes = len(resp.content)
                    else:
                        resp = session.get(base_url, headers=headers, timeout=30)
                        recv_bytes = len(resp.content)

                    job.stats['bytes_recv'] += recv_bytes
                    job.stats['requests'] += 1
                    job.log(f"HTTP {method} {base_url} → {resp.status_code} | sent={sent_bytes}B recv={recv_bytes}B")
                except Exception as e:
                    job.stats['errors'] += 1
                    job.log(f"HTTP error: {base_url} — {e}")

                if burst_count == 1:
                    time.sleep(interval)
            if burst_count > 1:
                job.log(f"Burst of {burst_count} complete, pausing {burst_pause}s")
                time.sleep(burst_pause)
        job.log("Stopped")

    # ─── DNS (port 9998) ────────────────────────────────────

    def _run_dns(self, job: TrafficJob):
        """Send DNS A-record queries to the DNS forwarder on port 9998 (App-ID: dns)."""
        cfg = job.config
        host = cfg.get('host', 'server')
        port = int(cfg.get('port', 9998))
        domains_raw = cfg.get('domains', 'google.com\namazon.com\nmicrosoft.com\ngithub.com\ncloudflare.com')
        domains = [d.strip() for d in domains_raw.replace(',', '\n').split('\n') if d.strip()]
        if not domains:
            domains = ['google.com']
        interval, burst_count, burst_pause = self._get_timing(cfg)
        dscp = cfg.get('dscp', 'BE')
        tos = _dscp_to_tos(dscp)

        burst_str = f" burst={burst_count}x pause={burst_pause}s" if burst_count > 1 else ""
        job.log(f"DNS queries → {host}:{port} domains={len(domains)} interval={interval:.3f}s{burst_str} DSCP={dscp}(TOS={tos})")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        _set_tos(sock, tos)

        domain_idx = 0
        while not job.should_stop():
            for _ in range(burst_count):
                if job.should_stop():
                    break
                domain = domains[domain_idx % len(domains)]
                domain_idx += 1
                try:
                    # Build DNS A-record query packet
                    query = self._build_dns_query(domain)
                    sock.sendto(query, (host, port))
                    job.stats['bytes_sent'] += len(query)
                    resp, _ = sock.recvfrom(4096)
                    job.stats['bytes_recv'] += len(resp)
                    job.stats['requests'] += 1
                    # Parse response for answer count
                    ans_count = struct.unpack('!H', resp[6:8])[0] if len(resp) >= 8 else 0
                    job.log(f"DNS {domain} → {host}:{port} | sent={len(query)}B recv={len(resp)}B answers={ans_count}")
                except socket.timeout:
                    job.stats['errors'] += 1
                    job.log(f"DNS {domain} → {host}:{port} | timeout")
                except Exception as e:
                    job.stats['errors'] += 1
                    job.log(f"DNS error: {domain} — {e}")
                if burst_count == 1:
                    time.sleep(interval)
            if burst_count > 1:
                job.log(f"Burst of {burst_count} complete, pausing {burst_pause}s")
                time.sleep(burst_pause)

        sock.close()
        job.log("Stopped")

    @staticmethod
    def _build_dns_query(domain):
        """Build a minimal DNS A-record query packet."""
        import struct as st
        txn_id = random.randint(0, 0xFFFF)
        flags = 0x0100  # standard query, recursion desired
        header = st.pack('!HHHHHH', txn_id, flags, 1, 0, 0, 0)
        # Encode QNAME
        qname = b''
        for label in domain.split('.'):
            qname += bytes([len(label)]) + label.encode('ascii')
        qname += b'\x00'
        # QTYPE=A (1), QCLASS=IN (1)
        question = qname + st.pack('!HH', 1, 1)
        return header + question

    # ─── iperf3 ───────────────────────────────────────────

    def _run_iperf(self, job: TrafficJob):
        cfg = job.config
        host = cfg.get('host', 'server')
        port = int(cfg.get('port', 5201))
        proto = cfg.get('protocol', 'TCP').lower()
        bandwidth = cfg.get('bandwidth', '100M')
        parallel = int(cfg.get('parallel', 1))
        reverse = cfg.get('reverse', False)
        dscp = cfg.get('dscp', 'BE')
        tos = _dscp_to_tos(dscp)
        duration = job.duration if job.duration > 0 else 3600

        cmd = ['iperf3', '-c', host, '-p', str(port), '-b', bandwidth,
               '-t', str(duration), '-P', str(parallel)]
        if proto == 'udp':
            cmd.append('-u')
        if reverse:
            cmd.append('-R')
        if tos > 0:
            cmd.extend(['-S', str(tos)])

        job.log(f"iperf3 {proto.upper()} → {host}:{port} bw={bandwidth} "
                f"parallel={parallel} reverse={reverse} duration={duration}s")

        retries = 0
        max_retries = 5
        while not job.should_stop():
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                # Stream stdout lines in real-time for live activity logs
                while not job.should_stop() and proc.poll() is None:
                    line = proc.stdout.readline()
                    if line:
                        stripped = line.strip()
                        # Log interval lines (contain transfer stats) and summary
                        if stripped and ('sec' in stripped or 'sender' in stripped or 'receiver' in stripped):
                            job.log(f"iperf3 :{port} | {stripped}")
                            retries = 0  # reset on successful data
                    else:
                        time.sleep(0.5)
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=5)
                # Read any remaining output
                remaining = proc.stdout.read()
                stderr = proc.stderr.read()

                if remaining:
                    for line in remaining.split('\n'):
                        stripped = line.strip()
                        if stripped and ('sec' in stripped or 'sender' in stripped or 'receiver' in stripped):
                            job.log(f"iperf3 :{port} | {stripped}")

                # On transient errors, retry same port after brief wait
                if proc.returncode != 0 and stderr:
                    err_lower = stderr.lower()
                    if any(s in err_lower for s in ['server is busy', 'control socket has closed',
                            'unable to receive parameters', 'server side protocol']):
                        retries += 1
                        if retries > max_retries:
                            job.log(f"iperf3 :{port} — too many retries, giving up")
                            break
                        job.log(f"iperf3 :{port} — server busy, retrying in 3s ({retries}/{max_retries})")
                        time.sleep(3)
                        continue
                    elif any(s in err_lower for s in ['connection refused', 'unable to connect', 'no route to host']):
                        job.log(f"iperf3 :{port} — cannot reach server ({stderr.strip()[:80]})")
                        break
                    job.log(f"iperf3 :{port} error: {stderr[:300]}")

                job.log(f"iperf3 done on port {port} (exit={proc.returncode})")
                break
            except Exception as e:
                job.stats['errors'] += 1
                job.log(f"iperf3 error on port {port}: {e}")
                break

        job.log("Stopped")


    # ─── FTP ────────────────────────────────────────────────

    def _run_ftp(self, job: TrafficJob):
        cfg = job.config
        host = cfg.get('host', 'server')
        port = int(cfg.get('port', 21))
        username = cfg.get('username', 'anonymous')
        password = cfg.get('password', '')
        filename = cfg.get('filename', 'testfile_100mb.bin')
        random_size = cfg.get('random_size', False)
        dscp = cfg.get('dscp', 'BE')
        tos = _dscp_to_tos(dscp)
        ftp_files = ['testfile_100mb.bin']

        job.log(f"FTP continuous download from {host}:{port} random_size={random_size} DSCP={dscp}(TOS={tos})")

        while not job.should_stop():
            try:
                ftp = ftplib.FTP()
                ftp.connect(host, port, timeout=30)
                if tos > 0:
                    _set_tos(ftp.sock, tos)
                ftp.login(username, password)
                ftp.set_pasv(True)

                cur_file = random.choice(ftp_files) if random_size else filename
                size = ftp.size(cur_file) or 0
                job.log(f"Connected — downloading {cur_file} ({size} bytes)")

                bytes_recv = 0
                last_log_bytes = 0
                LOG_INTERVAL = 1024 * 1024  # log every 1MB

                def callback(data):
                    nonlocal bytes_recv, last_log_bytes
                    if job.should_stop():
                        raise StopIteration("Duration reached")
                    bytes_recv += len(data)
                    job.stats['bytes_recv'] += len(data)
                    if bytes_recv - last_log_bytes >= LOG_INTERVAL:
                        pct = f" ({bytes_recv * 100 // size}%)" if size > 0 else ""
                        job.log(f"FTP {cur_file} ← recv={bytes_recv}B{pct}")
                        last_log_bytes = bytes_recv

                try:
                    ftp.retrbinary(f'RETR {cur_file}', callback, blocksize=65536)
                except StopIteration:
                    pass

                job.stats['requests'] += 1
                job.log(f"FTP {cur_file} ← download complete: {bytes_recv}B")
                ftp.quit()
            except StopIteration:
                break
            except Exception as e:
                job.stats['errors'] += 1
                job.log(f"FTP error: {e}")
                time.sleep(2)

            if not job.should_stop():
                job.log("Restarting download (continuous)")
                time.sleep(0.5)

        job.log("Stopped")

    # ─── SSH ────────────────────────────────────────────────

    def _run_ssh(self, job: TrafficJob):
        cfg = job.config
        host = cfg.get('host', 'server')
        port = int(cfg.get('port', 2222))
        username = cfg.get('username', 'testuser')
        password = cfg.get('password', 'testpass')
        command = cfg.get('command', 'uptime')
        interval, burst_count, burst_pause = self._get_timing(cfg)
        dscp = cfg.get('dscp', 'BE')
        tos = _dscp_to_tos(dscp)

        burst_str = f" burst={burst_count}x pause={burst_pause}s" if burst_count > 1 else ""
        job.log(f"SSH {username}@{host}:{port} cmd='{command}' interval={interval:.3f}s{burst_str} DSCP={dscp}(TOS={tos})")

        client = None
        while not job.should_stop():
            # Establish/re-establish persistent connection
            if client is None:
                try:
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    client.connect(host, port=port, username=username,
                                   password=password, timeout=10,
                                   banner_timeout=15,
                                   allow_agent=False, look_for_keys=False)
                    transport = client.get_transport()
                    if transport and tos > 0:
                        try:
                            _set_tos(transport.sock, tos)
                        except Exception:
                            pass
                    job.log(f"SSH connected to {host}:{port}")
                except Exception as e:
                    job.stats['errors'] += 1
                    job.log(f"SSH connect error: {username}@{host}:{port} — {e}")
                    client = None
                    time.sleep(3)
                    continue

            for _ in range(burst_count):
                if job.should_stop():
                    break
                try:
                    # Check if transport is still active
                    transport = client.get_transport()
                    if not transport or not transport.is_active():
                        raise EOFError("Connection lost")
                    stdin, stdout, stderr = client.exec_command(command, timeout=10)
                    out = stdout.read().decode().strip()
                    err = stderr.read().decode().strip()
                    exit_code = stdout.channel.recv_exit_status()
                    job.stats['requests'] += 1
                    job.stats['bytes_recv'] += len(out)
                    job.log(f"SSH {username}@{host} $ {command} → exit={exit_code} | recv={len(out)}B | {out[:150]}")
                    if err:
                        job.log(f"SSH stderr: {err[:200]}")
                except Exception as e:
                    job.stats['errors'] += 1
                    job.log(f"SSH error: {username}@{host}:{port} — {e}")
                    # Close broken connection, will reconnect on next loop
                    try:
                        client.close()
                    except Exception:
                        pass
                    client = None
                    time.sleep(2)
                    break
                if burst_count == 1:
                    time.sleep(interval)
            if burst_count > 1:
                job.log(f"Burst of {burst_count} complete, pausing {burst_pause}s")
                time.sleep(burst_pause)

        if client:
            try:
                client.close()
            except Exception:
                pass
        job.log("Stopped")

    # ─── External HTTPS ────────────────────────────────────

    def _run_ext_https(self, job: TrafficJob):
        cfg = job.config
        # Support multi-URL: 'urls' textarea (newline/comma separated) or legacy 'url' field
        raw = cfg.get('urls', cfg.get('url', 'https://www.google.com'))
        urls = [u.strip() for u in raw.replace(',', '\n').split('\n') if u.strip()]
        if not urls:
            job.log("No URLs configured")
            return
        method = cfg.get('method', 'GET').upper()
        interval, burst_count, burst_pause = self._get_timing(cfg)
        verify_ssl = not cfg.get('ignore_ssl', False)
        dscp = cfg.get('dscp', 'BE')
        tos = _dscp_to_tos(dscp)

        burst_str = f" burst={burst_count}x pause={burst_pause}s" if burst_count > 1 else ""
        job.log(f"External HTTPS {method} → {len(urls)} URL(s) interval={interval:.3f}s{burst_str} DSCP={dscp}(TOS={tos})")
        for i, u in enumerate(urls):
            job.log(f"  URL[{i}]: {u}")

        session = requests.Session()
        if tos > 0:
            adapter = DscpHTTPAdapter(tos=tos)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

        url_index = 0
        while not job.should_stop():
            for _ in range(burst_count):
                if job.should_stop():
                    break
                url = urls[url_index % len(urls)]
                url_index += 1
                try:
                    headers = {'X-Forwarded-For': _random_xff()}
                    if method == 'GET':
                        resp = session.get(url, headers=headers, verify=verify_ssl, timeout=30)
                    else:
                        resp = session.request(method, url, headers=headers, verify=verify_ssl, timeout=30)
                    job.stats['bytes_recv'] += len(resp.content)
                    job.stats['requests'] += 1
                    job.log(f"{method} {resp.status_code} — {len(resp.content)}B ({url})")
                except Exception as e:
                    job.stats['errors'] += 1
                    job.log(f"Error: {url} — {e}")
                if burst_count == 1:
                    time.sleep(interval)
            if burst_count > 1:
                job.log(f"Burst of {burst_count} complete, pausing {burst_pause}s")
                time.sleep(burst_pause)
        job.log("Stopped")

    # ─── hping3 ─────────────────────────────────────────────

    def _run_hping3(self, job: TrafficJob):
        cfg = job.config
        host = cfg.get('host', 'server')
        mode = cfg.get('mode', 'ICMP')
        port = int(cfg.get('port', 0))
        packet_size = int(cfg.get('packet_size', 64))
        count = int(cfg.get('count', 0))
        interval_cfg = float(cfg.get('interval', 1))
        flood = cfg.get('flood', False)
        ttl = int(cfg.get('ttl', 64))
        dscp = cfg.get('dscp', 'BE')
        tos = _dscp_to_tos(dscp)

        # hping3 requires raw sockets — must run via sudo
        import network_shaper
        sudo_pw = None
        with network_shaper._sudo_lock:
            sudo_pw = network_shaper._sudo_password
        if not sudo_pw:
            job.log("hping3 requires sudo — authenticate first in Link Simulation")
            job.stats['errors'] += 1
            return

        cmd = ['sudo', '-S', 'hping3', host, '--ttl', str(ttl), '-d', str(packet_size)]

        # Mode flags
        mode_map = {
            'ICMP': ['--icmp'],
            'TCP SYN': ['-S', '-p', str(port or 80)],
            'TCP ACK': ['-A', '-p', str(port or 80)],
            'TCP FIN': ['-F', '-p', str(port or 80)],
            'UDP': ['--udp', '-p', str(port or 53)],
            'Traceroute': ['--traceroute', '--icmp'],
        }
        cmd.extend(mode_map.get(mode, ['--icmp']))

        if tos > 0:
            cmd.extend(['--tos', str(tos)])

        if flood:
            cmd.append('--flood')
        else:
            # hping3 interval is in microseconds with -i, or use -i uN
            interval_us = int(interval_cfg * 1000000)
            cmd.extend(['-i', f'u{interval_us}'])

        if count > 0:
            cmd.extend(['-c', str(count)])

        mode_str = f"{mode} port={port}" if 'TCP' in mode or mode == 'UDP' else mode
        job.log(f"hping3 {host} mode={mode_str} size={packet_size} ttl={ttl} "
                f"flood={flood} DSCP={dscp}(TOS={tos})")

        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            proc.stdin.write(sudo_pw + '\n')
            proc.stdin.flush()
            while not job.should_stop() and proc.poll() is None:
                line = proc.stdout.readline()
                if line:
                    stripped = line.strip()
                    if stripped and '[sudo]' not in stripped:
                        job.stats['requests'] += 1
                        job.stats['bytes_sent'] += packet_size
                        if 'rtt=' in stripped or 'flags=' in stripped or 'ip=' in stripped:
                            job.stats['bytes_recv'] += packet_size
                        job.log(f"hping3 {host} → {stripped}")
                else:
                    time.sleep(0.1)
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=5)
            # Read remaining output
            remaining = proc.stdout.read()
            if remaining:
                for line in remaining.strip().split('\n'):
                    if line.strip() and '[sudo]' not in line:
                        job.log(f"hping3 {host} → {line.strip()}")
        except Exception as e:
            job.stats['errors'] += 1
            job.log(f"hping3 error: {e}")

        job.log("Stopped")
