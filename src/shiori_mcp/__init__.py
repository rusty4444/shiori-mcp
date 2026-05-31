"""Shiori MCP server package."""

from __future__ import annotations

import os
import sys

from mcp.server.fastmcp import FastMCP

from . import client as api
from .tools import register_tools

mcp = FastMCP("shiori-mcp")
register_tools(mcp)


def _timeout_from_env() -> float:
    raw = os.environ.get("SHIORI_TIMEOUT", "20")
    try:
        return float(raw)
    except ValueError:
        print("Error: SHIORI_TIMEOUT must be a number", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Run the Shiori MCP server over stdio."""
    base_url = os.environ.get("SHIORI_BASE_URL", "").strip()
    if not base_url:
        print("Error: SHIORI_BASE_URL is required", file=sys.stderr)
        sys.exit(1)
    api.configure(
        base_url=base_url,
        username=os.environ.get("SHIORI_USERNAME"),
        password=os.environ.get("SHIORI_PASSWORD"),
        session_id=os.environ.get("SHIORI_SESSION_ID"),
        timeout=_timeout_from_env(),
    )
    mcp.run(transport="stdio")


__all__ = ["main", "mcp"]
