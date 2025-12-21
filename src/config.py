"""
Configuration loader for non-secret parameters.
Loads config from config/config.yaml.
"""


import yaml
from pathlib import Path

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
