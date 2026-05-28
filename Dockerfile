FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.4 /uv /uvx /bin/

ARG TARGETARCH
ARG SIGNING_HELPER_VERSION=1.8.0

RUN groupadd -r meridian && useradd -r -g meridian -d /home/meridian -s /sbin/nologin meridian

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN UV_PROJECT_ENVIRONMENT=/usr/local uv sync --frozen --all-extras --no-dev --no-install-project --no-cache

COPY meridian/ meridian/
RUN UV_PROJECT_ENVIRONMENT=/usr/local uv sync --frozen --all-extras --no-dev --no-cache

# Download AWS IAM Roles Anywhere signing helper
# TARGETARCH is set by Docker BuildKit: amd64 | arm64
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    case "${TARGETARCH}" in \
        amd64) AWS_ARCH="X86_64" ;; \
        arm64) AWS_ARCH="Aarch64" ;; \
        *) echo "Unsupported architecture: ${TARGETARCH}" && exit 1 ;; \
    esac && \
    curl -fsSL -o /usr/local/bin/aws_signing_helper \
        "https://rolesanywhere.amazonaws.com/releases/${SIGNING_HELPER_VERSION}/${AWS_ARCH}/Linux/Amzn2023/aws_signing_helper" && \
    chmod +x /usr/local/bin/aws_signing_helper && \
    apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/lib/meridian && chown meridian:meridian /var/lib/meridian

USER meridian

CMD ["python", "-m", "meridian.updater.main"]
