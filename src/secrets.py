"""
Secrets management utilities.
Loads credentials from config/secrets.yaml (gitignored).
"""

import yaml
from pathlib import Path


def get_project_root() -> Path:
    """Find the project root by looking for config/secrets.yaml."""
    current = Path(__file__).resolve().parent
    # Walk up the directory tree for config/secrets.yaml
    for parent in [current] + list(current.parents):
        secrets_path = parent / "config" / "secrets.yaml"
        if secrets_path.exists():
            return parent
    raise FileNotFoundError(
        "Could not find config/secrets.yaml. "
        "Copy config/secrets.example.yaml to config/secrets.yaml "
        "and add your credentials."
    )


def load_secrets(path: str | Path | None = None) -> dict:
    """
    Load secrets from YAML file.
    Args:
        path: Optional path to secrets file. Defaults to config/secrets.yaml
    Returns:
        Dictionary containing secrets
    """
    if path is None:
        secrets_path = get_project_root() / "config" / "secrets.yaml"
    else:
        secrets_path = Path(path)
    if not secrets_path.exists():
        raise FileNotFoundError(
            f"Secrets file not found: {secrets_path}\n"
            "Copy config/secrets.example.yaml to config/secrets.yaml."
        )
    with open(secrets_path) as f:
        return yaml.safe_load(f)


def get_ha_credentials(server_name: str | None = None) -> tuple[str, str]:
    """
    Get Home Assistant URL and token from secrets.
    Args:
        server_name: Server name. If None, uses default from config.
    Returns:
        Tuple of (url, token)
    """
    from .config import get_default_server, get_server_config
    
    if server_name is None:
        server_name = get_default_server()
    
    secrets = load_secrets()
    config = get_server_config(server_name)
    
    # Get token from secrets
    ha_secrets = secrets.get("home_assistant", {}).get("servers", {})
    server_secrets = ha_secrets.get(server_name, {})
    token = server_secrets.get("token")
    
    # Build URL from config
    host = config.get("host")
    port = config.get("port", 8123)
    url = f"http://{host}:{port}"
    
    if not token:
        raise ValueError(
            f"Missing token for server '{server_name}' in config/secrets.yaml. "
            f"Ensure 'home_assistant.servers.{server_name}.token' is set."
        )
    
    return url, token


def get_all_servers() -> list[str]:
    """
    Get list of all configured servers from secrets.
    Returns:
        List of server names.
    """
    from .config import get_all_servers as config_get_all_servers
    return config_get_all_servers()


def get_db_config(server_name: str | None = None) -> dict:
    """
    Get database configuration for a specific server.
    Args:
        server_name: Server name. If None, uses default from config.
    Returns:
        Database configuration dictionary.
    """
    from .config import get_default_server
    
    if server_name is None:
        server_name = get_default_server()
    
    secrets = load_secrets()
    db_servers = secrets.get("database", {}).get("servers", {})
    
    if server_name not in db_servers:
        raise ValueError(
            f"Database config for server '{server_name}' not found in config/secrets.yaml."
        )
    
    return db_servers[server_name]


def get_tunnel_config(server_name: str | None = None) -> dict:
    """
    Get SSH tunnel configuration for a specific server.
    Args:
        server_name: Server name. If None, uses default from config.
    Returns:
        Tunnel configuration dictionary.
    """
    from .config import get_default_server
    
    if server_name is None:
        server_name = get_default_server()
    
    secrets = load_secrets()
    tunnel_servers = secrets.get("ssh_tunnel", {}).get("servers", {})
    
    if server_name not in tunnel_servers:
        raise ValueError(
            f"SSH tunnel config for server '{server_name}' not found in config/secrets.yaml."
        )
    
    return tunnel_servers[server_name]
