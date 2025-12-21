import unittest
from src.home_assistant import HomeAssistantClient


class TestHomeAssistantConnection(unittest.TestCase):

    def test_api_connection(self):
        ha = HomeAssistantClient()
        config = ha.test_connection()
        self.assertIn('location_name', config)
        self.assertIn('version', config)


if __name__ == "__main__":
    unittest.main()
