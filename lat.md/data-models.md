# Data Models

Pydantic v2 models in `meridian/updater/models.py` defining the application's type-safe schema for configuration, state, and DNS records.

## Core Types

Domain types representing DNS records and runtime state.

- [[meridian/updater/models.py#RecordType]] — enum: `A` (IPv4), `AAAA` (IPv6)
- [[meridian/updater/models.py#IPState]] — cached IP state with `has_changed()` comparison method, used by [[state-management]]
- [[meridian/updater/models.py#DNSRecord]] — hostname, zone_id, record_type, ttl for a single DNS record
- [[meridian/updater/models.py#HostConfig]] — per-host settings with `to_records()` that expands into `DNSRecord` list based on ipv4/ipv6 flags

## Config Types

Hierarchical configuration models validated at startup.

- [[meridian/updater/models.py#IAMRolesAnywhereConfig]] — [[authentication]] parameters (ARNs, cert paths, region with defaults)
- [[meridian/updater/models.py#Route53ProviderConfig]] — wraps `IAMRolesAnywhereConfig`
- [[meridian/updater/models.py#ProviderConfig]] — provider selection (name + provider-specific config block). Uses `extra='allow'` so new providers can be added without modifying this model.
- [[meridian/updater/models.py#AppConfig]] — top-level: poll_interval (≥10s), state_file, hosts list, provider, log_level, ip_detection, notifications
