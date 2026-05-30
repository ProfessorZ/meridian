"""Tests for configuration loading (YAML + env overrides + resilience)."""

import os
from pathlib import Path

import pytest

from meridian.updater.config import load_config

# @lat: [[tests#Configuration Loading#Loads YAML with environment overrides]]
def test_load_config_env_overrides(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("poll_interval: 120\nlog_level: DEBUG\n")

    monkeypatch.setenv("MERIDIAN_CONFIG", str(cfg_file))
    monkeypatch.setenv("MERIDIAN_POLL_INTERVAL", "600")
    monkeypatch.setenv("MERIDIAN_LOG_LEVEL", "WARNING")

    cfg = load_config()
    assert cfg.poll_interval == 600
    assert cfg.log_level == "WARNING"


def test_load_config_missing_file_still_works(tmp_path, monkeypatch, caplog):
    missing = tmp_path / "nope.yaml"
    monkeypatch.setenv("MERIDIAN_CONFIG", str(missing))

    cfg = load_config()
    assert cfg.poll_interval == 300  # default
    assert "Config file not found" in caplog.text
