"""Provider registry for dynamic DNS provider lookup."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from meridian.updater.providers.base import DNSProvider

if TYPE_CHECKING:
    from meridian.updater.models import ProviderConfig

_REGISTRY: dict[str, type[DNSProvider]] = {}


def register_provider(name: str, cls: type[DNSProvider]) -> None:
    """Register a DNS provider class under a given name."""
    _REGISTRY[name] = cls
    logger.debug("Registered DNS provider: {name}", name=name)


def get_provider(config: ProviderConfig) -> DNSProvider:
    """Instantiate and return the configured DNS provider.

    Raises:
        ValueError: If the configured provider name is not registered.
    """
    cls = _REGISTRY.get(config.name)
    if cls is None:
        available = ", ".join(_REGISTRY.keys()) or "(none)"
        raise ValueError(
            f"Unknown DNS provider '{config.name}'. Available: {available}"
        )
    return cls(config)
