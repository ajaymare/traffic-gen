"""
Router-based link simulation via SSH.

Connects to Linux routers via SSH and applies tc/netem impairment rules
on selected interfaces. Supports multiple routers independently.
"""
import re
import time
import logging
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import paramiko

logger = logging.getLogger(__name__)

ROUTER_PRESETS = {
    'degraded_wan': {'latency_ms': 300, 'jitter_ms': 50, 'packet_loss_pct': 5, 'bandwidth_mbps': 0},
    'voice_sla': {'latency_ms': 200, 'jitter_ms': 40, 'packet_loss_pct': 2, 'bandwidth_mbps': 0},
    'video_sla': {'latency_ms': 150, 'jitter_ms': 30, 'packet_loss_pct': 3, 'bandwidth_mbps': 0},
}


def _slugify(name):
    """Convert a display name to a URL-safe ID."""
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


@dataclass
class RouterConnection:
    router_id: str
    name: str
    ip: str
    username: str
    password: str
    ssh_client: Optional[paramiko.SSHClient] = field(default=None, repr=False)
    connected: bool = False
    interfaces: list = field(default_factory=list)
    selected_interface: Optional[str] = None
    current_mode: str = 'idle'  # idle, healthy, impaired, link_down
    impairment_config: dict = field(default_factory=lambda: {
        'latency_ms': 0, 'jitter_ms': 0, 'packet_loss_pct': 0, 'bandwidth_mbps': 0})
    logs: deque = field(default_factory=lambda: deque(maxlen=100))

    def log(self, msg):
        ts = time.strftime('%H:%M:%S')
        entry = f"[{ts}] {msg}"
        self.logs.append(entry)
        logger.info(f"[Router:{self.name}] {msg}")

    def to_dict(self):
        return {
            'router_id': self.router_id,
            'name': self.name,
            'ip': self.ip,
            'username': self.username,
            'connected': self.connected,
            'interfaces': list(self.interfaces),
            'selected_interface': self.selected_interface,
            'current_mode': self.current_mode,
            'impairment_config': dict(self.impairment_config),
            'logs': list(self.logs)[-50:],
        }


class RouterManager:
    """Manages multiple SSH router connections for link simulation."""

    def __init__(self):
        self._routers: dict[str, RouterConnection] = {}
        self._lock = threading.Lock()

    # ─── Router Registry ─────────────────────────────────────

    def add_router(self, name, ip, username, password):
        """Add a router, connect via SSH, and discover interfaces."""
        name = name.strip()
        ip = ip.strip()
        if not name or not ip or not username:
            return False, "Name, IP, and username are required", {}

        router_id = _slugify(name)
        with self._lock:
            if router_id in self._routers:
                return False, f"Router '{name}' already exists", {}

        router = RouterConnection(
            router_id=router_id, name=name, ip=ip,
            username=username.strip(), password=password,
        )

        # Attempt connection
        ok, msg = self._connect(router)
        if not ok:
            return False, msg, {}

        # Discover interfaces
        self._discover_interfaces(router)

        with self._lock:
            self._routers[router_id] = router

        return True, f"Connected to {name} ({ip})", router.to_dict()

    def remove_router(self, router_id):
        """Disconnect and remove a router."""
        with self._lock:
            router = self._routers.pop(router_id, None)
        if not router:
            return False, f"Router '{router_id}' not found"

        # Clean up: restore healthy state before disconnecting
        if router.connected and router.selected_interface and router.current_mode != 'idle':
            self._apply_healthy(router)

        self._disconnect(router)
        return True, f"Router '{router.name}' removed"

    def get_router(self, router_id):
        with self._lock:
            return self._routers.get(router_id)

    def list_routers(self):
        with self._lock:
            return [r.to_dict() for r in self._routers.values()]

    # ─── Connection Management ───────────────────────────────

    def connect(self, router_id):
        router = self.get_router(router_id)
        if not router:
            return False, "Router not found"
        if router.connected:
            return True, "Already connected"
        ok, msg = self._connect(router)
        if ok:
            self._discover_interfaces(router)
        return ok, msg

    def disconnect(self, router_id):
        router = self.get_router(router_id)
        if not router:
            return False, "Router not found"
        self._disconnect(router)
        return True, f"Disconnected from {router.name}"

    def _connect(self, router):
        """Establish SSH connection to a router."""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=router.ip,
                username=router.username,
                password=router.password,
                timeout=10,
                allow_agent=False,
                look_for_keys=False,
            )
            router.ssh_client = client
            router.connected = True
            router.log(f"Connected to {router.ip}")
            return True, f"Connected to {router.ip}"
        except paramiko.AuthenticationException:
            msg = "Authentication failed: invalid username or password"
            router.log(f"Connection failed: {msg}")
            return False, msg
        except paramiko.SSHException as e:
            msg = f"SSH error: {e}"
            router.log(f"Connection failed: {msg}")
            return False, msg
        except Exception as e:
            msg = f"Cannot connect to {router.ip}: {e}"
            router.log(f"Connection failed: {msg}")
            return False, msg

    def _disconnect(self, router):
        """Close SSH connection."""
        if router.ssh_client:
            try:
                router.ssh_client.close()
            except Exception:
                pass
            router.ssh_client = None
        router.connected = False
        router.current_mode = 'idle'
        router.log("Disconnected")

    def _ensure_connected(self, router):
        """Check SSH connection is alive; attempt one reconnect if dead."""
        if router.ssh_client:
            transport = router.ssh_client.get_transport()
            if transport and transport.is_active():
                return True
        # Connection lost — attempt reconnect
        router.log("SSH connection lost, attempting reconnect...")
        router.connected = False
        ok, msg = self._connect(router)
        if not ok:
            router.log(f"Reconnect failed: {msg}")
        return ok

    def _ssh_exec(self, router, cmd):
        """Execute a command on the router via SSH.

        Returns (success: bool, output: str).
        """
        if not self._ensure_connected(router):
            return False, "SSH connection lost. Please reconnect."

        try:
            router.log(f"exec: {cmd}")
            stdin, stdout, stderr = router.ssh_client.exec_command(cmd, timeout=15)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', errors='replace').strip()
            err = stderr.read().decode('utf-8', errors='replace').strip()

            if exit_code != 0:
                # Ignore "RTNETLINK answers: No such file or directory" (no qdisc to delete)
                if 'No such file' in err or 'Cannot delete' in err:
                    return True, out
                router.log(f"cmd failed (exit {exit_code}): {err}")
                return False, err or f"Command failed with exit code {exit_code}"

            return True, out
        except Exception as e:
            router.connected = False
            msg = f"SSH exec error: {e}"
            router.log(msg)
            return False, msg

    # ─── Interface Discovery ─────────────────────────────────

    def discover_interfaces(self, router_id):
        router = self.get_router(router_id)
        if not router:
            return []
        self._discover_interfaces(router)
        return router.interfaces

    def _discover_interfaces(self, router):
        """Discover interfaces on the router via SSH."""
        interfaces = {}

        # Get link info
        ok, link_output = self._ssh_exec(router, 'ip -o link show')
        if not ok:
            router.log(f"Interface discovery failed: {link_output}")
            return

        # Parse link output: "2: eth0: <BROADCAST,...> ... state UP ..."
        for line in link_output.split('\n'):
            if not line.strip():
                continue
            match = re.match(r'\d+:\s+(\S+?)(?:@\S+)?:\s+<([^>]*)>.*?state\s+(\S+)', line)
            if match:
                name = match.group(1)
                state = match.group(3).lower()
                if name == 'lo':
                    continue
                interfaces[name] = {
                    'name': name,
                    'ip_address': '',
                    'subnet': '',
                    'description': '',
                    'state': state,
                }

        # Get address info
        ok, addr_output = self._ssh_exec(router, 'ip -o -4 addr show')
        if ok:
            for line in addr_output.split('\n'):
                if not line.strip():
                    continue
                match = re.match(r'\d+:\s+(\S+)\s+inet\s+(\S+)', line)
                if match:
                    name = match.group(1)
                    cidr = match.group(2)
                    if name in interfaces:
                        parts = cidr.split('/')
                        interfaces[name]['ip_address'] = parts[0]
                        interfaces[name]['subnet'] = '/' + parts[1] if len(parts) > 1 else ''

        # Try to get interface descriptions (ip link show alias)
        ok, alias_output = self._ssh_exec(router, 'ip -o link show')
        if ok:
            for line in alias_output.split('\n'):
                alias_match = re.search(r'^\d+:\s+(\S+?)(?:@\S+)?:.*\\\\alias\s+(.+)', line)
                if alias_match:
                    name = alias_match.group(1)
                    if name in interfaces:
                        interfaces[name]['description'] = alias_match.group(2).strip()

        router.interfaces = list(interfaces.values())
        router.log(f"Discovered {len(router.interfaces)} interfaces")

    # ─── Interface Selection ─────────────────────────────────

    def select_interface(self, router_id, interface_name):
        router = self.get_router(router_id)
        if not router:
            return False, "Router not found"
        if not any(i['name'] == interface_name for i in router.interfaces):
            return False, f"Interface '{interface_name}' not found on router"
        router.selected_interface = interface_name
        router.log(f"Selected interface: {interface_name}")
        return True, f"Interface '{interface_name}' selected"

    # ─── Mode Application ────────────────────────────────────

    def apply_mode(self, router_id, mode, config=None):
        """Apply a mode to the router's selected interface.

        mode: 'healthy', 'impaired', or 'link_down'
        config: dict with latency_ms, jitter_ms, packet_loss_pct, bandwidth_mbps (for impaired mode)
        """
        router = self.get_router(router_id)
        if not router:
            return False, "Router not found"
        if not router.connected:
            return False, "Router not connected"
        if not router.selected_interface:
            return False, "No interface selected"

        if mode == 'healthy':
            return self._apply_healthy(router)
        elif mode == 'impaired':
            return self._apply_impaired(router, config or {})
        elif mode == 'link_down':
            return self._apply_link_down(router)
        else:
            return False, f"Unknown mode: {mode}"

    def _apply_healthy(self, router):
        """Clear all impairment and ensure interface is up."""
        iface = router.selected_interface
        # Clear tc rules (ignore errors if none exist)
        self._ssh_exec(router, f'sudo tc qdisc del dev {iface} root')
        # Bring interface up
        ok, msg = self._ssh_exec(router, f'sudo ip link set {iface} up')
        if not ok:
            return False, f"Failed to bring up {iface}: {msg}"

        router.current_mode = 'healthy'
        router.impairment_config = {'latency_ms': 0, 'jitter_ms': 0,
                                     'packet_loss_pct': 0, 'bandwidth_mbps': 0}
        router.log(f"Mode: HEALTHY — {iface} up, no impairment")
        return True, f"{iface} healthy — no impairment"

    def _apply_impaired(self, router, config):
        """Apply tc/netem impairment on the selected interface."""
        iface = router.selected_interface
        latency_ms = int(config.get('latency_ms', 0))
        jitter_ms = int(config.get('jitter_ms', 0))
        packet_loss_pct = float(config.get('packet_loss_pct', 0))
        bandwidth_mbps = int(config.get('bandwidth_mbps', 0))

        # Ensure interface is up first
        self._ssh_exec(router, f'sudo ip link set {iface} up')
        # Clear existing rules
        self._ssh_exec(router, f'sudo tc qdisc del dev {iface} root')

        # Build netem args
        netem_args = self._build_netem_args(latency_ms, jitter_ms, packet_loss_pct)
        has_netem = len(netem_args) > 0
        has_bw = bandwidth_mbps > 0

        if not has_netem and not has_bw:
            router.current_mode = 'healthy'
            router.log("No impairment values set — mode remains healthy")
            return True, "No impairment values — interface is healthy"

        if has_bw and has_netem:
            self._ssh_exec(router,
                f'sudo tc qdisc add dev {iface} root handle 1: htb default 10')
            self._ssh_exec(router,
                f'sudo tc class add dev {iface} parent 1: classid 1:10 htb '
                f'rate {bandwidth_mbps}mbit ceil {bandwidth_mbps}mbit')
            ok, msg = self._ssh_exec(router,
                f'sudo tc qdisc add dev {iface} parent 1:10 handle 10: netem {netem_args}')
        elif has_bw:
            self._ssh_exec(router,
                f'sudo tc qdisc add dev {iface} root handle 1: htb default 10')
            ok, msg = self._ssh_exec(router,
                f'sudo tc class add dev {iface} parent 1: classid 1:10 htb '
                f'rate {bandwidth_mbps}mbit ceil {bandwidth_mbps}mbit')
        else:
            ok, msg = self._ssh_exec(router,
                f'sudo tc qdisc add dev {iface} root netem {netem_args}')

        if not ok:
            return False, f"Failed to apply impairment: {msg}"

        router.current_mode = 'impaired'
        router.impairment_config = {
            'latency_ms': latency_ms, 'jitter_ms': jitter_ms,
            'packet_loss_pct': packet_loss_pct, 'bandwidth_mbps': bandwidth_mbps,
        }
        desc = self._fmt_impairment(router.impairment_config)
        router.log(f"Mode: IMPAIRED — {iface} | {desc}")
        return True, f"{iface} impaired — {desc}"

    def _apply_link_down(self, router):
        """Shut down the selected interface."""
        iface = router.selected_interface
        # Clear tc rules first
        self._ssh_exec(router, f'sudo tc qdisc del dev {iface} root')
        # Bring interface down
        ok, msg = self._ssh_exec(router, f'sudo ip link set {iface} down')
        if not ok:
            return False, f"Failed to bring down {iface}: {msg}"

        router.current_mode = 'link_down'
        router.impairment_config = {'latency_ms': 0, 'jitter_ms': 0,
                                     'packet_loss_pct': 0, 'bandwidth_mbps': 0}
        router.log(f"Mode: LINK DOWN — {iface} shut down")
        return True, f"{iface} is DOWN"

    # ─── Command Helpers ─────────────────────────────────────

    @staticmethod
    def _build_netem_args(latency_ms, jitter_ms, packet_loss_pct):
        """Build netem argument string. Designed to be overridden for other vendors."""
        parts = []
        if latency_ms > 0:
            parts.append(f'delay {int(latency_ms)}ms')
            if jitter_ms > 0:
                parts.append(f'{int(jitter_ms)}ms distribution normal')
        if packet_loss_pct > 0:
            parts.append(f'loss {float(packet_loss_pct)}%')
        return ' '.join(parts)

    @staticmethod
    def _fmt_impairment(config):
        """Format impairment values for display."""
        parts = []
        if config.get('latency_ms'):
            parts.append(f"latency={config['latency_ms']}ms")
        if config.get('jitter_ms'):
            parts.append(f"jitter={config['jitter_ms']}ms")
        if config.get('packet_loss_pct'):
            parts.append(f"loss={config['packet_loss_pct']}%")
        if config.get('bandwidth_mbps'):
            parts.append(f"bw={config['bandwidth_mbps']}Mbps")
        return ' '.join(parts) if parts else 'none'

    # ─── Status ──────────────────────────────────────────────

    def get_status(self, router_id):
        router = self.get_router(router_id)
        if not router:
            return {'error': 'Router not found'}
        # Refresh connected state
        if router.ssh_client:
            transport = router.ssh_client.get_transport()
            if not transport or not transport.is_active():
                router.connected = False
                router.current_mode = 'idle'
        return router.to_dict()

    def get_all_status(self):
        with self._lock:
            return {rid: r.to_dict() for rid, r in self._routers.items()}


# Module-level singleton
router_manager = RouterManager()
