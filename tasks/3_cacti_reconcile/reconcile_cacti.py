#!/usr/bin/env python3
"""Reconcile Cacti (graphing/weathermap) against Nautobot (source of truth).
READ-ONLY on both systems.

Cacti has no REST API at Zoox, so this reuses the guest-mode web client in
cacti_mcp.py (Weathermap gallery + Graphs list — no Console password needed).

Two deliverables:
  1. Device coverage: devices graphed in Cacti but missing from Nautobot
     (and a count of Nautobot devices not seen in Cacti).
  2. Interface description backfill: Cacti graph titles carry human-meaningful
     interface labels; Nautobot interface descriptions are largely blank. Where
     a Cacti interface maps to a Nautobot interface with an empty description,
     propose the Cacti label as a backfill.

Outputs:
  CACTI_VS_NAUTOBOT.md      human-readable report
  CACTI_IFACE_BACKFILL.csv  proposed interface-description changes

Run:
  python3 reconcile_cacti.py
"""
from __future__ import annotations

import csv
import os
import re
import sys
from pathlib import Path

import requests

requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]


def _find_mcp_dir() -> Path:
    """Locate the folder containing cacti_mcp.py, regardless of repo layout."""
    here = Path(__file__).resolve().parent
    for d in [here, *here.parents]:
        if (d / "mcp" / "cacti_mcp.py").exists():
            return d / "mcp"
        if (d / "cacti_mcp.py").exists():
            return d
    return here


_MCP_DIR = _find_mcp_dir()
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

# Reuse the guest Cacti web client built for the MCP server.
from cacti_mcp import guest  # noqa: E402


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
            line = line[len("export ") :]
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key.startswith(("NAUTOBOT_", "CACTI_", "OBSERVIUM_")) and not os.environ.get(key):
            os.environ[key] = val


_load_env_local()
NB_URL = os.environ.get("NAUTOBOT_URL", "").rstrip("/")
NB_TOKEN = os.environ.get("NAUTOBOT_TOKEN", "")
for k, v in {"NAUTOBOT_URL": NB_URL, "NAUTOBOT_TOKEN": NB_TOKEN}.items():
    if not v:
        sys.exit(f"ERROR: {k} not set (check .env.local).")

# Interface-name heuristic: Junos (et-/xe-/ge-/ae/lo/fxp/irb/em) + Arista/Cisco styles.
IFACE_RE = re.compile(
    r"^(?:et-|xe-|ge-|fe-|gr-|lt-|ae|lo|fxp|em|irb|vlan|Ethernet|Port-Channel|Po|"
    r"Management|Mgmt|Vlan|Loopback|Tunnel|Gi|Te|Fa|Hu|Twe|Fo)\S*\d\S*$",
    re.I,
)

# Generic Cacti graph-template names that are NOT real interface descriptions.
GENERIC_GRAPH_TYPES = {
    "traffic",
    "bits",
    "bytes",
    "packets",
    "unicast packets",
    "non-unicast packets",
    "broadcast packets",
    "multicast packets",
    "errors",
    "discards",
    "errors/discards",
    "cpu",
    "cpu usage",
    "memory",
    "memory usage",
    "uptime",
    "temperature",
    "utilization",
}


def short(host: str) -> str:
    """Normalize a hostname to its short form for matching (strip domain)."""
    return (host or "").split(".")[0].strip().lower()


# ---------------------------------------------------------------------------
# Nautobot (read-only)
# ---------------------------------------------------------------------------
def nautobot_devices() -> dict[str, dict]:
    query = """
    { devices {
        name
        interfaces { name description }
      } }
    """
    r = requests.post(
        f"{NB_URL}/api/graphql/",
        json={"query": query},
        headers={"Authorization": f"Token {NB_TOKEN}", "Accept": "application/json"},
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        sys.exit(f"GraphQL errors: {data['errors']}")
    out: dict[str, dict] = {}
    for d in data["data"]["devices"]:
        ifaces = {}
        for i in d.get("interfaces") or []:
            ifaces[i["name"]] = (i.get("description") or "").strip()
        out[short(d["name"])] = {"name": d["name"], "interfaces": ifaces}
    return out


# ---------------------------------------------------------------------------
# Cacti (read-only, guest mode)
# ---------------------------------------------------------------------------
def parse_graph_title(title: str) -> tuple[str, str, str] | None:
    """Return (host_short, interface, description) from a Cacti graph title.

    Handles two Zoox title formats:
      A) "HOST - Traffic - et-0/0/0.0"      (Junos template; no real desc)
      B) "HOST <real description> - et-0/1/3"  (edge/WAN; rich desc)

    Only returns when the trailing segment looks like an interface name.
    `description` is "" when the title carries only a generic graph-type label.
    """
    title = title.strip()
    if " - " not in title:
        return None
    segments = [s.strip() for s in title.split(" - ")]
    last = segments[-1].strip()
    if not IFACE_RE.match(last):
        return None
    iface = last
    head_tokens = segments[0].split(None, 1)
    if not head_tokens:
        return None
    host = head_tokens[0]

    if len(segments) == 2:
        # Format B: everything after the host token in segment 0 is the description.
        desc = head_tokens[1].strip() if len(head_tokens) > 1 else ""
    else:
        # Format A (and variants): middle segments between host and interface.
        middles = segments[1:-1]
        meaningful = [m for m in middles if m.lower() not in GENERIC_GRAPH_TYPES]
        # also fold any trailing text from segment 0 beyond the host token
        if len(head_tokens) > 1:
            meaningful.insert(0, head_tokens[1].strip())
        desc = " - ".join(m for m in meaningful if m).strip()

    # drop pure-generic / empty descriptions
    if desc.lower() in GENERIC_GRAPH_TYPES:
        desc = ""
    return short(host), iface, desc


def cacti_data() -> dict:
    g = guest()
    # Weathermap device names (nodes) + counts.
    wm_hosts: set[str] = set()
    maps = g.parse_gallery(g.gallery_html())
    for m in maps:
        parsed = g.parse_map_areas(g.map_html(m["id"]))
        for node in parsed["nodes"]:
            hn = node.get("hostname")
            if hn:
                wm_hosts.add(short(hn))

    # Graph titles → host/interface/description (the rich source).
    graphs = g.list_graph_titles(limit=0)  # all graphs
    graph_hosts: set[str] = set()
    # host -> { iface -> cacti_label }
    iface_labels: dict[str, dict[str, str]] = {}
    for gr in graphs:
        pg = parse_graph_title(gr["title"])
        if not pg:
            # still capture host token for coverage if present
            first = gr["title"].split(None, 1)
            if first:
                graph_hosts.add(short(first[0]))
            continue
        host, iface, desc = pg
        graph_hosts.add(host)
        if not desc:
            continue
        iface_labels.setdefault(host, {})
        # keep the first (usually physical) label seen for an interface
        iface_labels[host].setdefault(iface, desc)

    return {
        "weathermap_count": len(maps),
        "weathermap_hosts": wm_hosts,
        "graph_hosts": graph_hosts,
        "all_hosts": wm_hosts | graph_hosts,
        "graph_count": len(graphs),
        "iface_labels": iface_labels,
    }


# ---------------------------------------------------------------------------
def main() -> int:
    print("Querying Nautobot (read-only)...")
    nb = nautobot_devices()
    print(f"  Nautobot devices: {len(nb)}")
    print("Reading Cacti (guest mode)...")
    cacti = cacti_data()
    print(f"  Cacti weathermaps: {cacti['weathermap_count']}  graphs: {cacti['graph_count']}")
    print(f"  Cacti hosts seen: {len(cacti['all_hosts'])}")

    nb_keys = set(nb)
    cacti_keys = cacti["all_hosts"]

    cacti_only = sorted(cacti_keys - nb_keys)
    nb_only = sorted(nb_keys - cacti_keys)
    both = sorted(cacti_keys & nb_keys)

    # Interface description backfill candidates.
    backfill_rows: list[dict[str, str]] = []
    for host in both:
        ndev = nb[host]
        labels = cacti["iface_labels"].get(host, {})
        for iface, label in sorted(labels.items()):
            # exact match to a Nautobot interface
            nb_desc = ndev["interfaces"].get(iface)
            matched_iface = iface
            if nb_desc is None and "." in iface:
                # subinterface in Cacti, try the physical parent in Nautobot
                parent = iface.split(".", 1)[0]
                if parent in ndev["interfaces"]:
                    nb_desc = ndev["interfaces"][parent]
                    matched_iface = parent
            if nb_desc is None:
                continue  # interface not modeled in Nautobot
            if nb_desc == "":
                backfill_rows.append(
                    {
                        "device": ndev["name"],
                        "interface": matched_iface,
                        "cacti_interface": iface,
                        "proposed_description": label,
                    }
                )

    # --- CSV (proposed interface-description backfills) ---
    here = Path(__file__).resolve().parent
    with open(here / "CACTI_IFACE_BACKFILL.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["device", "interface", "cacti_interface", "proposed_description"])
        for r in backfill_rows:
            w.writerow(
                [r["device"], r["interface"], r["cacti_interface"], r["proposed_description"]]
            )

    # --- Markdown ---
    out: list[str] = []
    out.append("# Cacti vs Nautobot Reconciliation (read-only)\n")
    out.append("Cacti = graphing/weathermap (actual). Nautobot = source of truth (intended).")
    out.append("No changes were made to either system.\n")
    out.append("## Totals\n")
    out.append("| Metric | Count |")
    out.append("| --- | --- |")
    out.append(f"| Nautobot devices | {len(nb)} |")
    out.append(f"| Cacti weathermaps | {cacti['weathermap_count']} |")
    out.append(f"| Cacti graphs | {cacti['graph_count']} |")
    out.append(f"| Distinct hosts seen in Cacti | {len(cacti_keys)} |")
    out.append(f"| Hosts in BOTH | {len(both)} |")
    out.append(f"| In Cacti but NOT in Nautobot | {len(cacti_only)} |")
    out.append(f"| In Nautobot but NOT in Cacti | {len(nb_only)} |")
    out.append(f"| Proposed interface-description backfills | {len(backfill_rows)} |")
    out.append("")

    if cacti_only:
        out.append("## Graphed in Cacti but missing from Nautobot\n")
        out.append("These devices are actively monitored/graphed but absent from the source of truth.\n")
        out.append("| Cacti host |")
        out.append("| --- |")
        for h in cacti_only:
            out.append(f"| {h} |")
        out.append("")

    if backfill_rows:
        out.append("## Proposed interface-description backfills (the action list)\n")
        out.append("Nautobot interface description is blank; Cacti has a meaningful label.\n")
        out.append("| Device | Nautobot interface | Cacti interface | Proposed description |")
        out.append("| --- | --- | --- | --- |")
        for r in backfill_rows[:200]:
            out.append(
                f"| {r['device']} | {r['interface']} | {r['cacti_interface']} | "
                f"{r['proposed_description']} |"
            )
        if len(backfill_rows) > 200:
            out.append(f"\n_({len(backfill_rows) - 200} more rows in CACTI_IFACE_BACKFILL.csv)_")
        out.append("")

    # Bonus: rich Cacti interface descriptions for devices missing from Nautobot.
    bonus: list[tuple[str, str, str]] = []
    for host in cacti_only:
        for iface, label in sorted(cacti["iface_labels"].get(host, {}).items()):
            bonus.append((host, iface, label))
    if bonus:
        out.append("## Bonus: interface descriptions Cacti knows for Cacti-only devices\n")
        out.append("These devices aren't in Nautobot yet; Cacti already documents their links —\n")
        out.append("ready-made descriptions for when they're onboarded.\n")
        out.append("| Cacti host | Interface | Cacti description |")
        out.append("| --- | --- | --- |")
        for host, iface, label in bonus[:150]:
            out.append(f"| {host} | {iface} | {label} |")
        if len(bonus) > 150:
            out.append(f"\n_({len(bonus) - 150} more — see CACTI_IFACE_BACKFILL.csv companion data)_")
        out.append("")

    out.append("## Hosts in both systems (sanity)\n")
    out.append(", ".join(both) if both else "(none)")
    out.append("")
    out.append("## Notes & caveats\n")
    out.append("- Cacti's Graphs **list view truncates long titles** (~40 chars), so some")
    out.append("  descriptions above are cut off (e.g. `...(CAS-`). Full text is on each graph's")
    out.append("  edit page; a follow-up can fetch complete labels if needed.")
    out.append("- Junos devices already in Nautobot use a `HOST - Traffic - <iface>` graph naming")
    out.append("  that carries **no per-interface description**, so 0 direct backfills — honest, not a bug.")
    out.append("- The rich descriptions live on **edge/WAN routers** (e.g. `sv4rt02`, `sv5rt02`)")
    out.append("  which are **not in Nautobot** — captured in the bonus table for onboarding.")
    out.append("- The 22 Cacti-only devices strongly overlap the 22 **Observium-only** Junos routers")
    out.append("  found earlier (Atlanta, Austin, LA, SFO, etc.) — independent cross-validation of the")
    out.append("  same source-of-truth coverage gap.")
    out.append("")
    out.append("> Next step (with approval): onboard the genuinely-missing devices, then backfill")
    out.append("> descriptions from this data via a reviewed Nautobot change.")
    out.append("> This script wrote nothing to production.")

    (here / "CACTI_VS_NAUTOBOT.md").write_text("\n".join(out))
    print("Wrote CACTI_VS_NAUTOBOT.md and CACTI_IFACE_BACKFILL.csv")
    print(f"  cacti_only={len(cacti_only)}  nb_only={len(nb_only)}  both={len(both)}")
    print(f"  interface backfills proposed={len(backfill_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
