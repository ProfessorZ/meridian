# @lat: [[data-models]]
"""Pydantic v2 models for Meridian DDNS updater."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class RecordType(str, Enum):
    A = "A"
    AAAA = "AAAA"


class IPState(BaseModel):  # @lat: data-models#Core Types
    """Cached IP state persisted between polling cycles."""

    ipv4: str | None = None
    ipv6: str | None = None

    def has_changed(self, new_ipv4: str | None, new_ipv6: str | None) -> bool:
        return self.ipv4 != new_ipv4 or self.ipv6 != new_ipv6


class DNSRecord(BaseModel):
    """A single DNS record to manage."""

    hostname: str
    zone_id: str
    record_type: RecordType
    ttl: int = 300


class HostConfig(BaseModel):  # @lat: data-models#Core Types
    """Per-host configuration specifying which records to manage."""

    hostname: str
    zone_id: str
    ttl: int = 300
    ipv4: bool = True
    ipv6: bool = False

    def to_records(self) -> list[DNSRecord]:
        """Expand host config into individual DNS records."""
        records: list[DNSRecord] = []
        if self.ipv4:
            records.append(
                DNSRecord(
                    hostname=self.hostname,
                    zone_id=self.zone_id,
                    record_type=RecordType.A,
                    ttl=self.ttl,
                )
            )
        if self.ipv6:
            records.append(
                DNSRecord(
                    hostname=self.hostname,
                    zone_id=self.zone_id,
                    record_type=RecordType.AAAA,
                    ttl=self.ttl,
                )
            )
        return records


class IAMRolesAnywhereConfig(BaseModel):  # @lat: data-models#Config Types
    """Configuration for AWS IAM Roles Anywhere authentication."""

    trust_anchor_arn: str
    profile_arn: str
    role_arn: str
    certificate_path: Path
    private_key_path: Path
    signing_helper_path: Path = Path("/usr/local/bin/aws_signing_helper")
    region: str = "us-east-1"


class Route53ProviderConfig(BaseModel):
    """Route53-specific provider configuration."""

    iam_roles_anywhere: IAMRolesAnywhereConfig


class ProviderConfig(BaseModel):
    """DNS provider configuration."""

    name: str = "route53"
    route53: Route53ProviderConfig | None = None


class AppConfig(BaseModel):  # @lat: data-models#Config Types
    """Top-level application configuration."""

    poll_interval: int = Field(default=300, ge=10, description="Seconds between IP checks")
    state_file: Path = Path("/var/lib/meridian/state.json")
    hosts: list[HostConfig] = Field(default_factory=list)
    provider: ProviderConfig = Field(default_factory=ProviderConfig)
    log_level: str = "INFO"
