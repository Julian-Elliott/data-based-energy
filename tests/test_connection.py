"""
Connection tests for Home Assistant API and MariaDB database.
Compatible with VS Code Python Test Explorer (pytest).
Tests all configured servers from config.yaml.
"""

import pytest
from sqlalchemy import create_engine, text

from src.home_assistant import HomeAssistantClient
from src.secrets import load_secrets, get_all_servers, get_db_config, get_ha_credentials
from src.tunnel import SSHTunnel, ensure_tunnel
from src.config import get_server_config


def get_test_servers():
    """Get list of all servers to test."""
    try:
        return get_all_servers()
    except Exception:
        return []


class TestTailscaleConnection:
    """Test Tailscale VPN connectivity for all servers."""

    @pytest.mark.parametrize("server_name", get_test_servers())
    def test_tailscale_reachable(self, server_name):
        """Test that Home Assistant is reachable via Tailscale."""
        import socket

        config = get_server_config(server_name)
        host = config.get("host")
        port = config.get("port", 8123)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        try:
            result = sock.connect_ex((host, port))
            assert result == 0, f"Cannot reach {server_name} at {host}:{port}"
        finally:
            sock.close()


class TestSSHTunnel:
    """Test SSH tunnel functionality for all servers."""

    @pytest.mark.parametrize("server_name", get_test_servers())
    def test_tunnel_can_start(self, server_name):
        """Test that SSH tunnel can be started."""
        tunnel = SSHTunnel(server_name)

        # Try to start tunnel
        result = tunnel.start(wait_seconds=5)

        assert result, f"Failed to start SSH tunnel for {server_name}"
        assert tunnel.is_tunnel_active(), f"Tunnel not active after start for {server_name}"

    @pytest.mark.parametrize("server_name", get_test_servers())
    def test_tunnel_status(self, server_name):
        """Test tunnel status reporting."""
        tunnel = SSHTunnel(server_name)
        status = tunnel.get_status()

        assert "tunnel_active" in status
        assert "mariadb_responding" in status
        assert "local_port" in status

    @pytest.mark.parametrize("server_name", get_test_servers())
    def test_ensure_tunnel(self, server_name):
        """Test ensure_tunnel convenience function."""
        result = ensure_tunnel(server_name)
        assert result, f"ensure_tunnel() failed for {server_name}"


class TestMariaDBConnection:
    """Test MariaDB database connection through SSH tunnel for all servers."""

    @pytest.fixture(autouse=True)
    def setup_tunnel(self, request):
        """Ensure tunnel is active before each test."""
        # Get server_name from test parametrization
        if hasattr(request, 'param'):
            server_name = request.param
        else:
            # Extract from test node
            if 'server_name' in request.node.callspec.params:
                server_name = request.node.callspec.params['server_name']
            else:
                server_name = None
        
        if server_name:
            tunnel = SSHTunnel(server_name)
            if not tunnel.is_tunnel_active():
                tunnel.start(wait_seconds=5)
        yield
        # Don't stop tunnel after tests - leave it running

    @pytest.mark.parametrize("server_name", get_test_servers())
    def test_mariadb_responding(self, server_name):
        """Test that MariaDB responds through tunnel."""
        tunnel = SSHTunnel(server_name)
        assert tunnel.is_tunnel_active(), f"Tunnel not active for {server_name}"
        assert tunnel.is_mariadb_responding(), f"MariaDB not responding for {server_name}"

    @pytest.mark.parametrize("server_name", get_test_servers())
    def test_database_connection(self, server_name):
        """Test full database connection with SQLAlchemy."""
        db_config = get_db_config(server_name)

        connection_string = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )

        engine = create_engine(connection_string)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            row = result.fetchone()
            assert row is not None, f"No result returned from SELECT VERSION() for {server_name}"
            version = row[0]

        engine.dispose()

        assert "MariaDB" in version, f"Expected MariaDB for {server_name}, got: {version}"

    @pytest.mark.parametrize("server_name", get_test_servers())
    def test_can_query_states_meta(self, server_name):
        """Test that we can query the states_meta table."""
        db_config = get_db_config(server_name)

        connection_string = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )

        engine = create_engine(connection_string)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM states_meta"))
            row = result.fetchone()
            assert row is not None, f"No result returned from SELECT COUNT() for {server_name}"
            count = row[0]

        engine.dispose()

        assert count > 0, f"states_meta table is empty for {server_name}"


class TestHomeAssistantAPI:
    """Test Home Assistant REST API connection for all servers."""

    @pytest.mark.parametrize("server_name", get_test_servers())
    def test_api_connection(self, server_name):
        """Test that Home Assistant API is reachable."""
        ha = HomeAssistantClient(server_name=server_name)
        config = ha.test_connection()

        assert "location_name" in config, f"Missing location_name for {server_name}"
        assert "version" in config, f"Missing version for {server_name}"

    @pytest.mark.parametrize("server_name", get_test_servers())
    def test_api_returns_valid_config(self, server_name):
        """Test that API returns valid configuration."""
        ha = HomeAssistantClient(server_name=server_name)
        config = ha.test_connection()

        assert config.get("state") == "RUNNING", f"Home Assistant not running for {server_name}"


# Convenience test to run all connectivity checks
class TestFullConnectivity:
    """Full connectivity test suite for all servers."""

    @pytest.mark.parametrize("server_name", get_test_servers())
    def test_all_connections(self, server_name):
        """Test all connection types in sequence for each server."""
        errors = []
        
        print(f"\n\n=== Testing {server_name} ===")

        # Test 1: Tailscale
        try:
            import socket
            config = get_server_config(server_name)
            host = config.get("host")
            port = config.get("port", 8123)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            try:
                result = sock.connect_ex((host, port))
                if result != 0:
                    errors.append(f"Tailscale: Cannot reach {host}:{port}")
            finally:
                sock.close()
        except Exception as e:
            errors.append(f"Tailscale: {e}")

        # Test 2: SSH Tunnel
        try:
            tunnel = SSHTunnel(server_name)
            if not tunnel.ensure_connected():
                errors.append("SSH Tunnel: Failed to establish")
        except Exception as e:
            errors.append(f"SSH Tunnel: {e}")

        # Test 3: MariaDB
        try:
            tunnel = SSHTunnel(server_name)
            if not tunnel.is_mariadb_responding():
                errors.append("MariaDB: Not responding")
        except Exception as e:
            errors.append(f"MariaDB: {e}")

        # Test 4: Home Assistant API
        try:
            ha = HomeAssistantClient(server_name=server_name)
            ha.test_connection()
        except Exception as e:
            errors.append(f"Home Assistant API: {e}")

        assert len(errors) == 0, f"Connection failures for {server_name}: {errors}"
