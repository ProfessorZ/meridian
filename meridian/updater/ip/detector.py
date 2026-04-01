# @lat: [[meridian#IP Detection]]
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


async def _query_source(client: httpx.AsyncClient, url: str) -> str | None:
    """Query a single IP detection source, returning the IP or None on failure."""
    try:
        resp = await client.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        ip = resp.text.strip()
        if ip:
            return ip
    except httpx.HTTPError as exc:
        logger.debug("Source {url} failed: {exc}", url=url, exc=exc)
    return None


async def detect_ipv4() -> str | None:
    """Detect public IPv4 address using fallback sources.

    Tries each source in order, returning the first successful result.
    Returns None if all sources fail.
    """
    async with httpx.AsyncClient() as client:
        for url in IPV4_SOURCES:
            ip = await _query_source(client, url)
            if ip:
                logger.debug("IPv4 detected as {ip} from {url}", ip=ip, url=url)
                return ip
    logger.warning("All IPv4 detection sources failed")
    return None


async def detect_ipv6() -> str | None:
    """Detect public IPv6 address using fallback sources.

    Tries each source in order, returning the first successful result.
    Returns None if all sources fail or if the host has no IPv6 connectivity.
    """
    async with httpx.AsyncClient() as client:
        for url in IPV6_SOURCES:
            ip = await _query_source(client, url)
            if ip:
                logger.debug("IPv6 detected as {ip} from {url}", ip=ip, url=url)
                return ip
    logger.debug("No IPv6 address detected (this may be expected)")
    return None
