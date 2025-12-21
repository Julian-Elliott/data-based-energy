# Data-Based Energy: Home Assistant Data Collector

This project collects state and statistics data from a Home Assistant instance using a modular, secure, and testable Python codebase.

## Features

- **Modular API client** for Home Assistant (REST API)
- **Secure secrets management** using `config/secrets.yaml` (never commit secrets!)
- **Configurable parameters** in `config/config.yaml`
- **Jupyter notebook** for data exploration
- **VS Code Python Test integration** for robust testing

## Project Structure

```
.
├── config/
│   ├── config.yaml            # Non-secret config (host, port, etc.)
│   ├── config.example.yaml    # Template for config.yaml
│   ├── secrets.yaml           # Home Assistant token/URL (gitignored)
│   └── secrets.example.yaml   # Template for secrets.yaml
├── data/
│   └── raw/                   # Collected data (gitignored)
├── notebooks/
│   └── 01_explore_api.ipynb   # Example notebook
├── src/
│   ├── __init__.py
│   ├── config.py              # Config loader
│   ├── home_assistant.py      # Main API client
│   └── secrets.py             # Secrets loader
├── tests/
│   ├── __init__.py
│   └── test_connection.py     # Automated connection test
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
     python -m unittest discover -s tests
     ```
   - You should see a successful connection message.
4. **Explore data in Jupyter:**
   - Open `notebooks/01_explore_api.ipynb` in VS Code or Jupyter Lab.

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

## Security

- **Never commit `config/secrets.yaml`!** It is gitignored by default.
- Use `config.example.yaml` and `secrets.example.yaml` as templates for sharing.

## Testing

- Tests are in the `tests/` folder and use the VS Code Python Test extension.
- Imports use the `src.` prefix for compatibility.

## Extending

- Add new collectors or analysis modules in `src/`.
- Add more tests in `tests/`.

---

**Questions?** Open an issue or check the code comments for more details.
