# @lat: [[web-panel]]
"""Meridian web configuration panel — lightweight FastAPI app."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from meridian.updater.config import load_config
from meridian.updater.models import IPState
from meridian.version import __version__

app = FastAPI(title="Meridian DDNS Panel", version=__version__)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the status/config dashboard."""
    config = load_config(quiet=True)
    state = IPState()
    if config.state_file.exists():
        try:
            data = json.loads(config.state_file.read_text())
            state = IPState(**data)
        except (json.JSONDecodeError, ValueError):
            pass

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "config": config,
            "state": state,
        },
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


def run() -> None:
    """Entry point for the Meridian web panel."""
    import uvicorn

    uvicorn.run("meridian.panel.main:app", host="0.0.0.0", port=8080)
