# Route53 Provider

AWS Route53 DNS implementation in [[meridian/updater/providers/route53.py#Route53Provider]]. Extends the [[provider-system#Provider Interface]] using [[authentication]] credentials to manage DNS records.

Self-registers via `register_provider("route53", Route53Provider)` at module import time, following the [[provider-system#Provider Registry]] pattern.

## DNS Update

Performs Route53 `UPSERT` via [[meridian/updater/providers/route53.py#Route53Provider#update_record]]. Builds a `ChangeBatch` with the record's hostname, type (A/AAAA), TTL, and new IP value. Uses `change_resource_record_sets()` from the boto3 Route53 client.

## Credential Lifecycle

Manages temporary AWS credentials with automatic refresh on expiry via [[meridian/updater/providers/route53.py#Route53Provider#_refresh_credentials]].

- `_create_client()` — obtains credentials via [[authentication]] and creates a boto3 Route53 client session
- `_refresh_credentials()` — re-obtains credentials on `ExpiredTokenException` or `InvalidSignatureException`, then retries the failed operation once
