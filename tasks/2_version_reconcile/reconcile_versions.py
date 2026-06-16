#!/usr/bin/env python3
"""Reconcile Junos OS versions between Nautobot (source of truth) and Observium
(live monitoring). READ-ONLY on both systems.

Produces a proposed backfill list for Nautobot's empty software_version fields,
using the versions Observium has already discovered. Writes:
    VERSION_RECONCILE.md   human-readable report
    VERSION_RECONCILE.csv  machine-readable proposed changes

Run:
    python3 reconcile_versions.py
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import requests

requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]


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
        if (key.startswith("NAUTOBOT_") or key.startswith("OBSERVIUM_")) and not os.environ.get(key):
            os.environ[key] = val


_load_env_local()
NB_URL = os.environ.get("NAUTOBOT_URL", "").rstrip("/")
NB_TOKEN = os.environ.get("NAUTOBOT_TOKEN", "")
OBS_URL = os.environ.get("OBSERVIUM_URL", "").rstrip("/")
OBS_USER = os.environ.get("OBSERVIUM_USER", "")
OBS_PASS = os.environ.get("OBSERVIUM_PASSWORD", "")
for k, v in {"NAUTOBOT_URL": NB_URL, "NAUTOBOT_TOKEN": NB_TOKEN,
             "OBSERVIUM_URL": OBS_URL, "OBSERVIUM_USER": OBS_USER,
             "OBSERVIUM_PASSWORD": OBS_PASS}.items():
    if not v:
        sys.exit(f"ERROR: {k} not set (check .env.local).")


def short(host: str) -> str:
    """Normalize a hostname to its short form for matching (strip domain)."""
    return (host or "").split(".")[0].strip().lower()


def nautobot_junos() -> dict[str, dict]:
    query = """
    { devices(platform: "juniper_junos") {
        name software_version { version } primary_ip4 { address }
      } }
    """
    r = requests.post(
        f"{NB_URL}/api/graphql/", json={"query": query},
        headers={"Authorization": f"Token {NB_TOKEN}", "Accept": "application/json"},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        sys.exit(f"GraphQL errors: {data['errors']}")
    out = {}
    for d in data["data"]["devices"]:
        out[short(d["name"])] = {
            "name": d["name"],
            "version": (d.get("software_version") or {}).get("version"),
        }
    return out


def observium_devices() -> dict[str, dict]:
    r = requests.get(
        f"{OBS_URL}/api/v0/devices/", params={"pagesize": 2000},
        auth=(OBS_USER, OBS_PASS), headers={"Accept": "application/json"},
        verify=False, timeout=60,
    )
    r.raise_for_status()
    devs = r.json().get("devices") or {}
    items = devs.values() if isinstance(devs, dict) else devs
    out = {}
    for d in items:
        out[short(d.get("hostname", ""))] = {
            "hostname": d.get("hostname"),
            "version": d.get("version"),
            "os": d.get("os"),
            "status": d.get("status"),
        }
    return out


def main() -> int:
    nb = nautobot_junos()
    obs = observium_devices()

    rows = []
    counts = {"BACKFILL": 0, "MATCH": 0, "MISMATCH": 0, "NOT_IN_OBSERVIUM": 0}
    for key, ndev in sorted(nb.items()):
        odev = obs.get(key)
        nb_v = ndev["version"]
        obs_v = odev["version"] if odev else None
        if not odev:
            action = "NOT_IN_OBSERVIUM"
        elif not nb_v and obs_v:
            action = "BACKFILL"
        elif nb_v and obs_v and nb_v == obs_v:
            action = "MATCH"
        elif nb_v and obs_v and nb_v != obs_v:
            action = "MISMATCH"
        else:
            action = "NOT_IN_OBSERVIUM"
        counts[action] = counts.get(action, 0) + 1
        rows.append({
            "device": ndev["name"],
            "nautobot_version": nb_v or "",
            "observium_version": obs_v or "",
            "action": action,
        })

    # Bonus: Junos devices Observium monitors but Nautobot doesn't know about
    nb_keys = set(nb)
    obs_only = [
        o for k, o in sorted(obs.items())
        if k not in nb_keys and str(o.get("os", "")).startswith("junos")
    ]

    # --- CSV (proposed changes only: BACKFILL + MISMATCH) ---
    here = Path(__file__).resolve().parent
    with open(here / "VERSION_RECONCILE.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["device", "nautobot_version", "observium_version", "action"])
        for r in rows:
            if r["action"] in ("BACKFILL", "MISMATCH"):
                w.writerow([r["device"], r["nautobot_version"], r["observium_version"], r["action"]])

    # --- Markdown ---
    out = []
    out.append("# Junos OS Version Reconciliation: Nautobot vs Observium\n")
    out.append("Read-only comparison. No changes were made to either system.\n")
    out.append(f"- Nautobot Junos devices: **{len(nb)}**")
    out.append(f"- Observium devices indexed: **{len(obs)}**\n")
    out.append("## Outcome counts\n")
    out.append("| Action | Meaning | Count |")
    out.append("| --- | --- | --- |")
    out.append(f"| BACKFILL | Nautobot empty, Observium has version → propose adding | {counts['BACKFILL']} |")
    out.append(f"| MATCH | Already agree | {counts['MATCH']} |")
    out.append(f"| MISMATCH | Both set but differ → investigate | {counts['MISMATCH']} |")
    out.append(f"| NOT_IN_OBSERVIUM | No Observium match to source from | {counts['NOT_IN_OBSERVIUM']} |")
    out.append("")
    out.append("## Proposed backfills / mismatches (the action list)\n")
    out.append("| Device | Nautobot | Observium | Action |")
    out.append("| --- | --- | --- | --- |")
    for r in rows:
        if r["action"] in ("BACKFILL", "MISMATCH"):
            out.append(f"| {r['device']} | {r['nautobot_version'] or '—'} | "
                       f"{r['observium_version'] or '—'} | {r['action']} |")
    out.append("")
    out.append("## Full comparison\n")
    out.append("| Device | Nautobot | Observium | Action |")
    out.append("| --- | --- | --- | --- |")
    for r in rows:
        out.append(f"| {r['device']} | {r['nautobot_version'] or '—'} | "
                   f"{r['observium_version'] or '—'} | {r['action']} |")
    out.append("")
    if obs_only:
        out.append("## Bonus: Junos devices in Observium but NOT in Nautobot\n")
        out.append("These are monitored but missing from the source of truth.\n")
        out.append("| Observium hostname | Version | Status |")
        out.append("| --- | --- | --- |")
        for o in obs_only:
            st = "up" if str(o.get("status")) == "1" else "down"
            out.append(f"| {o.get('hostname')} | {o.get('version') or '—'} | {st} |")
        out.append("")
    out.append("> Next step (with approval): apply BACKFILL rows to Nautobot via a reviewed change.")
    out.append("> This script wrote nothing to production.")

    (here / "VERSION_RECONCILE.md").write_text("\n".join(out))
    print("Wrote VERSION_RECONCILE.md and VERSION_RECONCILE.csv")
    print(f"  BACKFILL={counts['BACKFILL']}  MATCH={counts['MATCH']}  "
          f"MISMATCH={counts['MISMATCH']}  NOT_IN_OBSERVIUM={counts['NOT_IN_OBSERVIUM']}")
    print(f"  Bonus (Observium-only Junos): {len(obs_only)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
