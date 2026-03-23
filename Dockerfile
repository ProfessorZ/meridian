FROM python:3.11-slim AS base

RUN groupadd -r meridian && useradd -r -g meridian -d /home/meridian -s /sbin/nologin meridian

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY meridian/ meridian/

RUN mkdir -p /var/lib/meridian && chown meridian:meridian /var/lib/meridian

USER meridian

CMD ["python", "-m", "meridian.updater.main"]
