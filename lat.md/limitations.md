# Known Limitations

This document captures gaps between Meridian's documented architecture and its current implementation. These limitations are the primary drivers for the feature-completeness work and are referenced from code and other lat.md sections.

## Async Contract Violations

Several components declare async interfaces but execute blocking I/O, causing the event loop in the [[polling-loop]] to stall during every cycle.

### Subprocess credential acquisition blocks

`obtain_credentials` in [[meridian/updater/auth/iam_roles_anywhere.py#obtain_credentials]] uses `subprocess.run` with up to 30s timeout. It is called synchronously from `Route53Provider.__init__` during provider instantiation in the async `_poll_and_update` path.

### Route53 API calls block

`update_record`, `_create_client`, and `_refresh_credentials` in the Route53 provider perform synchronous boto3 calls with no `await` or executor dispatch. This contradicts the async HTTP client usage highlighted in [[ip-detection]] and the overall async design.

## Provider Extensibility (Resolved)

The previous limitation has been fixed. `ProviderConfig` now uses `extra='allow'`, so new providers can define their own configuration blocks without changes to core data models. See [[roadmap#In Progress (Feature-Completeness Milestone)#True plugin architecture (Completed)]] and [[provider-system]].

## State Persistence Semantics (Resolved)

The previous "always advance state" behavior (even on total failure) has been fixed. State is now persisted only after a clean batch with zero ProviderErrors, so failed records are retried automatically on the next cycle. See [[state-management]] and the test spec [[tests#State Management#Persists state only after clean update batch]].

## Missing Infrastructure

No automated test suite exists despite references to testing in CHANGELOG and PR templates. GitHub Actions workflows are absent. Development tooling (ruff, mypy, pytest configuration) is not present in `pyproject.toml`.

## Production Readiness Gaps

Several operational features expected in a production DDNS tool are absent, increasing risk for credential or config problems.

- No `--dry-run` or startup validation mode to exercise credentials and IP detection without mutating DNS.
- Hard-coded IP detection sources and timeouts with no configuration override.
- Panel endpoint logs at INFO level on every request due to unconditional `load_config` calls.
- Version string in the FastAPI app is hard-coded and drifts from `meridian.version`.
- Limited observability: no structured events for changes or persistent failures beyond log lines.