# Route53 Provider

AWS Route53 DNS implementation in `meridian/updater/providers/route53.py`. Extends the [[provider-system]] interface using [[authentication]] credentials to manage DNS records.

## DNS Update

Performs Route53 `UPSERT` via `change_resource_record_sets()`. Builds a ChangeBatch with the record's hostname, type (A/AAAA), TTL, and new IP value.

## Credential Lifecycle

Manages temporary AWS credentials with automatic refresh on expiry.

- `_create_client()` — obtains credentials via [[authentication]] and creates a boto3 Route53 client
- `_refresh_credentials()` — re-obtains credentials on `ExpiredTokenException` or `InvalidSignatureException`, then retries the failed operation once
