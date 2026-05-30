"""Tests for public IP detection with fallback sources (uses respx for HTTP mocking)."""

import httpx
import pytest
import respx

from meridian.updater.ip.detector import (
    IPV4_SOURCES,
    IPV6_SOURCES,
    TIMEOUT,
    detect_ipv4,
    detect_ipv6,
)

# @lat: [[tests#IP Detection#Falls back through sources on failure]]
@respx.mock
@pytest.mark.asyncio
async def test_detect_ipv4_falls_back_on_first_failure():
    """First source fails, second succeeds → we get the IP from the second source."""
    respx.get(IPV4_SOURCES[0]).mock(side_effect=httpx.ConnectError("boom"))
    respx.get(IPV4_SOURCES[1]).mock(return_value=httpx.Response(200, text="203.0.113.42"))
    # third not called

    ip = await detect_ipv4()
    assert ip == "203.0.113.42"


@respx.mock
@pytest.mark.asyncio
async def test_detect_ipv4_all_sources_fail():
    for url in IPV4_SOURCES:
        respx.get(url).mock(side_effect=httpx.HTTPError("down"))
    ip = await detect_ipv4()
    assert ip is None


# @lat: [[tests#IP Detection#Returns None for IPv6 when unavailable]]
@respx.mock
@pytest.mark.asyncio
async def test_detect_ipv6_returns_none_on_all_failure():
    for url in IPV6_SOURCES:
        respx.get(url).mock(side_effect=httpx.ConnectError("no ipv6"))
    ip = await detect_ipv6()
    assert ip is None
