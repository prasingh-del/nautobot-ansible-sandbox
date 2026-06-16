#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["fastmcp>=2.0", "requests>=2.32"]
# ///
"""Read-only MCP server for Zoox Cacti (https://cacti.zooxlabs.com).

Two access modes:

1. **guest** (default when no password) — no login required. Uses the public
   Weathermap gallery and guest Graphs list (same as the shared guest link).
2. **full** — Cacti Console session (host CSV export, etc.) when CACTI_PASSWORD
   is set and login succeeds.

Guest entry point (Zoox):
  https://cacti.zooxlabs.com/plugins/weathermap/weathermap-cacti-plugin.php

Env vars (.env.local or ~/.cursor/mcp.json):
  CACTI_URL              default https://cacti.zooxlabs.com
  CACTI_MODE             guest | full | auto  (default auto)
  CACTI_WEATHERMAP_PATH  default plugins/weathermap/weathermap-cacti-plugin.php
  CACTI_USER / CACTI_PASSWORD   only for full mode
  CACTI_VERIFY_SSL       true/false (default false)
"""
from __future__ import annotations

import csv
import io
import os
import re
import sys
from html import unescape
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin

import requests


def _load_env_local() -> None:
    here = Path(__file__).resolve().parent
    env_path = next((d / ".env.local" for d in [here, *here.parents] if (d / ".env.local").exists()), None)
    if env_path is None:
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key.startswith("CACTI_") and not os.environ.get(key):
            os.environ[key] = val


_load_env_local()

URL = os.environ.get("CACTI_URL", "https://cacti.zooxlabs.com").rstrip("/")
MODE = os.environ.get("CACTI_MODE", "auto").lower()
WEATHERMAP_PATH = os.environ.get(
    "CACTI_WEATHERMAP_PATH",
    "plugins/weathermap/weathermap-cacti-plugin.php",
).lstrip("/")
USER = os.environ.get("CACTI_USER") or os.environ.get("OBSERVIUM_USER", "")
PASSWORD = os.environ.get("CACTI_PASSWORD") or os.environ.get("OBSERVIUM_PASSWORD", "")
VERIFY_SSL = os.environ.get("CACTI_VERIFY_SSL", "false").lower() in ("1", "true", "yes")

if not VERIFY_SSL:
    requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]

AREA_LINE_RE = re.compile(
    r'\bid=["\']([^"\']+)["\'].*?\bclass=["\'](node|link)["\']'
    r'.*?\bhref=["\']([^"\']*)["\']'
    r'(?:.*?\bdata-caption=["\']([^"\']*)["\'])?',
    re.I,
)
MAP_GALLERY_RE = re.compile(
    r'textSubHeaderDark[^>]*>(?P<title>[^<]+)</div></div><div><a\s+href='
    r'(?P<href>[^>\s]+)[^>]*><img[^>]*\btitle=["\'](?P<title2>[^"\']*)["\']',
    re.I,
)
GRAPH_ROW_RE = re.compile(
    r'<a class="linkEditMain" href="graph\.php\?local_graph_id=(\d+)&amp;rra_id=\d+">\s*([^<]+?)\s*</a>',
    re.I,
)


class CactiGuestClient:
    """Unauthenticated read-only access to guest Weathermap + Graph list."""

    def __init__(self, base_url: str, weathermap_path: str, verify_ssl: bool) -> None:
        self.base_url = base_url.rstrip("/")
        self.weathermap_path = weathermap_path.lstrip("/")
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.session.headers.update(
            {"User-Agent": "cacti-mcp/1.0 (guest read-only)", "Accept": "text/html,*/*"}
        )

    def weathermap_url(self, **params: Any) -> str:
        q = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        base = urljoin(self.base_url + "/", self.weathermap_path)
        return f"{base}?{q}" if q else base

    def get(self, path: str, params: Optional[dict[str, Any]] = None) -> requests.Response:
        rel = path.lstrip("/")
        full = urljoin(self.base_url + "/", rel)
        resp = self.session.get(full, params=params or {}, timeout=120)
        resp.raise_for_status()
        return resp

    def gallery_html(self) -> str:
        return self.get(self.weathermap_path).text

    def map_html(self, map_id: str) -> str:
        return self.get(self.weathermap_path, {"action": "viewmap", "id": map_id}).text

    @staticmethod
    def parse_gallery(html: str) -> list[dict[str, str]]:
        maps: list[dict[str, str]] = []
        seen: set[str] = set()
        for m in MAP_GALLERY_RE.finditer(html):
            title = unescape((m.group("title") or m.group("title2") or "").strip())
            href = unescape(m.group("href").strip())
            mid = ""
            mm = re.search(r"[?&]id=([a-f0-9]+)", href, re.I)
            if mm:
                mid = mm.group(1)
            if not mid or mid in seen:
                continue
            seen.add(mid)
            maps.append(
                {
                    "id": mid,
                    "title": title,
                    "view_url": href if href.startswith("http") else urljoin(URL + "/", href.lstrip("/")),
                }
            )
        return maps

    @staticmethod
    def _parse_caption(caption: str) -> dict[str, str]:
        caption = unescape(caption or "").strip()
        out: dict[str, str] = {"caption": caption}
        if " CPU Usage:" in caption:
            host, _, rest = caption.partition(" CPU Usage:")
            out["hostname"] = host.strip()
            out["metric"] = "cpu"
            out["value"] = rest.strip()
        elif " BW:" in caption:
            parts = caption.split()
            out["hostname"] = parts[0] if parts else ""
            out["metric"] = "link"
            for token in parts[1:]:
                if token.startswith("BW:"):
                    out["bandwidth"] = token[3:]
                elif token.startswith("out:"):
                    out["out_util"] = token[4:]
                elif token.startswith("in:"):
                    out["in_util"] = token[3:]
        return out

    @staticmethod
    def parse_map_areas(html: str) -> dict[str, Any]:
        title_m = re.search(
            r'cactiTableTitleRow">([^<[]+)',
            html,
            re.I,
        )
        title = unescape(title_m.group(1).strip()) if title_m else ""
        nodes: dict[str, dict[str, Any]] = {}
        links: dict[str, dict[str, Any]] = {}
        for line in html.splitlines():
            if "<area " not in line:
                continue
            m = AREA_LINE_RE.search(line)
            if not m:
                continue
            aid, cls, href, caption = m.group(1), m.group(2).lower(), m.group(3), m.group(4) or ""
            base_id = aid.rsplit(":", 1)[0] if ":" in aid else aid
            parsed = CactiGuestClient._parse_caption(caption)
            row: dict[str, Any] = {
                "area_id": aid,
                "href": unescape(href),
                **parsed,
            }
            obs = re.search(r"device=(\d+)", href)
            if obs:
                row["observium_device_id"] = obs.group(1)
            port = re.search(r"id=(\d+)", href)
            if port and "port_bits" in href:
                row["observium_port_id"] = port.group(1)
            bucket = nodes if cls == "node" else links
            bucket.setdefault(base_id, row)
        return {
            "title": title,
            "nodes": list(nodes.values()),
            "links": list(links.values()),
            "node_count": len(nodes),
            "link_count": len(links),
        }

    def list_graph_titles(
        self, query: Optional[str] = None, limit: int = 100, rows: int = 5000
    ) -> list[dict[str, str]]:
        # rows large enough to return all graphs on a single page (guest list view).
        resp = self.get("graph_view.php", {"action": "list", "rows": rows, "page": 1})
        graphs: list[dict[str, str]] = []
        for gid, title in GRAPH_ROW_RE.findall(resp.text):
            title = unescape(title.strip())
            if query and query.lower() not in title.lower():
                continue
            graphs.append(
                {
                    "local_graph_id": gid,
                    "title": title,
                    "graph_url": f"{self.base_url}/graph.php?local_graph_id={gid}&rra_id=0",
                }
            )
            if limit > 0 and len(graphs) >= limit:
                break
        return graphs


class CactiFullClient:
    """Authenticated Console access (requires Cacti account)."""

    def __init__(self, base_url: str, username: str, password: str, verify_ssl: bool) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.session.headers.update(
            {"User-Agent": "cacti-mcp/1.0 (read-only)", "Accept": "text/html,application/json,text/csv,*/*"}
        )
        self._logged_in = False

    def _csrf(self) -> str:
        resp = self.session.get(f"{self.base_url}/index.php", timeout=30)
        resp.raise_for_status()
        m = re.search(r'name=["\']__csrf_magic["\']\s+value=["\']([^"\']+)["\']', resp.text)
        if not m:
            raise RuntimeError("Could not find Cacti CSRF token on login page.")
        return m.group(1)

    def login(self) -> None:
        if not (self.username and self.password):
            raise RuntimeError("Missing CACTI_USER / CACTI_PASSWORD.")
        csrf = self._csrf()
        resp = self.session.post(
            f"{self.base_url}/index.php",
            data={
                "action": "login",
                "login_username": self.username,
                "login_password": self.password,
                "__csrf_magic": csrf,
            },
            timeout=30,
            allow_redirects=True,
        )
        resp.raise_for_status()
        if "Login to Cacti" in resp.text and "login_password" in resp.text:
            raise RuntimeError("Cacti login failed (invalid username/password or no Cacti account).")
        self._logged_in = True

    def ensure_login(self) -> None:
        if not self._logged_in:
            self.login()

    def get(self, path: str, params: Optional[dict[str, Any]] = None) -> requests.Response:
        self.ensure_login()
        full = urljoin(self.base_url + "/", path.lstrip("/"))
        resp = self.session.get(full, params=params or {}, timeout=120)
        resp.raise_for_status()
        return resp

    def export_hosts_csv(self, params: Optional[dict[str, Any]] = None) -> list[dict[str, str]]:
        q = dict(params or {})
        q["action"] = "export"
        resp = self.get("host.php", q)
        ctype = (resp.headers.get("content-type") or "").lower()
        text = resp.text
        if "html" in ctype or text.lstrip().startswith("<!"):
            raise RuntimeError("Expected CSV export from host.php but got HTML.")
        return list(csv.DictReader(io.StringIO(text)))


_guest: Optional[CactiGuestClient] = None
_full: Optional[CactiFullClient] = None
_resolved_mode: Optional[str] = None


def guest() -> CactiGuestClient:
    global _guest
    if _guest is None:
        _guest = CactiGuestClient(URL, WEATHERMAP_PATH, VERIFY_SSL)
    return _guest


def full() -> CactiFullClient:
    global _full
    if _full is None:
        _full = CactiFullClient(URL, USER, PASSWORD, VERIFY_SSL)
    return _full


def active_mode() -> str:
    """Resolve guest vs full once per process."""
    global _resolved_mode
    if _resolved_mode:
        return _resolved_mode
    if MODE == "guest":
        _resolved_mode = "guest"
        return _resolved_mode
    if MODE == "full":
        _resolved_mode = "full"
        return _resolved_mode
    # auto: try full login only when password explicitly set in env
    if os.environ.get("CACTI_PASSWORD"):
        try:
            full().login()
            _resolved_mode = "full"
            return _resolved_mode
        except Exception:
            pass
    _resolved_mode = "guest"
    return _resolved_mode


def _find_map(map_id: Optional[str] = None, name: Optional[str] = None) -> Optional[dict[str, str]]:
    maps = guest().parse_gallery(guest().gallery_html())
    if map_id:
        for m in maps:
            if m["id"] == map_id:
                return m
    if name:
        needle = name.lower()
        for m in maps:
            if needle in m["title"].lower():
                return m
    return None


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------
try:
    from fastmcp import FastMCP
except Exception:
    FastMCP = None  # type: ignore

if FastMCP is not None:
    mcp = FastMCP("cacti")

    @mcp.tool
    def cacti_status() -> dict[str, Any]:
        """Connectivity check. Guest mode: lists weathermap count; full mode: CSV device count."""
        mode = active_mode()
        if mode == "full":
            hosts = full().export_hosts_csv()
            return {
                "url": URL,
                "mode": "full",
                "user": USER,
                "ok": True,
                "device_count": len(hosts),
            }
        maps = guest().parse_gallery(guest().gallery_html())
        html = guest().gallery_html()
        logged_as = "guest" if "Logged in as" in html and ">guest<" in html else "unknown"
        return {
            "url": URL,
            "mode": "guest",
            "ok": True,
            "logged_in_as": logged_as,
            "weathermap_count": len(maps),
            "weathermaps": [m["title"] for m in maps],
            "note": "Guest access via Weathermap plugin — no Cacti Console password needed.",
        }

    @mcp.tool
    def list_weathermaps() -> dict[str, Any]:
        """List all network weathermaps visible to guest users."""
        maps = guest().parse_gallery(guest().gallery_html())
        return {"count": len(maps), "maps": maps}

    @mcp.tool
    def get_weathermap(map_id: Optional[str] = None, name: Optional[str] = None) -> dict[str, Any]:
        """Get one weathermap: nodes (devices) and links (utilization) parsed from the live map.

        Args:
            map_id: hex id from list_weathermaps (e.g. 21fc27cb8e963a6d4e80).
            name: substring match on map title (e.g. 'Sunnyvale', 'WAN').
        """
        if not map_id and not name:
            raise ValueError("Provide map_id or name.")
        meta = _find_map(map_id=map_id, name=name)
        if not meta:
            return {"found": False, "map_id": map_id, "name": name}
        detail = guest().parse_map_areas(guest().map_html(meta["id"]))
        return {"found": True, "map": meta, **detail}

    @mcp.tool
    def search_weathermap(query: str, limit: int = 50) -> dict[str, Any]:
        """Search device names and link labels across all guest weathermaps."""
        needle = query.lower()
        hits: list[dict[str, Any]] = []
        for meta in guest().parse_gallery(guest().gallery_html()):
            parsed = guest().parse_map_areas(guest().map_html(meta["id"]))
            for kind in ("nodes", "links"):
                for item in parsed[kind]:
                    caption = str(item.get("caption", ""))
                    hostname = str(item.get("hostname", ""))
                    if needle in caption.lower() or needle in hostname.lower():
                        hits.append(
                            {
                                "map_id": meta["id"],
                                "map_title": meta["title"],
                                "type": kind[:-1],
                                **item,
                            }
                        )
                        if limit > 0 and len(hits) >= limit:
                            return {"query": query, "count": len(hits), "results": hits}
        return {"query": query, "count": len(hits), "results": hits}

    @mcp.tool
    def list_graphs(
        query: Optional[str] = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """List Cacti graphs visible to guest users (graph_view list page).

        Titles usually include hostname + interface, e.g. 'fc01rt01 et-0/0/0'.
        """
        graphs = guest().list_graph_titles(query=query, limit=limit)
        return {"mode": active_mode(), "count": len(graphs), "graphs": graphs}

    @mcp.tool
    def list_hosts(
        query: Optional[str] = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        """List Cacti devices (full mode only — requires Console login).

        In guest mode, use list_weathermaps / search_weathermap instead.
        """
        if active_mode() != "full":
            return {
                "error": "full_mode_required",
                "message": "Device CSV export needs a Cacti Console account. "
                "Guest mode: use list_weathermaps or search_weathermap.",
                "mode": "guest",
            }
        rows = full().export_hosts_csv()
        if query:
            q = query.lower()
            rows = [
                r
                for r in rows
                if q in str(r.get("description", "")).lower()
                or q in str(r.get("hostname", "")).lower()
            ]
        total = len(rows)
        if limit > 0:
            rows = rows[:limit]
        return {"mode": "full", "count": total, "returned": len(rows), "hosts": rows}

    @mcp.tool
    def cacti_get(path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Generic read-only GET. Uses guest session unless full mode is active."""
        client: Any = full() if active_mode() == "full" else guest()
        if active_mode() == "full":
            full().ensure_login()
        resp = client.get(path, params)
        ctype = resp.headers.get("content-type", "")
        body = resp.text
        out: dict[str, Any] = {
            "mode": active_mode(),
            "url": resp.url,
            "status_code": resp.status_code,
            "content_type": ctype,
            "length": len(body),
        }
        if len(body) > 12000:
            out["text_preview"] = body[:12000]
            out["truncated"] = True
        else:
            out["text"] = body
        return out


def _selftest() -> int:
    print(f"URL={URL} MODE={MODE} VERIFY_SSL={VERIFY_SSL}")
    try:
        mode = active_mode()
        print(f"resolved_mode={mode}")
        if mode == "full":
            hosts = full().export_hosts_csv()
            print(f"device_count={len(hosts)}")
            for row in hosts[:3]:
                print(f"  - {row.get('description')} ({row.get('hostname')})")
        else:
            g = guest()
            maps = g.parse_gallery(g.gallery_html())
            print(f"weathermap_count={len(maps)}")
            for m in maps:
                print(f"  - {m['title']} id={m['id']}")
            if maps:
                sample = g.parse_map_areas(g.map_html(maps[0]["id"]))
                print(
                    f"sample_map={sample['title']} nodes={sample['node_count']} links={sample['link_count']}"
                )
            graphs = g.list_graph_titles(limit=3)
            print(f"sample_graphs={len(graphs)}")
            for gr in graphs:
                print(f"  - {gr['title'][:80]}")
    except Exception as e:  # noqa: BLE001
        print(f"FAILED: {e}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    if FastMCP is None:
        raise SystemExit("fastmcp not installed; cannot start MCP server.")
    mcp.run()
