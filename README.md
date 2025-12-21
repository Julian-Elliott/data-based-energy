# Data-Based Energy: Home Assistant Data Collector

This project collects state and statistics data from a Home Assistant instance using a modular, secure, and testable Python codebase.

## Features

- **Modular API client** for Home Assistant (REST API)
- **Direct MariaDB access** for faster bulk data extraction
- **SSH tunnel automation** for secure remote database access
- **Secure secrets management** using `config/secrets.yaml` (never commit secrets!)
- **Configurable parameters** in `config/config.yaml`
- **Jupyter notebooks** for data exploration and extraction
- **pytest integration** with VS Code Test Explorer

## Project Structure

```
.
├── config/
│   ├── config.yaml            # Non-secret config (host, port, etc.)
│   ├── config.example.yaml    # Template for config.yaml
│   ├── secrets.yaml           # Credentials and tokens (gitignored)
│   └── secrets.example.yaml   # Template for secrets.yaml
├── data/                       # Collected data (gitignored)
├── notebooks/
│   ├── 01_explore_api.ipynb   # API exploration
│   └── 02_extract_data.ipynb  # MariaDB data extraction
├── src/
│   ├── __init__.py
│   ├── config.py              # Config loader
│   ├── home_assistant.py      # REST API client
│   ├── secrets.py             # Secrets loader
│   └── tunnel.py              # SSH tunnel manager
├── tests/
│   ├── __init__.py
│   └── test_connection.py     # pytest connection tests
├── pytest.ini                  # pytest configuration
├── requirements.txt
├── .gitignore
└── README.md
```

## Quick Start

1. **Clone the repo and create a virtual environment:**
   ```sh
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Configure your secrets and config:**
   - Copy `config/secrets.example.yaml` to `config/secrets.yaml` and add your Home Assistant URL and token.
   - Copy `config/config.example.yaml` to `config/config.yaml` and set your host/port.
3. **Test the connection:**
   - Run tests in VS Code (Testing sidebar) or:
     ```sh
     pytest
     ```
   - All connectivity tests should pass.
4. **Explore data in Jupyter:**
   - `notebooks/01_explore_api.ipynb` - Explore the REST API
   - `notebooks/02_extract_data.ipynb` - Extract data from MariaDB

## Home Assistant URL and Token Setup

### 1. Finding Your Home Assistant URL (with Tailscale)

- If you use the [Tailscale add-on](https://tailscale.com/kb/1153/home-assistant/) for Home Assistant, your instance will be accessible at a unique Tailscale domain, e.g.:

  `http://homeassistant-xxxxxx.ts.net:8123`
- You can find this URL in the Tailscale admin panel or the Tailscale app on your device. Use this as the `url` in your `config/secrets.yaml`.

### 2. Creating a Long-Lived Access Token

- In Home Assistant, click your user icon (bottom left) to go to your **Profile** page.
- Scroll down to **Long-Lived Access Tokens** and click **Create Token**.
- Copy the token and paste it into your `config/secrets.yaml`.

> **Warning:**
>
> - Treat your long-lived token like a password. **Never share it or commit it to version control.**
> - If you believe your token has been exposed, revoke it immediately from your Home Assistant profile.

## Data Access Methods

This project supports two methods for accessing Home Assistant data:

### REST API (Recommended for real-time data)
- Uses the `HomeAssistantClient` class in `src/home_assistant.py`
- Good for: current states, triggering services, small queries
- See `notebooks/01_explore_api.ipynb`

### MariaDB Direct Access (Recommended for bulk extraction)
- Uses SSH tunnel through Tailscale for secure access
- The `SSHTunnel` class in `src/tunnel.py` manages the connection
- Good for: historical data, statistics, large exports
- See `notebooks/02_extract_data.ipynb`

**Note:** MariaDB access requires the MariaDB and SSH/Terminal add-ons on Home Assistant.

## Security

- **Never commit `config/secrets.yaml`!** It is gitignored by default.
- Use `config.example.yaml` and `secrets.example.yaml` as templates for sharing.
- Database access uses SSH tunneling over Tailscale VPN for security.
- Consider using a read-only database user for data extraction.

## Testing

- Tests use **pytest** and integrate with VS Code Test Explorer
- Run all tests: `pytest`
- Run specific tests: `pytest -k tunnel` or `pytest -k mariadb`
- Tests verify: Tailscale connectivity, SSH tunnel, MariaDB, Home Assistant API

## Extending

- Add new collectors or analysis modules in `src/`.
- Add more tests in `tests/`.

---

**Questions?** Open an issue or check the code comments for more details.
