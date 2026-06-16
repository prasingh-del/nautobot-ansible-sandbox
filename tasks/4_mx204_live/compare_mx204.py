#!/usr/bin/env python3
"""Compare the REAL MX204 (show outputs gathered by Ansible) vs Nautobot (SoT).

Parses mx204_output/*.txt (written by playbook_mx204.yml) for model, serial,
OS version, hostname, and physical interfaces, then queries Nautobot read-only
for the matching device and reports differences. Writes MX204_VS_NAUTOBOT.md.

Run (after the playbook):
    python3 compare_mx204.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
OUT = HERE / "mx204_output"


def _load_env_local() -> None:
    env_path = next((d / ".env.local" for d in [HERE, *HERE.parents] if (d / ".env.local").exists()), None)
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
        if (key.startswith("NAUTOBOT_") or key.startswith("MX204_")) and not os.environ.get(key):
            os.environ[key] = val


_load_env_local()
NB_URL = os.environ.get("NAUTOBOT_URL", "").rstrip("/")
NB_TOKEN = os.environ.get("NAUTOBOT_TOKEN", "")


def read(name: str) -> str:
    p = OUT / f"{name}.txt"
    return p.read_text(errors="replace") if p.exists() else ""


def short(host: str) -> str:
    return (host or "").split(".")[0].strip().lower()


def parse_device() -> dict:
    version_txt = read("version")
    chassis_txt = read("chassis_hardware")
    terse_txt = read("interfaces_terse")

    hostname = (re.search(r"(?im)^Hostname:\s*(\S+)", version_txt) or [None, ""])[1] \
        if re.search(r"(?im)^Hostname:\s*(\S+)", version_txt) else ""
    model = ""
    m = re.search(r"(?im)^Model:\s*(\S+)", version_txt)
    if m:
        model = m.group(1)
    version = ""
    m = re.search(r"(?im)^Junos:\s*(\S+)", version_txt)
    if m:
        version = m.group(1)
    else:  # EVO / alternate format: "... [21.4R3.15]"
        m = re.search(r"\[([\d][^\]]+)\]", version_txt)
        if m:
            version = m.group(1)
    serial = ""
    m = re.search(r"(?im)^Chassis\s+(\S+)", chassis_txt)
    if m:
        serial = m.group(1)

    # physical interfaces from "show interfaces terse": first column, no logical unit (.N)
    ifaces = set()
    for line in terse_txt.splitlines():
        if not line or line[0].isspace():
            continue
        tok = line.split()[0]
        if tok.lower() in ("interface",):
            continue
        if "." in tok:
            continue
        if re.match(r"^[a-z]+\d|^[a-z]+-\d", tok):
            ifaces.add(tok)
    return {
        "hostname": hostname, "model": model, "version": version,
        "serial": serial, "interfaces": sorted(ifaces),
    }


def nautobot_device(name: str) -> dict | None:
    query = """
    query ($name: [String]) {
      devices(name: $name) {
        name serial
        software_version { version }
        device_type { model }
        interfaces { name }
      }
    }
    """
    r = requests.post(
        f"{NB_URL}/api/graphql/",
        json={"query": query, "variables": {"name": [name]}},
        headers={"Authorization": f"Token {NB_TOKEN}", "Accept": "application/json"},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        sys.exit(f"GraphQL errors: {data['errors']}")
    devs = data["data"]["devices"]
    return devs[0] if devs else None


def verdict(dev: str, nb: str) -> str:
    if not nb:
        return "NB-EMPTY"
    if not dev:
        return "DEV-EMPTY"
    return "MATCH" if dev.strip().lower() == nb.strip().lower() else "DIFF"


def main() -> int:
    if not OUT.exists():
        sys.exit(f"{OUT} not found. Run playbook_mx204.yml first.")
    if not (NB_URL and NB_TOKEN):
        sys.exit("NAUTOBOT_URL / NAUTOBOT_TOKEN not set (check .env.local).")

    dev = parse_device()
    nb_name = os.environ.get("MX204_NAUTOBOT_NAME") or short(dev["hostname"])
    nb = nautobot_device(nb_name) if nb_name else None

    out = []
    out.append("# MX204: Real Device vs Nautobot (read-only)\n")
    out.append(f"- Device hostname (from box): `{dev['hostname'] or '?'}`")
    out.append(f"- Device model/serial/version: `{dev['model']}` / `{dev['serial']}` / `{dev['version']}`")
    out.append(f"- Compared against Nautobot device: `{nb_name or '(unknown)'}`\n")

    if not nb:
        out.append(f"> Nautobot has no device named `{nb_name}`. Set MX204_NAUTOBOT_NAME "
                   "in .env.local to compare against a specific device.\n")
        out.append(f"Device reports **{len(dev['interfaces'])}** physical interfaces:\n")
        out.append(", ".join(dev["interfaces"]) or "(none parsed)")
        (HERE / "MX204_VS_NAUTOBOT.md").write_text("\n".join(out))
        print(f"Nautobot device '{nb_name}' not found. Wrote MX204_VS_NAUTOBOT.md (device-only).")
        return 0

    nb_model = (nb.get("device_type") or {}).get("model") or ""
    nb_version = (nb.get("software_version") or {}).get("version") or ""
    nb_serial = nb.get("serial") or ""
    nb_ifaces = {i["name"] for i in (nb.get("interfaces") or [])}
    dev_ifaces = set(dev["interfaces"])

    out.append("## Field comparison\n")
    out.append("| Field | Real device | Nautobot | Result |")
    out.append("| --- | --- | --- | --- |")
    out.append(f"| Model | {dev['model'] or '—'} | {nb_model or '—'} | {verdict(dev['model'], nb_model)} |")
    out.append(f"| Serial | {dev['serial'] or '—'} | {nb_serial or '—'} | {verdict(dev['serial'], nb_serial)} |")
    out.append(f"| OS version | {dev['version'] or '—'} | {nb_version or '—'} | {verdict(dev['version'], nb_version)} |")
    out.append("")

    only_dev = sorted(dev_ifaces - nb_ifaces)
    only_nb = sorted(nb_ifaces - dev_ifaces)
    both = sorted(dev_ifaces & nb_ifaces)
    out.append("## Physical interface inventory\n")
    out.append(f"- On device AND in Nautobot: **{len(both)}**")
    out.append(f"- On device but MISSING from Nautobot: **{len(only_dev)}**")
    out.append(f"- In Nautobot but NOT on device: **{len(only_nb)}**\n")
    if only_dev:
        out.append("### On the real device but missing in Nautobot")
        out.append(", ".join(only_dev) + "\n")
    if only_nb:
        out.append("### In Nautobot but not seen on the device")
        out.append(", ".join(only_nb) + "\n")
    out.append("> Read-only comparison. Nothing was changed on the device or in Nautobot.")

    (HERE / "MX204_VS_NAUTOBOT.md").write_text("\n".join(out))
    print(f"Compared device '{dev['hostname']}' vs Nautobot '{nb_name}'. Wrote MX204_VS_NAUTOBOT.md")
    print(f"  model={verdict(dev['model'], nb_model)} serial={verdict(dev['serial'], nb_serial)} "
          f"version={verdict(dev['version'], nb_version)} "
          f"ifaces dev_only={len(only_dev)} nb_only={len(only_nb)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
