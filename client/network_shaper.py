"""
Network shaper using Linux tc/netem for latency, packet loss, and bandwidth control.
Requires NET_ADMIN capability.
"""
import random
import subprocess
import logging
import threading
import time

logger = logging.getLogger(__name__)

_random_bw_running = False
_random_bw_thread = None
_random_bw_lock = threading.Lock()

INTERFACE = 'eth0'


def _run(cmd):
    logger.info(f"tc cmd: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.warning(f"tc failed: {result.stderr.strip()}")
    return result.returncode == 0, result.stdout + result.stderr


def get_current_settings():
    ok, output = _run(f'tc qdisc show dev {INTERFACE}')
    return output if ok else "No settings applied"


def clear_all():
    _run(f'tc qdisc del dev {INTERFACE} root 2>/dev/null')
    logger.info("Cleared all shaping rules")
    return True


def apply_shaping(latency_ms=0, jitter_ms=0, packet_loss_pct=0, bandwidth_mbps=0):
    """Apply network impairment on egress."""
    clear_all()

    netem_parts = []
    if latency_ms > 0:
        s = f'delay {latency_ms}ms'
        if jitter_ms > 0:
            s += f' {jitter_ms}ms distribution normal'
        netem_parts.append(s)
    if packet_loss_pct > 0:
        netem_parts.append(f'loss {packet_loss_pct}%')

    has_netem = len(netem_parts) > 0
    has_bw = bandwidth_mbps > 0

    if has_bw and has_netem:
        _run(f'tc qdisc add dev {INTERFACE} root handle 1: htb default 10')
        _run(f'tc class add dev {INTERFACE} parent 1: classid 1:10 htb '
             f'rate {bandwidth_mbps}mbit ceil {bandwidth_mbps}mbit')
        _run(f'tc qdisc add dev {INTERFACE} parent 1:10 handle 10: netem {" ".join(netem_parts)}')
    elif has_bw:
        _run(f'tc qdisc add dev {INTERFACE} root handle 1: htb default 10')
        _run(f'tc class add dev {INTERFACE} parent 1: classid 1:10 htb '
             f'rate {bandwidth_mbps}mbit ceil {bandwidth_mbps}mbit')
    elif has_netem:
        _run(f'tc qdisc add dev {INTERFACE} root netem {" ".join(netem_parts)}')
    else:
        logger.info("No shaping parameters — traffic unimpaired")
        return True

    logger.info(f"Applied: latency={latency_ms}ms jitter={jitter_ms}ms "
                f"loss={packet_loss_pct}% bw={bandwidth_mbps}Mbps")
    return True


def start_random_bandwidth(min_mbps=20, max_mbps=1000, interval=10):
    """Cycle bandwidth randomly between min and max every interval seconds."""
    global _random_bw_running, _random_bw_thread
    with _random_bw_lock:
        if _random_bw_running:
            return False
        _random_bw_running = True

    def _loop():
        global _random_bw_running
        logger.info(f"Random bandwidth started: {min_mbps}-{max_mbps} Mbps every {interval}s")
        while _random_bw_running:
            bw = random.randint(min_mbps, max_mbps)
            clear_all()
            _run(f'tc qdisc add dev {INTERFACE} root handle 1: htb default 10')
            _run(f'tc class add dev {INTERFACE} parent 1: classid 1:10 htb '
                 f'rate {bw}mbit ceil {bw}mbit')
            logger.info(f"Random bandwidth set to {bw} Mbps")
            time.sleep(interval)
        clear_all()
        logger.info("Random bandwidth stopped")

    _random_bw_thread = threading.Thread(target=_loop, daemon=True)
    _random_bw_thread.start()
    return True


def stop_random_bandwidth():
    global _random_bw_running
    with _random_bw_lock:
        _random_bw_running = False
    return True


def is_random_bandwidth_running():
    return _random_bw_running


# ─── Source IP Aliases ──────────────────────────────────────

_alias_ips = []
_alias_lock = threading.Lock()


def _get_subnet_prefix():
    """Detect the subnet prefix length from the interface."""
    try:
        result = subprocess.run(
            f'ip -4 addr show dev {INTERFACE}',
            shell=True, capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'inet ' in line:
                # e.g. "inet 172.18.0.2/16 ..."
                parts = line.strip().split()
                addr_cidr = parts[1]  # 172.18.0.2/16
                return addr_cidr.split('/')[1]
    except Exception:
        pass
    return '24'


def add_ip_aliases(base_ip, count):
    """Add IP aliases to the interface.

    base_ip: starting IP, e.g. '172.18.0.100'
    count: number of aliases to add
    """
    global _alias_ips
    remove_ip_aliases()

    prefix = _get_subnet_prefix()
    parts = base_ip.split('.')
    base_last = int(parts[3])
    base_prefix = '.'.join(parts[:3])
    added = []

    for i in range(count):
        last_octet = base_last + i
        if last_octet > 254:
            break
        ip = f'{base_prefix}.{last_octet}'
        ok, _ = _run(f'ip addr add {ip}/{prefix} dev {INTERFACE}')
        if ok:
            added.append(ip)
            logger.info(f"Added alias IP {ip}/{prefix}")

    with _alias_lock:
        _alias_ips = added

    logger.info(f"Added {len(added)} IP aliases ({added[0]}-{added[-1]})" if added else "No aliases added")
    return added


def remove_ip_aliases():
    """Remove all previously added IP aliases."""
    global _alias_ips
    with _alias_lock:
        for ip in _alias_ips:
            _run(f'ip addr del {ip}/{_get_subnet_prefix()} dev {INTERFACE}')
            logger.info(f"Removed alias IP {ip}")
        _alias_ips = []


def get_alias_ips():
    """Return list of active alias IPs."""
    with _alias_lock:
        return list(_alias_ips)


def get_random_source_ip():
    """Return a random alias IP, or None if no aliases configured."""
    with _alias_lock:
        if _alias_ips:
            return random.choice(_alias_ips)
    return None
