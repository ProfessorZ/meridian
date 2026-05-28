# Meridian

Meridian is a Dynamic DNS (DDNS) updater for AWS Route53. It detects public IP changes and automatically updates DNS records using certificate-based [[authentication]] for credential-free operation.

## Architecture

The system is composed of several interconnected modules.

- [[polling-loop]] — the core async event loop that orchestrates IP detection and DNS updates
- [[ip-detection]] — multi-source fallback strategy for discovering public IPv4/IPv6
- [[provider-system]] — plugin architecture for DNS providers (currently [[route53-provider]])
- [[authentication]] — certificate-based AWS credential acquisition via IAM Roles Anywhere
- [[configuration]] — layered YAML + environment variable config with Pydantic validation
- [[data-models]] — Pydantic v2 models for config, state, and DNS records
- [[web-panel]] — optional FastAPI dashboard for monitoring status
- [[state-management]] — JSON file tracking last-known IPs to minimize DNS updates
- [[docker-deployment]] — multi-arch container with non-root execution

## Entry Points

The project defines two CLI entry points in `pyproject.toml`.

- `meridian` CLI → [[meridian/updater/main.py#main]] — loads config, configures logging, starts the [[polling-loop]]
- `meridian-panel` CLI → [[meridian/panel/main.py#run]] — starts the [[web-panel]] via uvicorn on port 8080

## Dependencies

Core runtime dependencies and their roles in the system.

- **pydantic v2** — type-safe validation for all [[data-models]]
- **pyyaml** — YAML parsing in [[configuration]]
- **httpx** — async HTTP client for [[ip-detection]] sources
- **loguru** — structured logging throughout all modules
- **boto3** — AWS SDK used by [[route53-provider]] for DNS API calls
- **fastapi / uvicorn / jinja2** — optional dependencies for the [[web-panel]]
