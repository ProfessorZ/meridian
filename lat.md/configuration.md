# Configuration

Layered config loading in `meridian/updater/config.py`. Combines YAML files with environment variable overrides, validated by Pydantic.

## Resolution Order

Config values are resolved from multiple sources with later sources overriding earlier ones.

1. YAML file (path from CLI arg, `MERIDIAN_CONFIG` env, or `/etc/meridian/config.yaml`)
2. Environment variable overrides: `MERIDIAN_POLL_INTERVAL`, `MERIDIAN_LOG_LEVEL`, `MERIDIAN_STATE_FILE`
3. Pydantic v2 validation via [[data-models]] `AppConfig`

## Resilience

The config loader handles degraded states gracefully.

- Missing config file → logs warning and uses defaults
- Corrupted state file → logs warning and resets to empty state
