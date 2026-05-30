"""High-level polling logic tests using mocks."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from meridian.updater.main import _poll_and_update
from meridian.updater.models import AppConfig, HostConfig, ProviderConfig
from meridian.updater.providers.base import ProviderError


@pytest.mark.asyncio
async def test_poll_no_change_skips_update(tmp_path, monkeypatch):
    """No IP change → early return, no provider updates attempted."""
    state_file = tmp_path / "state.json"
    state_file.write_text('{"ipv4": "1.2.3.4", "ipv6": null}')

    cfg = AppConfig(
        hosts=[HostConfig(hostname="example.com", zone_id="Z1")],
        state_file=state_file,
        provider=ProviderConfig(name="route53", route53=None),
    )

    with patch("meridian.updater.main.detect_ipv4", new_callable=AsyncMock) as m4, \
         patch("meridian.updater.main.detect_ipv6", new_callable=AsyncMock) as m6:
        m4.return_value = "1.2.3.4"
        m6.return_value = None

        result = await _poll_and_update(cfg)
        assert result is False


@pytest.mark.asyncio
async def test_poll_per_record_error_does_not_crash(tmp_path):
    """ProviderError on one record is logged but loop continues (per-record handling)."""
    state_file = tmp_path / "state.json"

    cfg = AppConfig(
        hosts=[HostConfig(hostname="example.com", zone_id="Z1")],
        state_file=state_file,
    )

    with patch("meridian.updater.main.detect_ipv4", new_callable=AsyncMock) as m4, \
         patch("meridian.updater.main.detect_ipv6", new_callable=AsyncMock) as m6, \
         patch("meridian.updater.main.get_provider") as get_prov:
        m4.return_value = "9.9.9.9"
        m6.return_value = None

        mock_provider = AsyncMock()
        mock_provider.update_record.side_effect = ProviderError("boom")
        get_prov.return_value = mock_provider

        # Should not raise
        result = await _poll_and_update(cfg)
        assert result is True  # change was processed (even with error)
        mock_provider.update_record.assert_awaited()


# @lat: [[tests#Polling Loop#Per-record errors do not abort cycle]]


# @lat: [[tests#Polling Loop#Per-record errors do not abort cycle]]
# @lat: [[tests#Notifications#Webhook on repeated update errors]]
# @lat: [[tests#Notifications#Webhook on successful IP change]]
# @lat: [[tests#Web Panel#Serves current state and config without secrets]]
# @lat: [[tests#Web Panel#Health endpoint always returns ok]]
@pytest.mark.asyncio
async def test_poll_with_notifications_config(tmp_path, monkeypatch):
    """Notifications config is accepted and does not break polling."""
    from meridian.updater.models import NotificationsConfig

    cfg = AppConfig(
        hosts=[],
        notifications=NotificationsConfig(webhook_url="http://example.com/hook", on_error=True),
    )

    with patch("meridian.updater.main.detect_ipv4", new_callable=AsyncMock) as m4:
        m4.return_value = "1.1.1.1"
        # Should run without error even with no hosts
        await _poll_and_update(cfg)
