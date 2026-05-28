# Authentication

Certificate-based AWS authentication in [[meridian/updater/auth/iam_roles_anywhere.py#obtain_credentials]]. Eliminates static credentials by using X.509 certificates to obtain temporary STS tokens.

## IAM Roles Anywhere

Uses the AWS `aws_signing_helper` binary to exchange an X.509 certificate and private key for temporary STS credentials. The helper is invoked via `subprocess.run()` with a 30-second timeout.

JSON output is parsed into [[meridian/updater/auth/iam_roles_anywhere.py#TemporaryCredentials]], a frozen dataclass holding `access_key_id`, `secret_access_key`, and `session_token`.

Required parameters (from [[data-models#Config Types|IAMRolesAnywhereConfig]]):
- Trust anchor ARN, profile ARN, role ARN
- Certificate and private key file paths
- Signing helper binary path (default `/usr/local/bin/aws_signing_helper`)
- AWS region (default `us-east-1`)

## Error Handling

The credential process fails fast on subprocess errors.

- Non-zero exit code → `RuntimeError` with stderr message
- Invalid JSON output → `RuntimeError` with parse error details
- Timeout after 30 seconds → subprocess `TimeoutExpired` exception
