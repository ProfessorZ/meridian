---
lat:
  require-code-mention: true
---

# Tests

Test specifications for the Meridian DDNS updater. These sections define the expected behavior that must be verified by automated tests. Every leaf section requires exactly one `# @lat:` reference in test code.

## Data Models

Core Pydantic models for state, hosts, records, and configuration.

### Core Types

IPState.has_changed, DNSRecord, HostConfig.to_records, RecordType, and provider config models.

## Configuration Loading

Configuration loading behavior, including layered sources and validation rules.

### Loads YAML with environment overrides

A configuration file is loaded and specific environment variables (`MERIDIAN_POLL_INTERVAL`, `MERIDIAN_LOG_LEVEL`, `MERIDIAN_STATE_FILE`) override values from the file or defaults. Missing files produce a warning but still yield a valid `AppConfig`.

### Validates poll interval minimum

A `poll_interval` below 10 seconds is rejected at Pydantic validation time with a clear error.

## IP Detection

Multi-source fallback logic for public IPv4 and IPv6 discovery.

### Falls back through sources on failure

When the first IPv4 or IPv6 detection source returns an error or empty body, subsequent sources in the list are tried until one succeeds or all have failed.

### Returns None for IPv6 when unavailable

`detect_ipv6` returns `None` (not an exception) when the host has no IPv6 connectivity or all sources fail; this is logged at debug level only.

## State Management

JSON persistence of last-known IPs with graceful handling of missing or corrupt files.

### Loads empty state on missing or corrupt file

`_load_state` returns a default `IPState` (all fields None) when the state file is absent or contains invalid JSON, logging a warning for corruption.

### Persists state only after clean update batch

After an IP change is detected, the new state is written only when every `update_record` call for the affected hosts succeeded. Any `ProviderError` leaves the previous state in place so the failed records will be retried on the next cycle.

### Tracks last_checked and last_error

`IPState` is enriched on every cycle with `last_checked` (UTC timestamp) and `last_error` (descriptive string when failures occur). These are surfaced in the web panel and available for notifications.

## Polling Loop

Core orchestration, change detection, per-record error isolation, and signal-driven shutdown.

### Per-record errors do not abort cycle

A `ProviderError` raised for one host/record is caught, logged, and does not prevent updates to other hosts in the same poll cycle or the subsequent state save decision.

### Graceful shutdown on SIGTERM/SIGINT

The main run loop installs handlers for SIGTERM and SIGINT that set an event. The wait between polls uses a timeout so shutdown occurs promptly without waiting for the full interval.

## Route53 Provider

Behavior and error contract for the built-in AWS Route53 DNS provider implementation.

### Refreshes credentials and retries once on auth errors

On auth-related Route53 errors the provider fetches fresh credentials and retries the change exactly once before surfacing a `ProviderError`.

### Always raises ProviderError on failure

Network errors, permission errors, or other boto3 failures are converted to `ProviderError` with a descriptive message; raw client exceptions never escape to the caller.

## Provider Registry and Extensibility

The registry and configuration model contract that enables (or currently limits) adding DNS providers.

### Rejects unknown provider names at instantiation time

`get_provider` raises `ValueError` listing available providers when the configured `name` is not registered.

### Supports additional providers via config extension

After the extensibility refactor, new providers register themselves and accept config under an arbitrary key without requiring changes to core Pydantic models. (Implemented — see `models.py:ProviderConfig` + updated README.)

## Web Panel

Read-only monitoring dashboard behavior and health endpoint contract.

### Serves current state and config without secrets

The index page renders the loaded `AppConfig` (sanitized) and latest `IPState` but never exposes certificate paths or private key material.

### Health endpoint always returns ok

`GET /health` returns `{"status": "ok"}` with 200 regardless of whether the updater is running or DNS updates are succeeding.

## CLI

Command-line interface behavior for the `meridian` entry point.

### Supports --dry-run / --validate

`meridian --dry-run` (or `--validate`) performs IP detection and provider/credential initialization but never calls `update_record`. It logs the changes it *would* have made and exits successfully.

### Supports --once for single execution

`meridian --once` runs exactly one poll cycle (respecting --dry-run if also provided) and then exits cleanly. Useful for manual testing and scheduled jobs.

### Supports --config, --version, and standard help

`--config` / `-c` overrides the config file location. `--version` / `-V` prints the version from `meridian.version` and exits. `--help` shows usage.

## Notifications

Optional webhook-based alerting for important DDNS events.

### Webhook on successful IP change

When `notifications.webhook_url` is set and `on_change: true`, a JSON payload with event `ip_changed` is POSTed after a clean successful batch of DNS updates.

### Webhook on repeated update errors

When `notifications.webhook_url` is set and `on_error: true`, a JSON payload with event `update_errors` is sent once the number of failures in a cycle meets or exceeds `error_threshold`.