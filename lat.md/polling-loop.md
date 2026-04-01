# Polling Loop

The main orchestration loop in `meridian/updater/main.py`. Runs on a configurable interval (default 300s).

Each cycle:
1. Instantiate the DNS provider via [[provider-system]]
2. Load cached IP state from disk via [[state-management]]
3. Run [[ip-detection]] for IPv4 and IPv6 concurrently
4. Compare against cached state — skip if unchanged
5. For each configured host, expand to DNS records and call provider.update_record()
6. Persist new state to disk
7. Wait for next cycle or shutdown signal

## Graceful Shutdown

Handles SIGTERM and SIGINT via `asyncio.Event`. The polling wait uses `asyncio.wait_for()` so shutdown is near-instant regardless of poll interval. Signal handlers set the event, breaking the loop cleanly.
