"""
Configuration loader for non-secret parameters.
Loads config from config/config.yaml.
"""


import yaml
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.yaml"


def load_config(path: str | Path = CONFIG_PATH) -> dict:
    """
    Load configuration from YAML file.
    Args:
        path: Path to config file.
    Returns:
        Dictionary of config values.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {path}\n"
            "Copy config.example.yaml to config.yaml and edit as needed."
        )
    with open(path) as f:
        return yaml.safe_load(f)


def get_ha_config() -> dict:
    """
    Get Home Assistant config section.
    Returns:
        Dictionary of HA config values.
    """
    config = load_config()
    return config.get("home_assistant", {})


def get_default_server() -> str:
    """
    Get the default server name from config.
    Returns:
        Default server name.
    """
    config = load_config()
    return config.get("default_server", "homeassistant")


def get_all_servers() -> list[str]:
    """
    Get list of all configured server names.
    Returns:
        List of server names.
    """
    config = load_config()
    servers = config.get("home_assistant", {}).get("servers", {})
    return list(servers.keys())


def get_server_config(server_name: Optional[str] = None) -> dict:
    """
    Get configuration for a specific server.
    Args:
        server_name: Name of the server. If None, uses default.
    Returns:
        Server configuration dictionary.
    """
    if server_name is None:
        server_name = get_default_server()
    
    config = load_config()
    servers = config.get("home_assistant", {}).get("servers", {})
    
    if server_name not in servers:
        raise ValueError(
            f"Server '{server_name}' not found in config. "
            f"Available servers: {list(servers.keys())}"
        )
    
    return servers[server_name]
