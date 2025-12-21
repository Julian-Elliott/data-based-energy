"""
Home Assistant API Client.
Provides methods to interact with Home Assistant REST API.
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Any
from src.secrets import get_ha_credentials


class HomeAssistantClient:
    """Client for interacting with Home Assistant REST API."""

    def __init__(self, url: Optional[str] = None, token: Optional[str] = None):
        """
        Initialize the Home Assistant client.
        Args:
            url: Home Assistant URL. If None, loads from config.yaml or
                config/secrets.yaml
            token: Long-lived access token. If None, loads from
                config/secrets.yaml
        """
        from .config import get_ha_config
        ha_config = get_ha_config()
        # Prefer explicit url, then config.yaml, then secrets.yaml
        if url is not None:
            self.url = url
        elif ha_config.get("host") and ha_config.get("port"):
            self.url = f"http://{ha_config['host']}:{ha_config['port']}"
        else:
            secret_url, _ = get_ha_credentials()
            self.url = secret_url

        if token is not None:
            self.token = token
        else:
            _, secret_token = get_ha_credentials()
            self.token = secret_token

        # Remove trailing slash if present
        self.url = self.url.rstrip("/")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make a request to the Home Assistant API."""
        url = f"{self.url}/api/{endpoint}"
        response = requests.request(
            method, url, headers=self.headers, **kwargs
        )
        response.raise_for_status()
        return response.json() if response.text else None

    def test_connection(self) -> dict:
        """Test the API connection and print status."""
        try:
            config = self._request("GET", "config")
            print("✅ Connected to Home Assistant!")
            print(f"   Location: {config.get('location_name', 'Unknown')}")
            print(f"   Version: {config.get('version', 'Unknown')}")
            return config
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection failed: {e}")
            raise

    def get_config(self) -> dict:
        """Get Home Assistant configuration."""
        return self._request("GET", "config")

    def get_states(self) -> list[dict]:
        """Get all entity states."""
        return self._request("GET", "states")

    def get_state(self, entity_id: str) -> dict:
        """Get state of a specific entity."""
        return self._request("GET", f"states/{entity_id}")

    def get_services(self) -> list[dict]:
        """Get all available services."""
        return self._request("GET", "services")

    def get_history(
        self,
        entity_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        minimal_response: bool = True,
    ) -> list[list[dict]]:
        """
        Get state history for entities.

        Args:
            entity_id: Specific entity ID to filter. If None, returns all.
            start_time: Start of history period. Defaults to 24h ago.
            end_time: End of history period. Defaults to now.
            minimal_response: If True, only return state changes.

        Returns:
            List of entity histories, each containing list of state changes.
        """
        if start_time is None:
            start_time = datetime.now() - timedelta(days=1)

        endpoint = f"history/period/{start_time.isoformat()}"

        params = {}
        if entity_id:
            params["filter_entity_id"] = entity_id
        if end_time:
            params["end_time"] = end_time.isoformat()
        if minimal_response:
            params["minimal_response"] = "true"

        return self._request("GET", endpoint, params=params)

    def get_statistics(
        self,
        entity_ids: list[str],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        period: str = "hour",
    ) -> list[list[dict]]:
        """
        Get long-term statistics for entities.

        Args:
            entity_ids: List of entity IDs to fetch statistics for.
            start_time: Start of statistics period.
            end_time: End of statistics period.
            period: Aggregation period: "5minute", "hour", "day", "week",
                "month"

        Returns:
            List of entity histories, each containing list of state changes.
        """
        if start_time is None:
            start_time = datetime.now() - timedelta(days=7)

        payload = {
            "type": "recorder/statistics_during_period",
            "start_time": start_time.isoformat(),
            "statistic_ids": entity_ids,
            "period": period,
        }

        if end_time:
            payload["end_time"] = end_time.isoformat()

        # Statistics require WebSocket API - using REST workaround
        # For full statistics support, use get_history with specific entities
        return self.get_history(
            entity_id=",".join(entity_ids),
            start_time=start_time,
            end_time=end_time,
        )

    def get_entities_by_domain(self, domain: str) -> list[dict]:
        """
        Get all entities for a specific domain (e.g., 'sensor', 'light').

        Args:
            domain: Entity domain to filter by.

        Returns:
            List of entity states matching the domain.
        """
        states = self.get_states()
        return [s for s in states if s["entity_id"].startswith(f"{domain}.")]

    def get_energy_entities(self) -> list[dict]:
        """Get all energy-related entities."""
        states = self.get_states()
        energy_keywords = ["energy", "power", "watt", "kwh", "consumption"]

        energy_entities = []
        for state in states:
            entity_id = state["entity_id"].lower()
            friendly_name = state.get("attributes", {}) \
                .get("friendly_name", "")
            friendly_name = friendly_name.lower()

            if any(
                kw in entity_id or kw in friendly_name
                for kw in energy_keywords
            ):
                energy_entities.append(state)

        return energy_entities

    def call_service(
        self,
        domain: str,
        service: str,
        entity_id: Optional[str] = None,
        **service_data,
    ) -> None:
        """
        Call a Home Assistant service.

        Args:
            domain: Service domain (e.g., 'light', 'switch')
            service: Service name (e.g., 'turn_on', 'turn_off')
            entity_id: Target entity ID
            **service_data: Additional service data
        """
        data = service_data.copy()
        if entity_id:
            data["entity_id"] = entity_id

        self._request("POST", f"services/{domain}/{service}", json=data)
