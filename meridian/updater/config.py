"""Configuration loading from YAML file and environment variables."""  # @lat: configuration

from __future__ import annotations

import os
from pathlib import Path

import yaml
from loguru import logger

from meridian.updater.models import AppConfig


def load_config(config_path: str | None = None) -> AppConfig:
    """Load configuration from a YAML file, with environment variable overrides.

    Resolution order:
    1. YAML config file (path from arg or MERIDIAN_CONFIG env var)
    2. Environment variable overrides (MERIDIAN_POLL_INTERVAL, MERIDIAN_LOG_LEVEL)
    """
    path = config_path or os.environ.get("MERIDIAN_CONFIG", "/etc/meridian/config.yaml")
    data: dict = {}

    config_file = Path(path)
    if config_file.exists():
        logger.info("Loading config from {path}", path=path)
        with open(config_file) as f:
            data = yaml.safe_load(f) or {}
    else:
        logger.warning("Config file not found at {path}, using defaults", path=path)

    # Environment variable overrides
    if interval := os.environ.get("MERIDIAN_POLL_INTERVAL"):
        data["poll_interval"] = int(interval)
    if log_level := os.environ.get("MERIDIAN_LOG_LEVEL"):
        data["log_level"] = log_level
    if state_file := os.environ.get("MERIDIAN_STATE_FILE"):
        data["state_file"] = state_file

    config = AppConfig(**data)
    logger.info(
        "Config loaded: {host_count} hosts, poll every {interval}s",
        host_count=len(config.hosts),
        interval=config.poll_interval,
    )
    return config
