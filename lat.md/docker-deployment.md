# Docker Deployment

Multi-architecture container build (amd64/arm64) for production deployment. Uses a non-root user and minimal base image for security.

## Image Details

The Dockerfile builds a secure, lightweight container.

- Base: `python:3.11-slim`
- Non-root `meridian` user for least-privilege execution
- AWS signing helper v1.8.0 downloaded as platform-specific binary via `TARGETARCH`
- State directory at `/var/lib/meridian` owned by the meridian user

## Compose Services

Docker Compose defines two services sharing config and state.

- **updater** — main [[polling-loop]] service with config/certs mounted read-only, restart unless-stopped
- **panel** — optional [[web-panel]] on port 8080, reads same config and state volume
