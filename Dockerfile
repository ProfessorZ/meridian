FROM python:3.11-slim AS base

ARG SIGNING_HELPER_VERSION=1.8.0

RUN groupadd -r meridian && useradd -r -g meridian -d /home/meridian -s /sbin/nologin meridian

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY meridian/ meridian/

# Download AWS IAM Roles Anywhere signing helper
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then ARCH="X86_64"; \
    elif [ "$ARCH" = "aarch64" ]; then ARCH="Aarch64"; \
    fi && \
    curl -fsSL -o /usr/local/bin/aws_signing_helper \
        "https://rolesanywhere.amazonaws.com/releases/${SIGNING_HELPER_VERSION}/${ARCH}/Linux/Amzn2023/aws_signing_helper" && \
    chmod +x /usr/local/bin/aws_signing_helper && \
    apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/lib/meridian && chown meridian:meridian /var/lib/meridian

USER meridian

CMD ["python", "-m", "meridian.updater.main"]
