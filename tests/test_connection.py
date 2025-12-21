"""
Connection tests for Home Assistant API and MariaDB database.
Compatible with VS Code Python Test Explorer (pytest).
"""

import pytest
from sqlalchemy import create_engine, text

from src.home_assistant import HomeAssistantClient
from src.secrets import load_secrets
from src.tunnel import SSHTunnel, ensure_tunnel


class TestTailscaleConnection:
    """Test Tailscale VPN connectivity."""

    def test_tailscale_reachable(self):
        """Test that Home Assistant is reachable via Tailscale."""
        import socket

        secrets = load_secrets()
        ha_url = secrets.get("home_assistant", {}).get("url", "")

        # Extract host from URL
        url_no_proto = ha_url.replace("http://", "").replace("https://", "")
        host = url_no_proto.split(":")[0]

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        try:
            result = sock.connect_ex((host, 8123))
            assert result == 0, f"Cannot reach Home Assistant at {host}:8123"
        finally:
            sock.close()


class TestSSHTunnel:
    """Test SSH tunnel functionality."""

    def test_tunnel_can_start(self):
        """Test that SSH tunnel can be started."""
        tunnel = SSHTunnel()

        # Try to start tunnel
        result = tunnel.start(wait_seconds=5)

        assert result, "Failed to start SSH tunnel"
        assert tunnel.is_tunnel_active(), "Tunnel not active after start"

    def test_tunnel_status(self):
        """Test tunnel status reporting."""
        tunnel = SSHTunnel()
        status = tunnel.get_status()

        assert "tunnel_active" in status
        assert "mariadb_responding" in status
        assert "local_port" in status

    def test_ensure_tunnel(self):
        """Test ensure_tunnel convenience function."""
        result = ensure_tunnel()
        assert result, "ensure_tunnel() failed"


class TestMariaDBConnection:
    """Test MariaDB database connection through SSH tunnel."""

    @pytest.fixture(autouse=True)
    def setup_tunnel(self):
        """Ensure tunnel is active before each test."""
        tunnel = SSHTunnel()
        if not tunnel.is_tunnel_active():
            tunnel.start(wait_seconds=5)
        yield
        # Don't stop tunnel after tests - leave it running

    def test_mariadb_responding(self):
        """Test that MariaDB responds through tunnel."""
        tunnel = SSHTunnel()
        assert tunnel.is_tunnel_active(), "Tunnel not active"
        assert tunnel.is_mariadb_responding(), "MariaDB not responding"

    def test_database_connection(self):
        """Test full database connection with SQLAlchemy."""
        secrets = load_secrets()
        db_config = secrets.get("database", {})

        connection_string = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )

        engine = create_engine(connection_string)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            row = result.fetchone()
            assert row is not None, "No result returned from SELECT VERSION()"
            version = row[0]

        engine.dispose()

        assert "MariaDB" in version, f"Expected MariaDB, got: {version}"

    def test_can_query_states_meta(self):
        """Test that we can query the states_meta table."""
        secrets = load_secrets()
        db_config = secrets.get("database", {})

        connection_string = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )

        engine = create_engine(connection_string)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM states_meta"))
            row = result.fetchone()
            assert row is not None, "No result returned from SELECT COUNT(*)"
            count = row[0]

        engine.dispose()

        assert count > 0, "states_meta table is empty"


class TestHomeAssistantAPI:
    """Test Home Assistant REST API connection."""

    def test_api_connection(self):
        """Test that Home Assistant API is reachable."""
        ha = HomeAssistantClient()
        config = ha.test_connection()

        assert "location_name" in config
        assert "version" in config

    def test_api_returns_valid_config(self):
        """Test that API returns valid configuration."""
        ha = HomeAssistantClient()
        config = ha.test_connection()

        assert config.get("state") == "RUNNING", "Home Assistant not running"


# Convenience test to run all connectivity checks
class TestFullConnectivity:
    """Full connectivity test suite."""

    def test_all_connections(self):
        """Test all connection types in sequence."""
        errors = []

        # Test 1: Tailscale
        try:
            TestTailscaleConnection().test_tailscale_reachable()
        except AssertionError as e:
            errors.append(f"Tailscale: {e}")

        # Test 2: SSH Tunnel
        try:
            tunnel = SSHTunnel()
            if not tunnel.ensure_connected():
                errors.append("SSH Tunnel: Failed to establish")
        except Exception as e:
            errors.append(f"SSH Tunnel: {e}")

        # Test 3: MariaDB
        try:
            tunnel = SSHTunnel()
            if not tunnel.is_mariadb_responding():
                errors.append("MariaDB: Not responding")
        except Exception as e:
            errors.append(f"MariaDB: {e}")

        # Test 4: Home Assistant API
        try:
            ha = HomeAssistantClient()
            ha.test_connection()
        except Exception as e:
            errors.append(f"Home Assistant API: {e}")

        assert len(errors) == 0, f"Connection failures: {errors}"
