# @lat: [[ip-detection]]
"""Public IP detection with multiple fallback sources."""

from __future__ import annotations

import httpx
from loguru import logger

IPV4_SOURCES = [
    "https://api4.ipify.org",
    "https://ipv4.icanhazip.com",
    "https://ifconfig.me/ip",
]

IPV6_SOURCES = [
    "https://api6.ipify.org",
    "https://ipv6.icanhazip.com",
    "https://ifconfig.co/ip",
]

TIMEOUT = 10.0


async def _query_source(client: httpx.AsyncClient, url: str, timeout: float | None = None) -> str | None:
    """Query a single IP detection source, returning the IP or None on failure."""
    t = timeout or TIMEOUT
    try:
        resp = await client.get(url, timeout=t)
        resp.raise_for_status()
        ip = resp.text.strip()
        if ip:
            return ip
    except httpx.HTTPError as exc:
        logger.debug("Source {url} failed: {exc}", url=url, exc=exc)
    return None


async def detect_ipv4(
    sources: list[str] | None = None,
    timeout: float | None = None,
) -> str | None:
    """Detect public IPv4 address using fallback sources.

    Tries each source in order, returning the first successful result.
    Returns None if all sources fail.

    sources: optional override list (from config.ip_detection.ipv4_sources)
    timeout: optional override (from config.ip_detection.timeout)
    """
    effective_sources = sources or IPV4_SOURCES
    effective_timeout = timeout or TIMEOUT

    async with httpx.AsyncClient() as client:
        for url in effective_sources:
            ip = await _query_source(client, url, timeout=effective_timeout)
            if ip:
                logger.debug("IPv4 detected as {ip} from {url}", ip=ip, url=url)
                return ip
    logger.warning("All IPv4 detection sources failed")
    return None


async def detect_ipv6(
    sources: list[str] | None = None,
    timeout: float | None = None,
) -> str | None:
    """Detect public IPv6 address using fallback sources.

    Tries each source in order, returning the first successful result.
    Returns None if all sources fail or if the host has no IPv6 connectivity.

    sources: optional override list (from config.ip_detection.ipv6_sources)
    timeout: optional override (from config.ip_detection.timeout)
    """
    effective_sources = sources or IPV6_SOURCES
    effective_timeout = timeout or TIMEOUT

    async with httpx.AsyncClient() as client:
        for url in effective_sources:
            ip = await _query_source(client, url, timeout=effective_timeout)
            if ip:
                logger.debug("IPv6 detected as {ip} from {url}", ip=ip, url=url)
                return ip
    logger.debug("No IPv6 address detected (this may be expected)")
    return None
