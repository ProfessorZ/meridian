# Polling Loop

The main orchestration loop in [[meridian/updater/main.py#_poll_and_update]]. Runs on a configurable interval (default 300s), coordinating IP detection, change comparison, and DNS updates.

Each cycle:
1. Instantiate the DNS provider via [[provider-system]]
2. Load cached IP state from disk via [[state-management]]
3. Run [[ip-detection]] for IPv4 and IPv6
4. Compare against cached state — skip if unchanged
5. For each configured host, expand to DNS records via [[meridian/updater/models.py#HostConfig|HostConfig.to_records()]] and call [[meridian/updater/providers/base.py#DNSProvider|provider.update_record()]]
6. Persist new state to disk **only if the entire batch succeeded** (no ProviderErrors). Any failure leaves the old state so the affected records are retried next cycle.
7. Wait for next cycle or shutdown signal

Per-record error handling ensures a single failed update does not block other hosts — failures are logged via [[meridian/updater/providers/base.py#ProviderError]] and the loop continues. The clean-batch state rule (see [[state-management]]) guarantees that transient provider errors cause automatic retries without waiting for the next public IP change.

Provider instances are always closed via `try/finally` (even on early returns or unexpected exceptions inside a cycle).

## Graceful Shutdown

Signal-driven shutdown via [[meridian/updater/main.py#run]]. Handles SIGTERM and SIGINT using `asyncio.Event`. The polling wait uses `asyncio.wait_for()` so shutdown is near-instant regardless of poll interval. Signal handlers set the event, breaking the loop cleanly.

## Logging Setup

Configures loguru via [[meridian/updater/main.py#_configure_logging]]. Removes the default handler and adds a structured format with timestamps, severity levels, and logger names to stderr.
