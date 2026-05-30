# Authentication

Certificate-based AWS authentication in [[meridian/updater/auth/iam_roles_anywhere.py#obtain_credentials]]. Eliminates static credentials by using X.509 certificates to obtain temporary STS tokens.

## IAM Roles Anywhere

The `aws_signing_helper` binary exchanges X.509 certs for temporary STS credentials. Invocation now uses `asyncio.create_subprocess_exec` (non-blocking) with 30s timeout to avoid stalling the [[polling-loop]].

JSON output is parsed into [[meridian/updater/auth/iam_roles_anywhere.py#TemporaryCredentials]], a frozen dataclass holding `access_key_id`, `secret_access_key`, and `session_token`.

Required parameters (from [[data-models#Config Types|IAMRolesAnywhereConfig]]):
- Trust anchor ARN, profile ARN, role ARN
- Certificate and private key file paths
- Signing helper binary path (default `/usr/local/bin/aws_signing_helper`)
- AWS region (default `us-east-1`)

## Error Handling

The credential process fails fast on helper errors (now using asyncio primitives).

- Non-zero exit code → `RuntimeError` with stderr message
- Invalid JSON output → `RuntimeError` with parse error details
- Timeout after 30 seconds → `asyncio.TimeoutError` (converted internally)
