# IP Detection

Multi-source fallback IP detection in `meridian/updater/ip/detector.py`. Uses httpx async client with 10-second timeout per source.

## IPv4 Sources

Tried sequentially, returning the first success: ipify API v4, icanhazip v4, ifconfig.me.

## IPv6 Sources

Tried sequentially: ipify API v6, icanhazip v6, ifconfig.co. Returns None if unavailable (not treated as an error).

## Query Strategy

Each source is queried independently via `_query_source()`. On `httpx.HTTPError`, the failure is logged at debug level and the next source is tried. This ensures resilience against any single provider being down.
