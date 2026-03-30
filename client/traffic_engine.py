"""
Traffic engine — protocol handlers for HTTP/HTTPS, TCP, UDP, FTP, SSH, ICMP.
Each job runs in a background thread with a configurable duration.
"""
import os
import time
import random
import socket
import ftplib
import logging
import threading
import subprocess
from dataclasses import dataclass, field
from typing import Optional

import requests
import httpx
import paramiko
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)


def _random_xff():
    """Generate a random X-Forwarded-For IP address."""
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
    logs: list = field(default_factory=list)

    def log(self, msg):
        ts = time.strftime('%H:%M:%S')
        entry = f"[{ts}] {msg}"
        self.logs.append(entry)
        if len(self.logs) > 500:
            self.logs = self.logs[-250:]
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
                    "logs": job.logs[-30:],
                    "elapsed": job.elapsed(),
                    "remaining": job.remaining(),
                    "duration": job.duration,
                }
            return result

    def start_job(self, protocol, config):
        with self._lock:
            if protocol in self.jobs and self.jobs[protocol].running:
                return False, f"{protocol} already running"

            duration = int(config.pop('duration', 0))
            job = TrafficJob(protocol=protocol, config=config,
                             duration=duration, start_time=time.time())
            job.running = True
            self.jobs[protocol] = job

        handler = getattr(self, f'_run_{protocol}', None)
        if not handler:
            job.running = False
            return False, f"Unknown protocol: {protocol}"

        thread = threading.Thread(target=self._wrapped_run,
                                  args=(handler, job), daemon=True, name=f"traffic-{protocol}")
        job.thread = thread
        thread.start()
        dur_str = f" for {duration}s" if duration > 0 else " (indefinite)"
        return True, f"{protocol} started{dur_str}"

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
            if protocol not in self.jobs or not self.jobs[protocol].running:
                return False, f"{protocol} not running"
            self.jobs[protocol].running = False
        return True, f"{protocol} stopping"

    def stop_all(self):
        with self._lock:
            for job in self.jobs.values():
                job.running = False

    # ─── HTTP / HTTPS ───────────────────────────────────────

    def _run_http(self, job: TrafficJob):
        self._http_handler(job)

    def _run_https(self, job: TrafficJob):
        if 'url' not in job.config or not job.config['url'].startswith('https'):
            job.config['url'] = job.config.get('url', 'https://server/').replace('http://', 'https://')
        self._http_handler(job)

    def _http_handler(self, job: TrafficJob):
        cfg = job.config
        url = cfg.get('url', 'http://server/generate/100')
        method = cfg.get('method', 'GET').upper()
        interval = float(cfg.get('interval', 1))
        verify_ssl = not cfg.get('ignore_ssl', False)
        data_size_kb = int(cfg.get('data_size_kb', 0))
        upload = cfg.get('upload', False)
        random_size = cfg.get('random_size', False)

        job.log(f"{method} {url} interval={interval}s verify_ssl={verify_ssl} random_size={random_size}")

        session = requests.Session()

        while not job.should_stop():
            try:
                cur_size_kb = random.randint(1, max(data_size_kb, 1024)) if random_size else data_size_kb

                headers = {'X-Forwarded-For': _random_xff()}

                if upload and cur_size_kb > 0:
                    data = os.urandom(cur_size_kb * 1024)
                    resp = session.post(url, data=data, headers=headers, verify=verify_ssl, timeout=30)
                    job.stats['bytes_sent'] += len(data)
                elif method == 'GET':
                    if random_size:
                        rand_mb = random.randint(1, 100)
                        base = url.rsplit('/generate/', 1)[0] if '/generate/' in url else url.rstrip('/')
                        cur_url = f"{base}/generate/{rand_mb}"
                    else:
                        cur_url = url
                    resp = session.get(cur_url, headers=headers, verify=verify_ssl, timeout=60, stream=True)
                    content = resp.content
                    job.stats['bytes_recv'] += len(content)
                else:
                    data = os.urandom(cur_size_kb * 1024) if cur_size_kb > 0 else b''
                    resp = session.request(method, url, data=data, headers=headers, verify=verify_ssl, timeout=30)
                    job.stats['bytes_sent'] += len(data)
                    job.stats['bytes_recv'] += len(resp.content)

                job.stats['requests'] += 1
                job.log(f"{method} {resp.status_code} — {len(resp.content)} bytes")
            except Exception as e:
                job.stats['errors'] += 1
                job.log(f"Error: {e}")

            time.sleep(interval)
        job.log("Stopped")

    # ─── HTTP/2 ──────────────────────────────────────────────

    def _run_http2(self, job: TrafficJob):
        cfg = job.config
        url = cfg.get('url', 'https://server/')
        method = cfg.get('method', 'GET').upper()
        interval = float(cfg.get('interval', 1))
        verify_ssl = not cfg.get('ignore_ssl', False)
        data_size_kb = int(cfg.get('data_size_kb', 0))
        upload = cfg.get('upload', False)
        random_size = cfg.get('random_size', False)

        job.log(f"HTTP/2 {method} {url} interval={interval}s verify_ssl={verify_ssl} random_size={random_size}")

        client = httpx.Client(http2=True, verify=verify_ssl, timeout=60)

        while not job.should_stop():
            try:
                cur_size_kb = random.randint(1, max(data_size_kb, 1024)) if random_size else data_size_kb

                headers = {'X-Forwarded-For': _random_xff()}

                if upload and cur_size_kb > 0:
                    data = os.urandom(cur_size_kb * 1024)
                    resp = client.post(url, content=data, headers=headers)
                    job.stats['bytes_sent'] += len(data)
                elif method == 'GET':
                    if random_size:
                        rand_mb = random.randint(1, 100)
                        base = url.rsplit('/generate/', 1)[0] if '/generate/' in url else url.rstrip('/')
                        cur_url = f"{base}/generate/{rand_mb}"
                    else:
                        cur_url = url
                    resp = client.get(cur_url, headers=headers)
                    job.stats['bytes_recv'] += len(resp.content)
                else:
                    data = os.urandom(cur_size_kb * 1024) if cur_size_kb > 0 else b''
                    resp = client.request(method, url, content=data, headers=headers)
                    job.stats['bytes_sent'] += len(data)
                    job.stats['bytes_recv'] += len(resp.content)

                h2_used = resp.http_version == 'HTTP/2'
                job.stats['requests'] += 1
                job.log(f"{method} {resp.status_code} ({resp.http_version}) — {len(resp.content)} bytes")
            except Exception as e:
                job.stats['errors'] += 1
                job.log(f"Error: {e}")

            time.sleep(interval)

        client.close()
        job.log("Stopped")

    # ─── TCP ────────────────────────────────────────────────

    def _run_tcp(self, job: TrafficJob):
        cfg = job.config
        host = cfg.get('host', 'server')
        port = int(cfg.get('port', 9999))
        msg_size = int(cfg.get('msg_size', 1024))
        interval = float(cfg.get('interval', 0.5))
        random_size = cfg.get('random_size', False)

        if cfg.get('use_iperf', False):
            self._run_iperf(job, host, 'tcp')
            return

        job.log(f"TCP echo {host}:{port} msg_size={msg_size} random_size={random_size}")

        while not job.should_stop():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((host, port))
                job.log(f"Connected to {host}:{port}")

                while not job.should_stop():
                    cur_size = random.randint(64, max(msg_size, 65536)) if random_size else msg_size
                    data = os.urandom(cur_size)
                    sock.sendall(data)
                    job.stats['bytes_sent'] += len(data)
                    resp = sock.recv(65536)
                    job.stats['bytes_recv'] += len(resp)
                    job.stats['requests'] += 1
                    time.sleep(interval)

                sock.close()
            except Exception as e:
                job.stats['errors'] += 1
                job.log(f"TCP error: {e}")
                time.sleep(2)
        job.log("Stopped")

    # ─── UDP ────────────────────────────────────────────────

    def _run_udp(self, job: TrafficJob):
        cfg = job.config
        host = cfg.get('host', 'server')
        port = int(cfg.get('port', 9998))
        msg_size = int(cfg.get('msg_size', 1024))
        interval = float(cfg.get('interval', 0.5))
        random_size = cfg.get('random_size', False)

        if cfg.get('use_iperf', False):
            self._run_iperf(job, host, 'udp')
            return

        job.log(f"UDP echo {host}:{port} msg_size={msg_size} random_size={random_size}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)

        while not job.should_stop():
            try:
                cur_size = random.randint(64, max(msg_size, 65536)) if random_size else msg_size
                data = os.urandom(cur_size)
                sock.sendto(data, (host, port))
                job.stats['bytes_sent'] += len(data)
                resp, _ = sock.recvfrom(65536)
                job.stats['bytes_recv'] += len(resp)
                job.stats['requests'] += 1
            except socket.timeout:
                job.stats['errors'] += 1
            except Exception as e:
                job.stats['errors'] += 1
                job.log(f"UDP error: {e}")
            time.sleep(interval)

        sock.close()
        job.log("Stopped")

    # ─── iperf3 (dedicated protocols) ─────────────────────

    def _run_iperf_tcp(self, job: TrafficJob):
        self._run_iperf_full(job, 'tcp')

    def _run_iperf_udp(self, job: TrafficJob):
        self._run_iperf_full(job, 'udp')

    # ─── iperf3 helper ──────────────────────────────────────

    def _run_iperf_full(self, job, proto):
        cfg = job.config
        host = cfg.get('host', 'server')
        port = int(cfg.get('port', 5201))
        bandwidth = cfg.get('bandwidth', '100M')
        parallel = int(cfg.get('parallel', 1))
        reverse = cfg.get('reverse', False)
        duration = job.duration if job.duration > 0 else 3600

        cmd = ['iperf3', '-c', host, '-p', str(port), '-b', bandwidth,
               '-t', str(duration), '-P', str(parallel)]
        if proto == 'udp':
            cmd.append('-u')
        if reverse:
            cmd.append('-R')

        job.log(f"iperf3 {proto.upper()} → {host}:{port} bw={bandwidth} "
                f"parallel={parallel} reverse={reverse} duration={duration}s")

        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            while not job.should_stop() and proc.poll() is None:
                time.sleep(1)
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=5)
            stdout = proc.stdout.read()
            stderr = proc.stderr.read()
            job.log(f"iperf3 done (exit={proc.returncode})")
            if stdout:
                # Parse summary lines
                for line in stdout.split('\n'):
                    if 'sender' in line or 'receiver' in line or 'SUM' in line:
                        job.log(line.strip())
                if 'sender' not in stdout and 'receiver' not in stdout:
                    job.log(stdout[-500:])
            if stderr:
                job.log(f"stderr: {stderr[:300]}")
        except Exception as e:
            job.stats['errors'] += 1
            job.log(f"iperf3 error: {e}")
        job.log("Stopped")

    def _run_iperf(self, job, host, proto):
        """Legacy helper for TCP/UDP cards with use_iperf checkbox."""
        job.config['host'] = host
        self._run_iperf_full(job, proto)

    # ─── FTP ────────────────────────────────────────────────

    def _run_ftp(self, job: TrafficJob):
        cfg = job.config
        host = cfg.get('host', 'server')
        port = int(cfg.get('port', 21))
        username = cfg.get('username', 'anonymous')
        password = cfg.get('password', '')
        filename = cfg.get('filename', 'testfile_1gb.bin')
        random_size = cfg.get('random_size', False)
        ftp_files = ['testfile_100mb.bin', 'testfile_1gb.bin']

        job.log(f"FTP continuous download from {host}:{port} random_size={random_size}")

        while not job.should_stop():
            try:
                ftp = ftplib.FTP()
                ftp.connect(host, port, timeout=30)
                ftp.login(username, password)
                ftp.set_pasv(True)

                cur_file = random.choice(ftp_files) if random_size else filename
                size = ftp.size(cur_file) or 0
                job.log(f"Connected — downloading {cur_file} ({size} bytes)")

                bytes_recv = 0

                def callback(data):
                    nonlocal bytes_recv
                    if job.should_stop():
                        raise StopIteration("Duration reached")
                    bytes_recv += len(data)
                    job.stats['bytes_recv'] += len(data)

                try:
                    ftp.retrbinary(f'RETR {cur_file}', callback, blocksize=65536)
                except StopIteration:
                    pass

                job.stats['requests'] += 1
                job.log(f"Download pass complete: {bytes_recv} bytes")
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
        port = int(cfg.get('port', 22))
        username = cfg.get('username', 'testuser')
        password = cfg.get('password', 'testpass')
        command = cfg.get('command', 'uptime')
        interval = float(cfg.get('interval', 5))

        job.log(f"SSH {username}@{host}:{port} cmd='{command}' every {interval}s")

        while not job.should_stop():
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(host, port=port, username=username,
                               password=password, timeout=10,
                               allow_agent=False, look_for_keys=False)
                stdin, stdout, stderr = client.exec_command(command, timeout=10)
                out = stdout.read().decode().strip()
                err = stderr.read().decode().strip()
                job.stats['requests'] += 1
                job.stats['bytes_recv'] += len(out)
                job.log(f"Output: {out[:200]}")
                if err:
                    job.log(f"Stderr: {err[:200]}")
                client.close()
            except Exception as e:
                job.stats['errors'] += 1
                job.log(f"SSH error: {e}")
            time.sleep(interval)

        job.log("Stopped")

    # ─── ICMP ───────────────────────────────────────────────

    def _run_icmp(self, job: TrafficJob):
        cfg = job.config
        host = cfg.get('host', 'server')
        interval = float(cfg.get('interval', 1))
        packet_size = int(cfg.get('packet_size', 64))

        job.log(f"Ping {host} size={packet_size} interval={interval}s")

        while not job.should_stop():
            try:
                cmd = ['ping', '-c', '1', '-W', '3', '-s', str(packet_size), host]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                job.stats['requests'] += 1

                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'time=' in line:
                            job.log(line.strip())
                            break
                    job.stats['bytes_sent'] += packet_size
                    job.stats['bytes_recv'] += packet_size
                else:
                    job.stats['errors'] += 1
                    job.log(f"Ping failed: {result.stderr.strip()}")
            except Exception as e:
                job.stats['errors'] += 1
                job.log(f"Ping error: {e}")
            time.sleep(interval)

        job.log("Stopped")
