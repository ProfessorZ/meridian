# Changelog

All notable changes to Meridian will be documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)  
Versioning: [Semantic Versioning](https://semver.org/)

---

## [Unreleased]

### Added
- `lat.md/limitations.md`, `lat.md/roadmap.md`, and `lat.md/tests.md` skeletons (initially)

## [0.2.0] - 2026-05-30

Major feature-completeness release. Meridian is now production-viable with all critical correctness issues resolved, a truly extensible provider system, comprehensive observability, and a full test + CI foundation.

### Added
- Full CLI support: `--dry-run`/`--validate`, `--once`, `--config`, `--version`
- Optional webhook notifications (`notifications` block) for IP changes and repeated errors (fire-and-forget)
- Enhanced state tracking: `last_checked` timestamp and `last_error` in `IPState`, surfaced in web panel
- Configurable IP detection sources and timeout via `ip_detection` block
- Comprehensive test suite (6 modules) with `lat.md/tests.md` integration and `require-code-mention: true` satisfied
- GitHub Actions CI workflow (ruff, pytest, mypy, lat check, Docker build)
- Development tooling (ruff, mypy, pytest-asyncio, respx, moto, etc.) and `.dockerignore`

### Changed
- **Provider extensibility**: `ProviderConfig` now uses `extra='allow'`. New DNS providers can be added without modifying core Pydantic models (resolves the previous "plugin architecture illusion").
- **Core correctness**:
  - Eliminated blocking I/O (auth via `asyncio.create_subprocess_exec`, Route53 via `asyncio.to_thread`)
  - Implemented clean-batch state persistence (state only saved after zero `ProviderError`s)
  - Guaranteed provider lifecycle with `try/finally` close on all paths
  - Hardened Route53 credential refresh + retry (always surfaces `ProviderError`)
- Web panel: quiet config loading and consistent versioning
- Updated all `lat.md/` sections, README, and examples to reflect new architecture and capabilities
- Bumped version to 0.2.0

### Fixed
- Multiple production reliability issues identified in initial review (blocking I/O, lost updates on transient failures, fragile error handling, resource leaks)
- Corrected outdated claims in CHANGELOG and PR template regarding CI/tests

---

## [0.1.0] - Initial

### Added
- Initial scaffold: updater core, Route53 provider, IAM Roles Anywhere auth
- IPv4/IPv6 detection with multi-source fallback
- Plugin architecture for DNS providers
- Optional FastAPI web panel
- Docker support (slim image, non-root user)

<!-- Release template:
## [X.Y.Z] - YYYY-MM-DD

### Added
### Changed
### Fixed
### Removed
-->
