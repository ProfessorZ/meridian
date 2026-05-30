# Route53 Provider

AWS Route53 DNS implementation in [[meridian/updater/providers/route53.py#Route53Provider]]. Extends the [[provider-system#Provider Interface]] using [[authentication]] credentials to manage DNS records.

Self-registers via `register_provider("route53", Route53Provider)` at module import time, following the [[provider-system#Provider Registry]] pattern.

## DNS Update

Performs Route53 `UPSERT` via [[meridian/updater/providers/route53.py#Route53Provider#update_record]]. Builds a `ChangeBatch` with the record's hostname, type (A/AAAA), TTL, and new IP value. The blocking `change_resource_record_sets()` call is dispatched via `asyncio.to_thread` so the [[polling-loop]] event loop is never stalled.

## Credential Lifecycle

Manages temporary AWS credentials with automatic refresh on expiry via [[meridian/updater/providers/route53.py#Route53Provider#_refresh_credentials]] (now fully async after the auth refactor).

- `_create_client()` / `_ensure_client()` — lazily obtains credentials via [[authentication]] and creates a boto3 Route53 client session
- `_refresh_credentials()` — re-obtains credentials on `ExpiredTokenException` or `InvalidSignatureException`, then retries the failed operation exactly once. The retry path is wrapped so every failure (including the retry itself) is raised as `ProviderError`.
- `close()` — best-effort release of the boto3 client via `asyncio.to_thread` (called by the [[polling-loop]] after every cycle).
