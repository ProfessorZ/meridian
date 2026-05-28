# @lat: [[route53-provider]]
"""AWS Route53 DNS provider implementation."""

from __future__ import annotations

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
        self._client = self._create_client()

    def _create_client(self):
        """Create a boto3 Route53 client using IAM Roles Anywhere credentials."""
        creds = obtain_credentials(self._iam_config)
        session = boto3.Session(
            aws_access_key_id=creds.access_key_id,
            aws_secret_access_key=creds.secret_access_key,
            aws_session_token=creds.session_token,
            region_name=self._iam_config.region,
        )
        return session.client("route53")

    def _refresh_credentials(self) -> None:  # @lat: route53-provider#Credential Lifecycle
        """Re-obtain credentials and recreate the client."""
        logger.info("Refreshing IAM Roles Anywhere credentials")
        self._client = self._create_client()

    async def update_record(self, record: DNSRecord, ip: str) -> None:
        """Upsert a Route53 DNS record.

        Uses UPSERT to create the record if it doesn't exist or update
        it if it does. Automatically refreshes credentials on auth failure.
        """
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
            self._client.change_resource_record_sets(
                HostedZoneId=record.zone_id,
                ChangeBatch=change_batch,
            )
        except self._client.exceptions.ClientError as exc:
            error_code = exc.response["Error"]["Code"]
            if error_code in ("ExpiredTokenException", "InvalidSignatureException"):
                logger.warning("Credentials expired, refreshing and retrying")
                self._refresh_credentials()
                self._client.change_resource_record_sets(
                    HostedZoneId=record.zone_id,
                    ChangeBatch=change_batch,
                )
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


register_provider("route53", Route53Provider)
