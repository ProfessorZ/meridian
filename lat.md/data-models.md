# Data Models

Pydantic v2 models in `meridian/updater/models.py` defining the application's type-safe schema for configuration, state, and DNS records.

## Core Types

Domain types representing DNS records and runtime state.

- `RecordType` — enum: `A` (IPv4), `AAAA` (IPv6)
- `IPState` — cached IP state with `has_changed()` comparison method, used by [[state-management]]
- `DNSRecord` — hostname, zone_id, record_type, ttl for a single DNS record
- `HostConfig` — per-host settings with `to_records()` that expands into `DNSRecord` list

## Config Types

Hierarchical configuration models validated at startup.

- `IAMRolesAnywhereConfig` — [[authentication]] parameters (ARNs, cert paths, region)
- `Route53ProviderConfig` — wraps `IAMRolesAnywhereConfig`
- `ProviderConfig` — provider selection (name + provider-specific config block)
- `AppConfig` — top-level: poll_interval, state_file, hosts, provider, log_level
