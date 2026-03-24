# Meridian DDNS Updater

Dynamic DNS updater that detects your public IP and updates DNS records automatically. Built for AWS Route53 with IAM Roles Anywhere — no static credentials required.

## Features

- **Multi-source IP detection** — IPv4 and IPv6 with automatic fallback across multiple providers
- **Change detection** — only updates DNS when your IP actually changes
- **IAM Roles Anywhere** — certificate-based authentication, no `AWS_ACCESS_KEY_ID` in your environment
- **Plugin architecture** — extensible `DNSProvider` base class for additional providers
- **Web panel** — optional FastAPI dashboard for status monitoring
- **Docker-ready** — slim image, non-root user, volume-mounted config and state

## Requirements

The `aws_signing_helper` binary is bundled automatically in the Docker image. If running outside Docker, download it manually from the [AWS IAM Roles Anywhere documentation](https://docs.aws.amazon.com/rolesanywhere/latest/userguide/credential-helper.html).

## Quick Start

```bash
# 1. Copy and edit configuration
cp config.example.yaml config.yaml
cp .env.example .env

# 2. Run with Docker Compose
docker compose up -d
```

## Configuration

See `config.example.yaml` for a fully annotated example. Key options:

| Option | Default | Description |
|--------|---------|-------------|
| `poll_interval` | `300` | Seconds between IP checks |
| `hosts[].ipv4` | `true` | Manage A record for this host |
| `hosts[].ipv6` | `false` | Manage AAAA record for this host |
| `hosts[].ttl` | `300` | DNS record TTL in seconds |

Environment variables (`MERIDIAN_POLL_INTERVAL`, `MERIDIAN_LOG_LEVEL`, `MERIDIAN_STATE_FILE`) override config file values.

## Architecture

```
meridian/
├── updater/           # Core DDNS logic
│   ├── main.py        # Polling loop
│   ├── config.py      # Config loading
│   ├── models.py      # Pydantic v2 models
│   ├── ip/            # IP detection
│   ├── providers/     # DNS provider plugins
│   └── auth/          # IAM Roles Anywhere
└── panel/             # Optional web UI
```

## Adding a DNS Provider

Implement the `DNSProvider` interface and register it:

```python
from meridian.updater.providers.base import DNSProvider
from meridian.updater.providers.registry import register_provider

class MyProvider(DNSProvider):
    def __init__(self, config):
        ...

    async def update_record(self, record, ip):
        ...

register_provider("myprovider", MyProvider)
```

## Running outside Docker

```bash
pip install -e .
# or with panel:
pip install -e ".[panel]"
meridian  # starts the updater
```

## Development

```bash
pip install -r requirements.txt
python -m meridian.updater.main
```

## License

MIT
