"""Tests for state load/save logic and clean-batch behavior."""

import json
from pathlib import Path

from meridian.updater.main import _load_state, _save_state
from meridian.updater.models import IPState

# @lat: [[tests#State Management#Loads empty state on missing or corrupt file]]
def test_load_state_missing_file(tmp_path):
    path = tmp_path / "state.json"
    state = _load_state(path)
    assert state.ipv4 is None
    assert state.ipv6 is None


def test_load_state_corrupt_file(tmp_path, caplog):
    path = tmp_path / "state.json"
    path.write_text("not valid json {")
    state = _load_state(path)
    assert state.ipv4 is None
    assert "Corrupt state file" in caplog.text


# @lat: [[tests#State Management#Tracks last_checked and last_error]]
# @lat: [[tests#State Management#Persists state only after clean update batch]]
def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "state.json"
    s = IPState(ipv4="1.2.3.4", ipv6="2001:db8::1")
    _save_state(path, s)

    loaded = _load_state(path)
    assert loaded.ipv4 == "1.2.3.4"
    assert loaded.ipv6 == "2001:db8::1"
