# IAM Roles Anywhere Setup Guide

## 1. Overview

[IAM Roles Anywhere](https://docs.aws.amazon.com/rolesanywhere/latest/userguide/introduction.html) lets workloads outside AWS assume IAM roles using X.509 certificates instead of long-lived access keys. Meridian uses it to authenticate to Route 53 without storing `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` on disk.

The flow:

1. You create a **private CA** and issue a **client certificate**.
2. You register the CA as a **trust anchor** in IAM Roles Anywhere.
3. You create a **profile** that maps authenticated certificates to an **IAM role**.
4. Meridian calls `aws_signing_helper credential-process`, which presents the client cert, and receives short-lived STS credentials in return.

Certificates are rotatable. If a cert is compromised you revoke or replace it — no secrets to scrub from config files or environment variables.

## 2. Prerequisites

- **AWS CLI v2** installed and configured with permissions to create IAM roles, Roles Anywhere resources, and Route 53 policies.
- **OpenSSL** installed (any recent version).
- Collect these before you start:
  - Your **AWS account ID** (12-digit number).
  - The **Route 53 hosted zone ID(s)** Meridian will manage.
  - The **AWS region** you want Roles Anywhere resources in (e.g. `us-east-1`).

## 3. Create a Private CA and Client Certificate

All commands below use a single self-signed CA. This is appropriate for a personal or small-team setup. For production environments with many clients, consider AWS Private CA instead.

### 3.1 Generate the CA key and self-signed certificate

```bash
# Generate CA private key (4096-bit RSA)
openssl genrsa -out ca.key 4096

# Create self-signed CA certificate (valid 10 years)
openssl req -new -x509 -days 3650 -key ca.key \
  -out ca.crt \
  -subj "/CN=Meridian CA"
```

Keep `ca.key` safe. Anyone with this key can issue certificates that your trust anchor will accept.

### 3.2 Generate the client key, CSR, and signed certificate

```bash
# Generate client private key
openssl genrsa -out client.key 2048

# Create a certificate signing request
openssl req -new -key client.key \
  -out client.csr \
  -subj "/CN=meridian-ddns"

# Sign with the CA (valid 1 year)
openssl x509 -req -days 365 \
  -in client.csr \
  -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out client.crt
```

You now have:

| File         | Purpose                                   |
|--------------|-------------------------------------------|
| `ca.key`     | CA private key — store offline/secure      |
| `ca.crt`     | CA certificate — uploaded as trust anchor  |
| `client.key` | Client private key — used by Meridian      |
| `client.crt` | Client certificate — used by Meridian      |
| `client.csr` | CSR — can be deleted after signing         |

### 3.3 Verify the certificate

```bash
openssl verify -CAfile ca.crt client.crt
# Expected: client.crt: OK
```

## 4. Create the IAM Role

### 4.1 Trust policy

Create `trust-policy.json`. This allows the Roles Anywhere service to assume the role, restricted to certificates whose CN matches `meridian-ddns`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "rolesanywhere.amazonaws.com"
      },
      "Action": [
        "sts:AssumeRole",
        "sts:TagSession",
        "sts:SetSourceIdentity"
      ],
      "Condition": {
        "StringEquals": {
          "aws:PrincipalTag/x509Subject/CN": "meridian-ddns"
        }
      }
    }
  ]
}
```

### 4.2 Create the role

```bash
aws iam create-role \
  --role-name MeridianDDNSRole \
  --assume-role-policy-document file://trust-policy.json
```

### 4.3 Route 53 policy

Create `route53-policy.json`. Replace `<YOUR_ZONE_ID>` with your hosted zone ID (repeat the resource ARN for multiple zones):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowRecordChanges",
      "Effect": "Allow",
      "Action": "route53:ChangeResourceRecordSets",
      "Resource": "arn:aws:route53:::hostedzone/<YOUR_ZONE_ID>"
    },
    {
      "Sid": "AllowReadOps",
      "Effect": "Allow",
      "Action": [
        "route53:ListHostedZones",
        "route53:GetChange"
      ],
      "Resource": "*"
    }
  ]
}
```

### 4.4 Attach the policy

```bash
aws iam put-role-policy \
  --role-name MeridianDDNSRole \
  --policy-name MeridianRoute53Policy \
  --policy-document file://route53-policy.json
```

## 5. Create the Trust Anchor

Upload your CA certificate as a trust anchor:

```bash
aws rolesanywhere create-trust-anchor \
  --name MeridianTrustAnchor \
  --source "sourceType=CERTIFICATE_BUNDLE,sourceData={x509CertificateData=$(cat ca.crt)}" \
  --enabled \
  --region <YOUR_REGION>
```

Save the trust anchor ARN from the output:

```
arn:aws:rolesanywhere:<YOUR_REGION>:<YOUR_ACCOUNT_ID>:trust-anchor/<TRUST_ANCHOR_ID>
```

## 6. Create the Profile

Link the trust anchor to the IAM role:

```bash
aws rolesanywhere create-profile \
  --name MeridianProfile \
  --role-arns "arn:aws:iam::<YOUR_ACCOUNT_ID>:role/MeridianDDNSRole" \
  --enabled \
  --region <YOUR_REGION>
```

Save the profile ARN from the output:

```
arn:aws:rolesanywhere:<YOUR_REGION>:<YOUR_ACCOUNT_ID>:profile/<PROFILE_ID>
```

## 7. Configure Meridian

In your `config.yaml`, fill in the `provider.route53.iam_roles_anywhere` section with the ARNs from steps 4–6 and the certificate paths from step 3:

```yaml
provider:
  name: route53
  route53:
    iam_roles_anywhere:
      trust_anchor_arn: "arn:aws:rolesanywhere:<YOUR_REGION>:<YOUR_ACCOUNT_ID>:trust-anchor/<TRUST_ANCHOR_ID>"
      profile_arn: "arn:aws:rolesanywhere:<YOUR_REGION>:<YOUR_ACCOUNT_ID>:profile/<PROFILE_ID>"
      role_arn: "arn:aws:iam::<YOUR_ACCOUNT_ID>:role/MeridianDDNSRole"
      certificate_path: /etc/meridian/certs/client.crt
      private_key_path: /etc/meridian/certs/client.key
      signing_helper_path: /usr/local/bin/aws_signing_helper
      region: <YOUR_REGION>
```

If running in Docker, mount the certificate and key into the container. The `aws_signing_helper` binary is already included in the Meridian Docker image.

## 8. Verify It Works

Test credential retrieval directly:

```bash
aws_signing_helper credential-process \
  --trust-anchor-arn "arn:aws:rolesanywhere:<YOUR_REGION>:<YOUR_ACCOUNT_ID>:trust-anchor/<TRUST_ANCHOR_ID>" \
  --profile-arn "arn:aws:rolesanywhere:<YOUR_REGION>:<YOUR_ACCOUNT_ID>:profile/<PROFILE_ID>" \
  --role-arn "arn:aws:iam::<YOUR_ACCOUNT_ID>:role/MeridianDDNSRole" \
  --certificate /path/to/client.crt \
  --private-key /path/to/client.key
```

Expected output:

```json
{
  "Version": 1,
  "AccessKeyId": "ASIA...",
  "SecretAccessKey": "...",
  "SessionToken": "...",
  "Expiration": "2026-03-25T12:00:00Z"
}
```

If this returns valid JSON credentials, the full chain — certificate, trust anchor, profile, and role — is working. Meridian calls this same command internally.

## 9. Certificate Renewal

The client certificate created in this guide expires after 1 year. The CA certificate lasts 10 years.

To renew the client certificate:

```bash
# Generate a new client key and CSR
openssl genrsa -out client-new.key 2048
openssl req -new -key client-new.key -out client-new.csr -subj "/CN=meridian-ddns"

# Sign with the same CA
openssl x509 -req -days 365 \
  -in client-new.csr \
  -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out client-new.crt

# Replace the old files
mv client-new.crt /etc/meridian/certs/client.crt
mv client-new.key /etc/meridian/certs/client.key

# Restart Meridian to pick up the new cert
```

The trust anchor does not need to change — any certificate signed by the same CA will be accepted. When the CA certificate itself approaches expiry (after 10 years), you will need to generate a new CA and update the trust anchor in AWS.
