# Provider System

Plugin architecture for DNS backends in `meridian/updater/providers/`. Allows adding new DNS providers without modifying core logic.

## Provider Interface

`DNSProvider` (ABC in `base.py`) defines the contract for all providers.

- `update_record(record, ip)` — create or update a DNS record (abstract)
- `close()` — release resources (optional override)

## Provider Registry

Factory pattern in `registry.py` for provider instantiation.

- `register_provider(name, cls)` — called at module import time to register a provider class
- `get_provider(config)` — looks up the configured provider name and instantiates it

Currently [[route53-provider]] is the only registered provider.
