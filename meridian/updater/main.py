# @lat: [[polling-loop]]
"""Meridian DDNS updater — main polling loop."""

from __future__ import annotations

import argparse
import asyncio
import json
import signal
import sys
from pathlib import Path

from datetime import datetime

import httpx
from loguru import logger

from meridian.updater.config import load_config
from meridian.updater.ip.detector import detect_ipv4, detect_ipv6
from meridian.updater.models import AppConfig, IPState, RecordType
from meridian.updater.providers.base import ProviderError
from meridian.updater.providers.registry import get_provider
from meridian.version import __version__

# Ensure Route53 provider is registered on import
import meridian.updater.providers.route53  # noqa: F401


async def _send_webhook(url: str, payload: dict) -> None:
    """Fire-and-forget webhook POST. Errors are only logged."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
    except Exception as exc:
        logger.warning("Webhook delivery failed to {url}: {exc}", url=url, exc=exc)


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


async def _poll_and_update(config: AppConfig, dry_run: bool = False) -> bool:  # @lat: polling-loop
    """Run a single poll-and-update cycle.

    Detects current public IPs, compares against cached state,
    and updates DNS records only when changes are detected.

    State is only persisted when the batch completes with zero
    ProviderErrors (clean batch policy). Any failure leaves the
    previous state on disk so the affected records are retried on
    the next poll cycle even without a new IP change.

    The provider is always closed via try/finally, even on early
    returns or unexpected exceptions.

    Returns True if a change was processed (even in dry-run), False if skipped.
    """
    provider = get_provider(config.provider)
    try:
        state = _load_state(config.state_file)

        ip_cfg = config.ip_detection or None
        current_ipv4 = await detect_ipv4(
            sources=ip_cfg.ipv4_sources if ip_cfg else None,
            timeout=ip_cfg.timeout if ip_cfg else None,
        )
        current_ipv6 = await detect_ipv6(
            sources=ip_cfg.ipv6_sources if ip_cfg else None,
            timeout=ip_cfg.timeout if ip_cfg else None,
        )

        if not state.has_changed(current_ipv4, current_ipv6):
            logger.debug("No IP change detected, skipping update")
            # Still update last_checked for panel visibility
            fresh_state = IPState(
                ipv4=state.ipv4,
                ipv6=state.ipv6,
                last_checked=datetime.utcnow(),
            )
            _save_state(config.state_file, fresh_state)
            return False

        logger.info(
            "IP change detected: IPv4 {old4} -> {new4}, IPv6 {old6} -> {new6}",
            old4=state.ipv4,
            new4=current_ipv4,
            old6=state.ipv6,
            new6=current_ipv6,
        )

        if dry_run:
            logger.info("DRY-RUN: would perform the following updates (no actual changes):")

        update_errors = 0
        attempted = 0
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
                attempted += 1
                if dry_run:
                    logger.info(
                        "DRY-RUN: would update {type} {host} -> {ip} (zone {zone}, ttl {ttl})",
                        type=record.record_type.value,
                        host=record.hostname,
                        ip=ip,
                        zone=record.zone_id,
                        ttl=record.ttl,
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
                    update_errors += 1

        if dry_run:
            if attempted == 0:
                logger.info("DRY-RUN: no records would have been updated (no hosts or all skipped for missing IP)")
            return True

        notif = config.notifications
        change_happened = update_errors == 0

        if change_happened:
            new_state = IPState(
                ipv4=current_ipv4,
                ipv6=current_ipv6,
                last_checked=datetime.utcnow(),
            )
            _save_state(config.state_file, new_state)

            if notif and notif.webhook_url and notif.on_change:
                payload = {
                    "event": "ip_changed",
                    "ipv4": current_ipv4,
                    "ipv6": current_ipv6,
                    "hosts_updated": len(config.hosts),
                }
                asyncio.create_task(_send_webhook(notif.webhook_url, payload))
        else:
            logger.warning(
                "{count} update(s) failed; not advancing state so failed records will be retried next cycle",
                count=update_errors,
            )
            # Update state with error info even if we don't advance IPs
            error_state = IPState(
                ipv4=state.ipv4,
                ipv6=state.ipv6,
                last_checked=datetime.utcnow(),
                last_error=f"{update_errors} update(s) failed",
            )
            _save_state(config.state_file, error_state)

            if notif and notif.webhook_url and notif.on_error:
                if update_errors >= notif.error_threshold:
                    payload = {
                        "event": "update_errors",
                        "ipv4": current_ipv4,
                        "ipv6": current_ipv6,
                        "error_count": update_errors,
                        "attempted_records": attempted,
                    }
                    asyncio.create_task(_send_webhook(notif.webhook_url, payload))

        return True
    finally:
        await provider.close()


async def run(config: AppConfig, dry_run: bool = False, once: bool = False) -> None:  # @lat: polling-loop#Graceful Shutdown
    # @lat: [[tests#Polling Loop#Graceful shutdown on SIGTERM/SIGINT]]
    """Main loop — polls for IP changes at the configured interval.

    When once=True, runs exactly one cycle then exits (respects dry_run).
    """
    mode = "DRY-RUN" if dry_run else "normal"
    logger.info(
        "Meridian DDNS updater starting in {mode} mode (poll interval: {s}s)",
        mode=mode,
        s=config.poll_interval,
    )

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _shutdown_handler() -> None:
        logger.info("Received shutdown signal, stopping")
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _shutdown_handler)

    while not stop_event.is_set():
        try:
            did_work = await _poll_and_update(config, dry_run=dry_run)
            if once:
                logger.info("Single cycle (--once) completed")
                break
        except Exception as exc:
            logger.exception("Unhandled error during poll cycle: {exc}", exc=exc)
        if once:
            break
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=config.poll_interval)
        except asyncio.TimeoutError:
            pass


# @lat: [[tests#CLI#Supports --dry-run / --validate]]
# @lat: [[tests#CLI#Supports --once for single execution]]
# @lat: [[tests#CLI#Supports --config, --version, and standard help]]
def main() -> None:
    """Entry point for the Meridian DDNS updater."""
    parser = argparse.ArgumentParser(
        prog="meridian",
        description="Meridian DDNS updater for AWS Route53 with IAM Roles Anywhere",
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to config file (overrides MERIDIAN_CONFIG env var)",
    )
    parser.add_argument(
        "--dry-run", "--validate",
        action="store_true",
        dest="dry_run",
        help="Detect IPs, exercise credentials, and log what would be updated without making DNS changes",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single poll-and-update cycle then exit (useful for testing and cron)",
    )
    parser.add_argument(
        "--version", "-V",
        action="store_true",
        help="Print version and exit",
    )
    args = parser.parse_args()

    if args.version:
        print(f"meridian {__version__}")
        return

    config = load_config(args.config)
    _configure_logging(config.log_level)
    logger.info("Meridian DDNS updater initialized (version {v})", v=__version__)

    if args.dry_run:
        logger.info("DRY-RUN mode enabled — no DNS records will be modified")

    asyncio.run(run(config, dry_run=args.dry_run, once=args.once))


if __name__ == "__main__":
    main()
