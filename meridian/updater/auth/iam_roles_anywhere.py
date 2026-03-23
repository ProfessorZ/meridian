"""AWS IAM Roles Anywhere credential acquisition via aws_signing_helper."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

from loguru import logger

from meridian.updater.models import IAMRolesAnywhereConfig


@dataclass(frozen=True)
class TemporaryCredentials:
    """Short-lived AWS credentials obtained from IAM Roles Anywhere."""

    access_key_id: str
    secret_access_key: str
    session_token: str


def obtain_credentials(config: IAMRolesAnywhereConfig) -> TemporaryCredentials:
    """Obtain temporary AWS credentials using the aws_signing_helper binary.

    Invokes the `credential-process` subcommand of aws_signing_helper,
    which returns JSON-formatted temporary credentials suitable for
    boto3 session creation.

    Args:
        config: IAM Roles Anywhere configuration with paths and ARNs.

    Returns:
        TemporaryCredentials with short-lived AWS keys and session token.

    Raises:
        RuntimeError: If the signing helper fails or returns invalid output.
    """
    cmd = [
        str(config.signing_helper_path),
        "credential-process",
        "--trust-anchor-arn", config.trust_anchor_arn,
        "--profile-arn", config.profile_arn,
        "--role-arn", config.role_arn,
        "--certificate", str(config.certificate_path),
        "--private-key", str(config.private_key_path),
        "--region", config.region,
    ]

    logger.debug("Invoking signing helper for role {role}", role=config.role_arn)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"aws_signing_helper failed (exit {result.returncode}): {result.stderr.strip()}"
        )

    try:
        creds = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse signing helper output: {exc}") from exc

    return TemporaryCredentials(
        access_key_id=creds["AccessKeyId"],
        secret_access_key=creds["SecretAccessKey"],
        session_token=creds["SessionToken"],
    )
