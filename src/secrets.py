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


def get_ha_credentials() -> tuple[str, str]:
    """
    Get Home Assistant URL and token from secrets.
    Returns:
        Tuple of (url, token)
    """
    secrets = load_secrets()
    ha_config = secrets.get("home_assistant", {})
    url = ha_config.get("url")
    token = ha_config.get("token")
    if not url or not token:
        raise ValueError(
            "Missing Home Assistant credentials in config/secrets.yaml. "
            "Ensure 'home_assistant.url' and 'home_assistant.token' are set."
        )
    return url, token
