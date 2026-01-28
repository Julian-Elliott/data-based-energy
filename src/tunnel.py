"""
SSH Tunnel manager for MariaDB connection.
Provides utilities to start, stop, and check the SSH tunnel.
"""

import subprocess
import socket
import time
from typing import Optional

from src.secrets import load_secrets


class SSHTunnel:
    """Manages SSH tunnel for MariaDB access."""

    def __init__(self, server_name: Optional[str] = None):
        """Initialize tunnel with config from secrets.
        
        Args:
            server_name: Name of the server. If None, uses default.
        """
        from .secrets import get_tunnel_config
        from .config import get_default_server
        
        if server_name is None:
            server_name = get_default_server()
        
        self.server_name = server_name
        tunnel_config = get_tunnel_config(server_name)

        # All config must be in secrets.yaml - no defaults for security
        self.ssh_host = tunnel_config.get("host")
        self.ssh_port = tunnel_config.get("port", 22)
        self.ssh_user = tunnel_config.get("user", "root")
        self.remote_host = tunnel_config.get("remote_host", "core-mariadb")
        self.remote_port = tunnel_config.get("remote_port", 3306)
        self.local_port = tunnel_config.get("local_port", 3306)
        
        if not self.ssh_host:
            raise ValueError(
                f"SSH tunnel host not configured for server '{server_name}'. "
                f"Set ssh_tunnel.servers.{server_name}.host in config/secrets.yaml"
            )

        self._process: Optional[subprocess.Popen] = None

    def is_tunnel_active(self) -> bool:
        """
        Check if the SSH tunnel is active by testing local port.

        Returns:
            True if tunnel is active and responding.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(("127.0.0.1", self.local_port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def is_mariadb_responding(self) -> bool:
        """
        Check if MariaDB is responding through the tunnel.

        Returns:
            True if MariaDB responds with a valid handshake.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(("127.0.0.1", self.local_port))
            # MariaDB sends a greeting packet on connect
            data = sock.recv(100)
            sock.close()
            # Check for MariaDB signature in handshake
            return b"MariaDB" in data or b"mysql" in data.lower()
        except Exception:
            return False

    def start(self, wait_seconds: int = 3) -> bool:
        """
        Start the SSH tunnel in background.

        Args:
            wait_seconds: Seconds to wait for tunnel to establish.

        Returns:
            True if tunnel started successfully.
        """
        if self.is_tunnel_active():
            return True

        # Build SSH command
        cmd = [
            "ssh",
            "-L", f"{self.local_port}:{self.remote_host}:{self.remote_port}",
            "-p", str(self.ssh_port),
            f"{self.ssh_user}@{self.ssh_host}",
            "-N",  # No command, just tunnel
            "-f",  # Background
            "-o", "StrictHostKeyChecking=no",
            "-o", "ExitOnForwardFailure=yes",
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=10)

            # Wait for tunnel to establish
            for _ in range(wait_seconds * 2):
                time.sleep(0.5)
                if self.is_tunnel_active():
                    return True

            return self.is_tunnel_active()
        except subprocess.CalledProcessError as e:
            print(f"Failed to start tunnel: {e.stderr.decode()}")
            return False
        except subprocess.TimeoutExpired:
            print("Timeout starting SSH tunnel")
            return False

    def stop(self) -> bool:
        """
        Stop all SSH tunnels to the configured host.

        Returns:
            True if tunnels were stopped.
        """
        try:
            # Kill any SSH processes with our tunnel config
            subprocess.run(
                ["pkill", "-f", f"ssh.*{self.local_port}:{self.remote_host}"],
                capture_output=True
            )
            time.sleep(0.5)
            return not self.is_tunnel_active()
        except Exception:
            return False

    def ensure_connected(self) -> bool:
        """
        Ensure tunnel is connected, starting it if necessary.

        Returns:
            True if tunnel is active after check/start.
        """
        if self.is_tunnel_active():
            return True
        return self.start()

    def get_status(self) -> dict:
        """
        Get detailed tunnel status.

        Returns:
            Dictionary with tunnel status information.
        """
        tunnel_active = self.is_tunnel_active()
        mariadb_ok = self.is_mariadb_responding() if tunnel_active else False

        return {
            "tunnel_active": tunnel_active,
            "mariadb_responding": mariadb_ok,
            "local_port": self.local_port,
            "remote_target": f"{self.remote_host}:{self.remote_port}",
            "ssh_host": f"{self.ssh_user}@{self.ssh_host}:{self.ssh_port}",
        }


# Module-level convenience functions
_tunnels: dict[str, SSHTunnel] = {}


def get_tunnel(server_name: Optional[str] = None) -> SSHTunnel:
    """Get or create a tunnel instance for a server.
    
    Args:
        server_name: Server name. If None, uses default.
    """
    from .config import get_default_server
    
    if server_name is None:
        server_name = get_default_server()
    
    global _tunnels
    if server_name not in _tunnels:
        _tunnels[server_name] = SSHTunnel(server_name)
    return _tunnels[server_name]


def ensure_tunnel(server_name: Optional[str] = None) -> bool:
    """Ensure the SSH tunnel is connected.
    
    Args:
        server_name: Server name. If None, uses default.
    """
    return get_tunnel(server_name).ensure_connected()


def tunnel_status(server_name: Optional[str] = None) -> dict:
    """Get tunnel status.
    
    Args:
        server_name: Server name. If None, uses default.
    """
    return get_tunnel(server_name).get_status()
