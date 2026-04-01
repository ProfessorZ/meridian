"""Meridian DDNS updater — main polling loop."""  # @lat: polling-loop

from __future__ import annotations

import asyncio
import json
import signal
import sys
from pathlib import Path

from loguru import logger

from meridian.updater.config import load_config
from meridian.updater.ip.detector import detect_ipv4, detect_ipv6
from meridian.updater.models import AppConfig, IPState, RecordType
from meridian.updater.providers.base import ProviderError
from meridian.updater.providers.registry import get_provider

# Ensure Route53 provider is registered on import
import meridian.updater.providers.route53  # noqa: F401


def _configure_logging(level: str) -> None:
    """Set up loguru with structured console output."""
    logger.remove()
    logger.add(
        sys.stderr,
        level=level.upper(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
    )


def _load_state(path: Path) -> IPState:  # @lat: state-management#Load and Save
    """Load cached IP state from disk."""
    if path.exists():
        try:
            data = json.loads(path.read_text())
            return IPState(**data)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Corrupt state file, resetting: {exc}", exc=exc)
    return IPState()


def _save_state(path: Path, state: IPState) -> None:  # @lat: state-management#Load and Save
    """Persist IP state to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state.model_dump_json(indent=2))


async def _poll_and_update(config: AppConfig) -> None:  # @lat: polling-loop
    """Run a single poll-and-update cycle.

    Detects current public IPs, compares against cached state,
    and updates DNS records only when changes are detected.
    """
    provider = get_provider(config.provider)
    state = _load_state(config.state_file)

    current_ipv4 = await detect_ipv4()
    current_ipv6 = await detect_ipv6()

    if not state.has_changed(current_ipv4, current_ipv6):
        logger.debug("No IP change detected, skipping update")
        return

    logger.info(
        "IP change detected: IPv4 {old4} -> {new4}, IPv6 {old6} -> {new6}",
        old4=state.ipv4,
        new4=current_ipv4,
        old6=state.ipv6,
        new6=current_ipv6,
    )

    for host in config.hosts:
        for record in host.to_records():
            ip = current_ipv4 if record.record_type == RecordType.A else current_ipv6
            if ip is None:
                logger.warning(
                    "No {type} address available for {host}, skipping",
                    type=record.record_type.value,
                    host=record.hostname,
                )
                continue
            try:
                await provider.update_record(record, ip)
            except ProviderError as exc:
                logger.error(
                    "Failed to update {host} ({type}): {exc}",
                    host=record.hostname,
                    type=record.record_type.value,
                    exc=exc,
                )

    new_state = IPState(ipv4=current_ipv4, ipv6=current_ipv6)
    _save_state(config.state_file, new_state)
    await provider.close()


async def run(config: AppConfig) -> None:  # @lat: polling-loop#Graceful Shutdown
    """Main loop — polls for IP changes at the configured interval."""
    logger.info("Meridian DDNS updater starting (poll interval: {s}s)", s=config.poll_interval)

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _shutdown_handler() -> None:
        logger.info("Received shutdown signal, stopping")
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _shutdown_handler)

    while not stop_event.is_set():
        try:
            await _poll_and_update(config)
        except Exception as exc:
            logger.exception("Unhandled error during poll cycle: {exc}", exc=exc)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=config.poll_interval)
        except asyncio.TimeoutError:
            pass


def main() -> None:
    """Entry point for the Meridian DDNS updater."""
    config = load_config()
    _configure_logging(config.log_level)
    logger.info("Meridian DDNS updater initialized")
    asyncio.run(run(config))


if __name__ == "__main__":
    main()
