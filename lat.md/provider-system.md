# Provider System

Plugin architecture for DNS backends in `meridian/updater/providers/`. Allows adding new DNS providers without modifying core logic.

## Provider Interface

[[meridian/updater/providers/base.py#DNSProvider]] (ABC) defines the contract for all providers.

- [[meridian/updater/providers/base.py#DNSProvider#update_record|update_record(record, ip)]] — create or update a DNS record (abstract)
- `close()` — release resources (optional override, no-op by default)

Failures are signaled via [[meridian/updater/providers/base.py#ProviderError]], caught per-record by the [[polling-loop]].

## Provider Registry

Factory pattern in [[meridian/updater/providers/registry.py#register_provider]] and [[meridian/updater/providers/registry.py#get_provider]] for provider instantiation.

- `register_provider(name, cls)` — called at module import time to register a provider class
- `get_provider(config)` — looks up the configured provider name and instantiates it; raises `ValueError` if not found

Currently [[route53-provider]] is the only registered provider. New providers register themselves by calling `register_provider()` at import time (side-effect registration pattern).
