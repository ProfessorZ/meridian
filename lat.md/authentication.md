# Authentication

Certificate-based AWS authentication in `meridian/updater/auth/iam_roles_anywhere.py`. Eliminates static credentials by using X.509 certificates to obtain temporary STS tokens.

## IAM Roles Anywhere

Uses the AWS `aws_signing_helper` binary to exchange an X.509 certificate and private key for temporary STS credentials (access key, secret key, session token).

The helper is invoked via `subprocess.run()` with a 30-second timeout. JSON output is parsed into a `TemporaryCredentials` frozen dataclass.

Required parameters (from [[configuration]]):
- Trust anchor ARN, profile ARN, role ARN
- Certificate and private key file paths
- Signing helper binary path and AWS region
