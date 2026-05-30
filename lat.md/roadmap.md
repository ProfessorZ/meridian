# Roadmap and Future Work

Meridian's evolution plan, including items addressed by the current feature-completeness effort and explicitly deferred items. This section is the single source of truth for prioritization and prevents scope creep.

## In Progress (Feature-Completeness Milestone)

Items required to make the system match its own architectural claims and become production-ready for the documented use case.

### Core correctness and reliability

The highest-priority work eliminates blocking I/O, repairs retry logic, and defines a trustworthy state persistence policy.

- Eliminate blocking I/O in the async polling and provider paths using `asyncio.to_thread` and native subprocess primitives.
- Repair credential refresh retry logic so all failure modes surface as `ProviderError`.
- Define and implement a clear state persistence policy (clean batch success vs. per-host tracking) with corresponding tests and documentation updates.
- Ensure provider resources are always released via try/finally and consider cross-cycle reuse.

### True plugin architecture (Completed)

`ProviderConfig` now uses `extra='allow'`. New providers can be added by implementing `DNSProvider`, registering themselves, and using their own top-level key in the provider config block — no changes required to `models.py`.

- Refactored `ProviderConfig` (extra='allow') so additional providers can be added with only new code in `providers/` and optional config keys.
- Updated README, config.example.yaml, and documentation with the new pattern.

### Infrastructure and quality

A full test suite, CI pipeline, and development tooling configuration close the quality gap called out in the changelog and PR template.

- Add comprehensive pytest suite with mocks for IP sources, auth subprocess, and Route53 client (moto).
- Create `lat.md/tests.md` with `require-code-mention` frontmatter; every leaf spec referenced by exactly one test.
- Introduce GitHub Actions CI covering lint, type check, tests, `lat check`, and Docker build.
- Add ruff, mypy, and pytest configuration plus `.dockerignore`.

### Contained new capabilities

A small set of high-value operational features (dry-run, notifications, configurable detection, panel polish) are included in the current milestone.

- CLI flags: `--dry-run` / `validate`, `--once`, `--config PATH`, `--version`.
- Configurable IP detection sources and timeouts (backward-compatible extension).
- Optional webhook notifications for IP changes and repeated errors (implemented — basic fire-and-forget POST).
- Enhanced persisted state (last check timestamp, last error) surfaced in the web panel.
- Panel and logging polish (version consistency, quiet config loads, last-update display).

## Deferred (Post v0.2)

These valuable ideas are documented here to capture intent without inflating the current milestone.

### Advanced extensibility

Per-host provider selection and a reference second implementation are valuable but deferred to keep the current milestone focused.

- Per-host provider selection (different DNS backends for different records in the same config).
- Full second provider implementation (e.g. Cloudflare) as a reference.

### Observability

Prometheus metrics and richer structured events are useful future additions but out of scope for the initial completeness push.

- Prometheus-compatible `/metrics` endpoint (or integration into the existing panel).
- Structured event emission beyond loguru (for external collectors).

### Panel and operations

Interactive panel features and in-process refresh APIs require additional security design and are deferred.

- Authenticated config editing surface in the web panel (requires threat model and access control design).
- In-process force-refresh API or trigger mechanism for the panel "update now" button (beyond CLI one-shot).

### Notifications

Native email and chat integrations build on the webhook foundation but are deferred in favor of the simpler primitive for v0.2.

- Built-in email, Slack, or Discord delivery (webhook primitive already provides the base).

### Deployment

Kubernetes and systemd deployment artifacts are useful community contributions but not part of the core feature-completeness milestone.

- Kubernetes manifests and Helm chart.
- Systemd unit examples and bare-metal install scripts beyond pip + manual signing helper.

## Versioning and Release

Changes that affect behavior, configuration schema, or the provider interface will be released with semantic version bumps and entries in `CHANGELOG.md`. All lat.md updates and a clean `lat check` are required before any release tag.