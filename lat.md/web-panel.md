# Web Panel

Optional FastAPI dashboard in [[meridian/panel/main.py#app]] for monitoring DDNS status. Reads [[configuration]] and [[state-management]] data to render a live view.

## Endpoints

Two HTTP endpoints serve monitoring and health check needs.

- `GET /` → [[meridian/panel/main.py#index]] — HTML dashboard showing current IPs, config summary, and managed hosts table
- `GET /health` → [[meridian/panel/main.py#health]] — JSON health check returning `{"status": "ok"}`

## Dashboard UI

Dark-themed responsive HTML using Jinja2 templates (`meridian/panel/templates/index.html`). Displays cached IPv4/IPv6, poll interval, provider name, and a table of all managed hosts with their zone IDs, IPv4/IPv6 flags, and TTL values.

## Server

Runs via [[meridian/panel/main.py#run]] which starts uvicorn on `0.0.0.0:8080`. Uvicorn is imported lazily to avoid a hard dependency when only the updater CLI is used.
