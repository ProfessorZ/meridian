# IP Detection

Multi-source fallback IP detection in [[meridian/updater/ip/detector.py#detect_ipv4]] and [[meridian/updater/ip/detector.py#detect_ipv6]]. Uses httpx async client with 10-second timeout per source.

Each source is queried independently via [[meridian/updater/ip/detector.py#_query_source]]. On `httpx.HTTPError`, the failure is logged at debug level and the next source is tried. This ensures resilience against any single provider being down.

## IPv4 Sources

Tried sequentially via [[meridian/updater/ip/detector.py#detect_ipv4]], returning the first success. Logs a warning if all sources fail.

- `https://api4.ipify.org`
- `https://ipv4.icanhazip.com`
- `https://ifconfig.me/ip`

## IPv6 Sources

Tried sequentially via [[meridian/updater/ip/detector.py#detect_ipv6]]. Returns `None` if unavailable — this is not treated as an error since many hosts lack IPv6 connectivity.

- `https://api6.ipify.org`
- `https://ipv6.icanhazip.com`
- `https://ifconfig.co/ip`
