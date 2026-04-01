"""Abstract DNS provider interface."""  # @lat: provider-system#Provider Interface

from __future__ import annotations

from abc import ABC, abstractmethod

from meridian.updater.models import DNSRecord


class DNSProvider(ABC):
    """Base class for DNS provider implementations.

    All providers must implement `update_record` to handle upserting
    a DNS record with the given IP address.
    """

    @abstractmethod
    async def update_record(self, record: DNSRecord, ip: str) -> None:
        """Create or update a DNS record to point to the given IP.

        Args:
            record: The DNS record to update (hostname, zone, type, TTL).
            ip: The IP address value to set.

        Raises:
            ProviderError: If the DNS update fails.
        """

    async def close(self) -> None:
        """Release any resources held by the provider."""


class ProviderError(Exception):
    """Raised when a DNS provider operation fails."""
