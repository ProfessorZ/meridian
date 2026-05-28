# Configuration

Layered config loading in [[meridian/updater/config.py#load_config]]. Combines YAML files with environment variable overrides, validated by Pydantic.

## Resolution Order

Config values are resolved from multiple sources with later sources overriding earlier ones.

1. YAML file (path from CLI arg, `MERIDIAN_CONFIG` env, or `/etc/meridian/config.yaml`)
2. Environment variable overrides: `MERIDIAN_POLL_INTERVAL`, `MERIDIAN_LOG_LEVEL`, `MERIDIAN_STATE_FILE`
3. Pydantic v2 validation via [[data-models#Config Types|AppConfig]]

## Resilience

The config loader handles degraded states gracefully without crashing.

- Missing config file → logs warning and uses Pydantic defaults
- Invalid YAML → falls back to empty dict, Pydantic applies defaults
- Environment variables override any YAML value when set

## Environment Variables

Three environment variables provide override capability for containerized deployments.

| Variable | Type | Effect |
|---|---|---|
| `MERIDIAN_CONFIG` | path | Config file location |
| `MERIDIAN_POLL_INTERVAL` | int | Seconds between poll cycles |
| `MERIDIAN_LOG_LEVEL` | string | Logging verbosity |
| `MERIDIAN_STATE_FILE` | path | IP state persistence location |
