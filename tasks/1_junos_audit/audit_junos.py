#!/usr/bin/env python3
"""Read-only audit of Junos devices in production Nautobot.

Asks Nautobot's GraphQL API for every juniper_junos device and reports which
important fields are empty (software_version, interface descriptions, primary
IP, serial). Writes JUNOS_AUDIT.md. Does NOT modify anything.

Run:
    set -a && . ./.env.local && set +a
    python3 audit_junos.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

# --- load creds from .env.local if not already in the environment ---------
def _load_env_local() -> None:
    here = Path(__file__).resolve().parent
    env_path = next((d / ".env.local" for d in [here, *here.parents] if (d / ".env.local").exists()), None)
    if env_path is None:
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key.startswith("NAUTOBOT_") and not os.environ.get(key):
            os.environ[key] = val


_load_env_local()
URL = os.environ.get("NAUTOBOT_URL", "").rstrip("/")
TOKEN = os.environ.get("NAUTOBOT_TOKEN", "")
if not URL or not TOKEN:
    sys.exit("ERROR: NAUTOBOT_URL / NAUTOBOT_TOKEN not set (check .env.local).")

# Management-only interface names: if a device has ONLY these, its interface
# inventory is probably incomplete (real uplinks not modeled yet).
MGMT_ONLY = {"fxp0.0", "fxp0 (re0)", "fxp0 (re1)", "re0:mgmt-0.0", "re1:mgmt-0.0"}

QUERY = """
{
  devices(platform: "juniper_junos") {
    name
    serial
    software_version { version }
    primary_ip4 { address }
    device_type { model }
    location { name }
    status { name }
    interfaces { name description }
  }
}
"""


def fetch():
    resp = requests.post(
        f"{URL}/api/graphql/",
        json={"query": QUERY},
        headers={"Authorization": f"Token {TOKEN}", "Accept": "application/json"},
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json()
    if "errors" in payload:
        sys.exit(f"GraphQL errors: {payload['errors']}")
    return payload["data"]["devices"]


def main() -> int:
    devices = fetch()
    rows = []
    n_no_version = n_no_ip = n_no_serial = n_mgmt_only = 0
    total_ifaces = blank_ifaces = 0

    for d in devices:
        name = d["name"]
        model = (d.get("device_type") or {}).get("model") or "-"
        version = (d.get("software_version") or {}).get("version")
        ip = (d.get("primary_ip4") or {}).get("address")
        serial = d.get("serial") or ""
        ifaces = d.get("interfaces") or []
        names = {i["name"] for i in ifaces}
        blanks = sum(1 for i in ifaces if not (i.get("description") or "").strip())

        total_ifaces += len(ifaces)
        blank_ifaces += blanks
        mgmt_only = bool(names) and names.issubset(MGMT_ONLY)

        if not version:
            n_no_version += 1
        if not ip:
            n_no_ip += 1
        if not serial:
            n_no_serial += 1
        if mgmt_only:
            n_mgmt_only += 1

        flags = []
        if not version:
            flags.append("no-version")
        if not ip:
            flags.append("no-mgmt-ip")
        if not serial:
            flags.append("no-serial")
        if mgmt_only:
            flags.append("mgmt-only-ifaces")
        if ifaces and blanks == len(ifaces):
            flags.append("all-desc-blank")

        rows.append({
            "name": name, "model": model, "version": version or "—",
            "ip": ip or "—", "serial": serial or "—",
            "ifaces": len(ifaces), "blank_desc": blanks,
            "flags": ", ".join(flags) or "ok",
        })

    rows.sort(key=lambda r: (r["flags"] == "ok", r["name"]))
    total = len(devices)

    out = []
    out.append("# Junos Data-Quality Audit (Nautobot, read-only)\n")
    out.append(f"- Source: `{URL}` (GraphQL, read-only)")
    out.append(f"- Junos devices audited: **{total}**\n")
    out.append("## Summary of gaps\n")
    out.append("| Gap | Devices affected |")
    out.append("| --- | --- |")
    out.append(f"| Missing `software_version` | {n_no_version} / {total} |")
    out.append(f"| Missing `primary_ip4` (mgmt IP) | {n_no_ip} / {total} |")
    out.append(f"| Missing `serial` | {n_no_serial} / {total} |")
    out.append(f"| Interface inventory mgmt-only | {n_mgmt_only} / {total} |")
    out.append(
        f"| Blank interface descriptions | {blank_ifaces} / {total_ifaces} interfaces |"
    )
    out.append("")
    out.append("## Per-device detail\n")
    out.append("| Device | Model | Version | Mgmt IP | Serial | Ifaces | Blank desc | Flags |")
    out.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        out.append(
            f"| {r['name']} | {r['model']} | {r['version']} | {r['ip']} | "
            f"{r['serial']} | {r['ifaces']} | {r['blank_desc']} | {r['flags']} |"
        )
    out.append("")
    out.append("## Suggested priorities (propose-only — no writes made)\n")
    out.append("1. Backfill `software_version` (Observium already has these — see Task 2).")
    out.append("2. Add management IPs for devices flagged `no-mgmt-ip` (needed for automation).")
    out.append("3. Complete interface inventory for `mgmt-only-ifaces` devices.")
    out.append("4. Add interface descriptions (intent) for key uplinks.")
    out.append("")

    (Path(__file__).resolve().parent / "JUNOS_AUDIT.md").write_text("\n".join(out))
    print(f"Audited {total} Junos devices. Wrote JUNOS_AUDIT.md")
    print(f"  no-version={n_no_version}  no-ip={n_no_ip}  no-serial={n_no_serial}  "
          f"mgmt-only={n_mgmt_only}  blank-desc={blank_ifaces}/{total_ifaces}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
