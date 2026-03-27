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
