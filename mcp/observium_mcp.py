#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["fastmcp>=2.0", "requests>=2.32"]
# ///
"""Read-only MCP server for Observium's REST API.

Auth: HTTP Basic (the same AD username/password used for the web UI).
Observium's "API access key" in user preferences is for RSS/Atom feeds, not
the REST API, so a disabled key button does not block this.

Env vars (set in ~/.cursor/mcp.json or sourced from .env.local for selftest):
  OBSERVIUM_URL       e.g. https://sun-observium01-p.zooxlabs.com
  OBSERVIUM_USER      e.g. prasingh
  OBSERVIUM_PASSWORD  your AD password
  OBSERVIUM_VERIFY_SSL  "true"/"false" (default false; internal cert)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional

import requests


def _load_env_local() -> None:
    """Load OBSERVIUM_* vars from a sibling .env.local if not already set.

    Keeps the password in one gitignored file instead of duplicating it into
    ~/.cursor/mcp.json. Supports lines like: export KEY="value" / KEY=value.
    """
    here = Path(__file__).resolve().parent
    env_path = next((d / ".env.local" for d in [here, *here.parents] if (d / ".env.local").exists()), None)
    if env_path is None:
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key.startswith("OBSERVIUM_") and not os.environ.get(key):
            os.environ[key] = val


_load_env_local()

URL = os.environ.get("OBSERVIUM_URL", "").rstrip("/")
USER = os.environ.get("OBSERVIUM_USER", "")
PASSWORD = os.environ.get("OBSERVIUM_PASSWORD", "")
VERIFY_SSL = os.environ.get("OBSERVIUM_VERIFY_SSL", "false").lower() in ("1", "true", "yes")

_session: Optional[requests.Session] = None


def _client() -> requests.Session:
    global _session
    if _session is None:
        if not (URL and USER and PASSWORD):
            raise RuntimeError(
                "Missing OBSERVIUM_URL / OBSERVIUM_USER / OBSERVIUM_PASSWORD env vars."
            )
        s = requests.Session()
        s.auth = (USER, PASSWORD)
        s.headers.update({"Accept": "application/json"})
        s.verify = VERIFY_SSL
        _session = s
    return _session


def _get(path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Core GET against /api/v0. `path` is relative, e.g. 'devices' or 'ports/123'."""
    if not VERIFY_SSL:
        # silence the noisy InsecureRequestWarning for the internal cert
        requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]
    rel = path.strip("/")
    full = f"{URL}/api/v0/{rel}/" if not rel.endswith("/") else f"{URL}/api/v0/{rel}"
    resp = _client().get(full, params=params or {}, timeout=30)
    resp.raise_for_status()
    try:
        return resp.json()
    except ValueError:
        return {"_raw": resp.text}


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------
try:
    from fastmcp import FastMCP
except Exception:  # allow --selftest without fastmcp installed in some envs
    FastMCP = None  # type: ignore

if FastMCP is not None:
    mcp = FastMCP("observium")

    @mcp.tool
    def observium_status() -> dict[str, Any]:
        """Quick connectivity check. Returns total device count from Observium."""
        data = _get("devices", {"fields": "device_id", "pagesize": 1})
        return {
            "url": URL,
            "user": USER,
            "ok": True,
            "device_count": data.get("count"),
            "status": data.get("status"),
        }

    @mcp.tool
    def observium_api(path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Generic read-only GET against any Observium /api/v0 endpoint.

        Args:
            path: endpoint relative to /api/v0, e.g. 'devices', 'ports/4567',
                  'alerts', 'health/processors', 'inventory/12'.
            params: optional query parameters (Observium supports rich filters,
                  e.g. {'location': 'Austin', 'os': 'arista_eos', 'status': 0}).
        """
        return _get(path, params)

    @mcp.tool
    def list_devices(
        location: Optional[str] = None,
        os: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[int] = None,
        group: Optional[str] = None,
        query: Optional[str] = None,
        pagesize: int = 100,
    ) -> dict[str, Any]:
        """List monitored devices.

        Args:
            location: filter by location string.
            os: device OS family (e.g. 'arista_eos', 'fortigate', 'junos').
            type: device type (e.g. 'network', 'firewall').
            status: 1 = up, 0 = down.
            group: device group name/id.
            query: free-text hostname match (Observium 'hostname' param).
            pagesize: max rows (default 100).
        """
        params: dict[str, Any] = {"pagesize": pagesize}
        if location is not None:
            params["location"] = location
        if os is not None:
            params["os"] = os
        if type is not None:
            params["type"] = type
        if status is not None:
            params["status"] = status
        if group is not None:
            params["group"] = group
        if query is not None:
            params["hostname"] = query
        return _get("devices", params)

    @mcp.tool
    def get_device(device_id: int) -> dict[str, Any]:
        """Get full detail for a single device by its numeric device_id."""
        return _get(f"devices/{device_id}")

    @mcp.tool
    def list_ports(
        device_id: Optional[int] = None,
        state: Optional[str] = None,
        errors: Optional[bool] = None,
        pagesize: int = 200,
    ) -> dict[str, Any]:
        """List interfaces/ports.

        Args:
            device_id: restrict to one device.
            state: 'up' or 'down' (ifOperStatus).
            errors: if True, only ports with error counters.
            pagesize: max rows (default 200).
        """
        params: dict[str, Any] = {"pagesize": pagesize}
        if device_id is not None:
            params["device_id"] = device_id
        if state is not None:
            params["state"] = state
        if errors:
            params["errors"] = 1
        return _get("ports", params)

    @mcp.tool
    def get_port(port_id: int) -> dict[str, Any]:
        """Get full detail for a single port by its numeric port_id."""
        return _get(f"ports/{port_id}")

    @mcp.tool
    def list_alerts(
        status: Optional[str] = None,
        device_id: Optional[int] = None,
        pagesize: int = 100,
    ) -> dict[str, Any]:
        """List alerts.

        Args:
            status: 'failed' (active) or 'ok'.
            device_id: restrict to one device.
            pagesize: max rows (default 100).
        """
        params: dict[str, Any] = {"pagesize": pagesize}
        if status is not None:
            params["status"] = status
        if device_id is not None:
            params["device_id"] = device_id
        return _get("alerts", params)

    @mcp.tool
    def list_sensors(
        device_id: Optional[int] = None,
        metric: Optional[str] = None,
        pagesize: int = 200,
    ) -> dict[str, Any]:
        """List health sensors (temperature, voltage, fans, etc.).

        Args:
            device_id: restrict to one device.
            metric: sensor class, e.g. 'temperature', 'voltage', 'fanspeed'.
            pagesize: max rows (default 200).
        """
        params: dict[str, Any] = {"pagesize": pagesize}
        if device_id is not None:
            params["device_id"] = device_id
        if metric is not None:
            params["metric"] = metric
        return _get("health", params)


def _selftest() -> int:
    """Hit a few endpoints and print a summary. Run: uv run observium_mcp.py --selftest"""
    print(f"URL={URL} USER={USER} VERIFY_SSL={VERIFY_SSL}")
    try:
        dev = _get("devices", {"pagesize": 3})
    except Exception as e:  # noqa: BLE001
        print(f"FAILED: {e}")
        return 1
    print(f"status={dev.get('status')} count={dev.get('count')}")
    devices = dev.get("devices") or {}
    sample = list(devices.values())[:3] if isinstance(devices, dict) else devices[:3]
    for d in sample:
        print(
            "  - id={device_id} {hostname} os={os} type={type} status={status}".format(
                device_id=d.get("device_id"),
                hostname=d.get("hostname"),
                os=d.get("os"),
                type=d.get("type"),
                status=d.get("status"),
            )
        )
    print("OK")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    if FastMCP is None:
        raise SystemExit("fastmcp not installed; cannot start MCP server.")
    mcp.run()
