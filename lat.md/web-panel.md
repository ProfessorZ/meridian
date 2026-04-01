# Web Panel

Optional FastAPI dashboard in `meridian/panel/` for monitoring DDNS status. Reads [[configuration]] and [[state-management]] data to render a live view.

## Endpoints

Two HTTP endpoints serve monitoring and health check needs.

- `GET /` — HTML dashboard showing current IPs, config summary, and managed hosts table
- `GET /health` — JSON health check returning `{"status": "ok"}`

## Dashboard UI

Dark-themed responsive HTML using Jinja2 templates. Displays cached IPv4/IPv6, poll interval, provider name, and a table of all managed hosts with their zone IDs, IPv4/IPv6 flags, and TTL values. Runs on port 8080 via uvicorn.
