# @lat: [[route53-provider]]
"""AWS Route53 DNS provider implementation."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import boto3
from loguru import logger

from meridian.updater.auth.iam_roles_anywhere import obtain_credentials
from meridian.updater.models import DNSRecord
from meridian.updater.providers.base import DNSProvider, ProviderError
from meridian.updater.providers.registry import register_provider

if TYPE_CHECKING:
    from meridian.updater.models import ProviderConfig


class Route53Provider(DNSProvider):
    """DNS provider for AWS Route53.

    Uses IAM Roles Anywhere for credential acquisition — no static
    AWS access keys required.
    """

    def __init__(self, config: ProviderConfig) -> None:
        if config.route53 is None:
            raise ProviderError("Route53 provider requires 'route53' configuration block")
        self._iam_config = config.route53.iam_roles_anywhere
        self._client = None  # created lazily on first use (async)

    async def _create_client(self):
        """Create a boto3 Route53 client using IAM Roles Anywhere credentials (async)."""
        creds = await obtain_credentials(self._iam_config)
        session = boto3.Session(
            aws_access_key_id=creds.access_key_id,
            aws_secret_access_key=creds.secret_access_key,
            aws_session_token=creds.session_token,
            region_name=self._iam_config.region,
        )
        return session.client("route53")

    async def _refresh_credentials(self) -> None:  # @lat: route53-provider#Credential Lifecycle
        # @lat: [[tests#Route53 Provider#Refreshes credentials and retries once on auth errors]]
        # @lat: [[tests#Route53 Provider#Always raises ProviderError on failure]]
        """Re-obtain credentials and recreate the client (async)."""
        logger.info("Refreshing IAM Roles Anywhere credentials")
        self._client = await self._create_client()

    async def _ensure_client(self) -> None:
        if self._client is None:
            self._client = await self._create_client()

    async def update_record(self, record: DNSRecord, ip: str) -> None:
        """Upsert a Route53 DNS record.

        Uses UPSERT to create the record if it doesn't exist or update
        it if it does. The actual Route53 API call is dispatched via
        asyncio.to_thread so the event loop is never blocked.

        Automatically refreshes credentials on auth failure and retries
        the operation once. All error paths (including the retry) raise
        ProviderError so the polling loop can handle them per-record.
        """
        await self._ensure_client()
        change_batch = {
            "Comment": f"Meridian DDNS update for {record.hostname}",
            "Changes": [
                {
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": record.hostname,
                        "Type": record.record_type.value,
                        "TTL": record.ttl,
                        "ResourceRecords": [{"Value": ip}],
                    },
                }
            ],
        }

        try:
            await asyncio.to_thread(
                self._client.change_resource_record_sets,
                HostedZoneId=record.zone_id,
                ChangeBatch=change_batch,
            )
        except self._client.exceptions.ClientError as exc:
            error_code = exc.response["Error"]["Code"]
            if error_code in ("ExpiredTokenException", "InvalidSignatureException"):
                logger.warning("Credentials expired, refreshing and retrying")
                await self._refresh_credentials()
                await self._ensure_client()
                try:
                    await asyncio.to_thread(
                        self._client.change_resource_record_sets,
                        HostedZoneId=record.zone_id,
                        ChangeBatch=change_batch,
                    )
                except Exception as retry_exc:
                    # Ensure the retry failure is also turned into ProviderError
                    if isinstance(retry_exc, self._client.exceptions.ClientError):
                        raise ProviderError(
                            f"Route53 update failed for {record.hostname} after credential refresh: {retry_exc}"
                        ) from retry_exc
                    raise ProviderError(
                        f"Route53 update failed for {record.hostname} after credential refresh: {retry_exc}"
                    ) from retry_exc
            else:
                raise ProviderError(
                    f"Route53 update failed for {record.hostname}: {exc}"
                ) from exc

        logger.info(
            "Updated {type} record for {host} -> {ip}",
            type=record.record_type.value,
            host=record.hostname,
            ip=ip,
        )

    async def close(self) -> None:
        """Release the underlying boto3 client resources if present."""
        if self._client is not None:
            try:
                await asyncio.to_thread(self._client.close)
            except Exception:
                # Best-effort; clients are usually safe to abandon
                pass
            self._client = None


register_provider("route53", Route53Provider)
