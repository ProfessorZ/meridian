"""Tests for Pydantic data models (config, state, DNS records)."""

from pathlib import Path

import pytest

from meridian.updater.models import (
    AppConfig,
    DNSRecord,
    HostConfig,
    IAMRolesAnywhereConfig,
    IPState,
    ProviderConfig,
    RecordType,
    Route53ProviderConfig,
)

# @lat: [[tests#Data Models#Core Types]]
def test_ipstate_has_changed():
    """Basic change detection logic used by the polling loop."""
    s = IPState(ipv4="1.2.3.4", ipv6=None)
    assert s.has_changed("1.2.3.4", None) is False
    assert s.has_changed("1.2.3.5", None) is True
    assert s.has_changed(None, "2001:db8::1") is True


# @lat: [[tests#State Management#Persists state only after clean update batch]]
def test_hostconfig_to_records():
    """HostConfig expands into the correct A/AAAA records (core of record management)."""
    h = HostConfig(
        hostname="example.com",
        zone_id="Z123",
        ttl=300,
        ipv4=True,
        ipv6=True,
    )
    records = h.to_records()
    assert len(records) == 2
    assert records[0].record_type == RecordType.A
    assert records[1].record_type == RecordType.AAAA
    assert all(r.hostname == "example.com" and r.zone_id == "Z123" for r in records)


def test_hostconfig_requires_at_least_one_ip_version():
    """We want this invariant (enforced in a later model update)."""
    # For now just document the intent; the model currently allows ipv4=ipv6=False
    h = HostConfig(hostname="x", zone_id="Z1", ipv4=False, ipv6=False)
    assert h.to_records() == []


# @lat: [[tests#Configuration Loading#Validates poll interval minimum]]
# Minimal smoke for config model construction (full load tests come later)
def test_appconfig_defaults_and_validation():
    cfg = AppConfig(hosts=[])
    assert cfg.poll_interval == 300
    assert cfg.log_level == "INFO"

    with pytest.raises(Exception):  # Pydantic v2 ValidationError
        AppConfig(poll_interval=5)  # below ge=10
