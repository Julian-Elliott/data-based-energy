"""
Test Home Assistant API connection using config and secrets.
"""
from home_assistant import HomeAssistantClient

if __name__ == "__main__":
    print("Testing Home Assistant API connection...")
    try:
        ha = HomeAssistantClient()
        config = ha.test_connection()
        print("\nConnection successful!")
        print(f"Location: {config.get('location_name', 'Unknown')}")
        print(f"Version: {config.get('version', 'Unknown')}")
    except Exception as e:
        print(f"Connection failed: {e}")
