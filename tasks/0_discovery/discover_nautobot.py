#!/usr/bin/env python3

import os
import sys
import requests
from collections import Counter, defaultdict

NAUTOBOT_URL = os.getenv("NAUTOBOT_URL", "").rstrip("/")
TOKEN = os.getenv("NAUTOBOT_TOKEN", "")

if not NAUTOBOT_URL or not TOKEN:
    sys.exit("ERROR: source .env.local first")

HEADERS = {
    "Authorization": f"Token {TOKEN}",
    "Accept": "application/json",
}

session = requests.Session()
session.headers.update(HEADERS)


def fetch_all(endpoint, limit=100):
    url = f"{NAUTOBOT_URL}/api/{endpoint}/"
    results = []
    offset = 0

    while True:
        r = session.get(url, params={"limit": limit, "offset": offset}, timeout=30)
        r.raise_for_status()
        data = r.json()
        results.extend(data.get("results", []))

        if not data.get("next"):
            return results, data.get("count", len(results))

        offset += limit


def label(obj):
    if not obj:
        return "None"
    if isinstance(obj, str):
        return obj
    return obj.get("display") or obj.get("name") or obj.get("model") or obj.get("label") or obj.get("id") or "Unknown"


def nested_id(obj):
    if isinstance(obj, dict):
        return obj.get("id")
    return None


print("Fetching Nautobot data...")

devices, device_count = fetch_all("dcim/devices")
device_types, _ = fetch_all("dcim/device-types")
manufacturers, _ = fetch_all("dcim/manufacturers")
roles, _ = fetch_all("extras/roles")
locations, _ = fetch_all("dcim/locations")
platforms, _ = fetch_all("dcim/platforms")

device_type_by_id = {dt["id"]: dt for dt in device_types}
manufacturer_by_id = {m["id"]: m for m in manufacturers}

role_counts = Counter()
location_counts = Counter()
type_counts = Counter()
manufacturer_counts = Counter()
status_counts = Counter()
platform_counts = Counter()

candidate_juniper = []
candidate_cisco = []
candidate_mx204 = []
missing_primary_ip = []

for d in devices:
    name = d.get("name", "Unknown")
    role_counts[label(d.get("role"))] += 1
    location_counts[label(d.get("location"))] += 1
    status_counts[label(d.get("status"))] += 1
    platform_counts[label(d.get("platform"))] += 1

    dt_id = nested_id(d.get("device_type"))
    dt = device_type_by_id.get(dt_id, {})
    dt_name = label(dt)
    type_counts[dt_name] += 1

    mfg = label(dt.get("manufacturer"))
    manufacturer_counts[mfg] += 1

    searchable = f"{name} {dt_name} {mfg} {label(d.get('role'))}".lower()

    if "juniper" in searchable:
        candidate_juniper.append((name, dt_name, label(d.get("role")), label(d.get("location"))))

    if "cisco" in searchable:
        candidate_cisco.append((name, dt_name, label(d.get("role")), label(d.get("location"))))

    if "mx204" in searchable:
        candidate_mx204.append((name, dt_name, label(d.get("role")), label(d.get("location"))))

    if not d.get("primary_ip4") and not d.get("primary_ip6"):
        missing_primary_ip.append((name, dt_name, label(d.get("role")), label(d.get("location"))))


def top(counter, n=20):
    return counter.most_common(n)


def table(rows, headers):
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(x).replace("|", "/") for x in row) + " |")
    return "\n".join(lines)


report = []

report.append("# Org Nautobot Discovery Report\n")
report.append("## Summary\n")
report.append(f"- Nautobot URL: `{NAUTOBOT_URL}`")
report.append(f"- Device count: `{device_count}`")
report.append(f"- Device type count: `{len(device_types)}`")
report.append(f"- Manufacturer count: `{len(manufacturers)}`")
report.append(f"- Role count: `{len(roles)}`")
report.append(f"- Location count: `{len(locations)}`")
report.append("")

report.append("## Top Device Roles\n")
report.append(table(top(role_counts), ["Role", "Count"]))
report.append("")

report.append("## Top Manufacturers\n")
report.append(table(top(manufacturer_counts), ["Manufacturer", "Count"]))
report.append("")

report.append("## Top Device Types\n")
report.append(table(top(type_counts), ["Device Type", "Count"]))
report.append("")

report.append("## Top Locations\n")
report.append(table(top(location_counts), ["Location", "Count"]))
report.append("")

report.append("## Status Counts\n")
report.append(table(top(status_counts), ["Status", "Count"]))
report.append("")

report.append("## Candidate Juniper Devices\n")
report.append(table(candidate_juniper[:50], ["Device", "Type", "Role", "Location"]) if candidate_juniper else "No Juniper candidates found.")
report.append("")

report.append("## Candidate Cisco Devices\n")
report.append(table(candidate_cisco[:50], ["Device", "Type", "Role", "Location"]) if candidate_cisco else "No Cisco candidates found.")
report.append("")

report.append("## Candidate MX204 Devices\n")
report.append(table(candidate_mx204[:50], ["Device", "Type", "Role", "Location"]) if candidate_mx204 else "No MX204 candidates found.")
report.append("")

report.append("## Devices Missing Primary IP - First 50\n")
report.append(table(missing_primary_ip[:50], ["Device", "Type", "Role", "Location"]))
report.append("")

report.append("## Automation Ideas\n")
report.append("- Generate interface configs from Nautobot data.")
report.append("- Report devices missing primary IPs.")
report.append("- Report network interfaces missing descriptions.")
report.append("- Generate intended config for Juniper MX devices.")
report.append("- Generate intended config for Cisco switches.")
report.append("- Compare Nautobot intended state vs device running config.")
report.append("- Build pre-change validation before any config push.")
report.append("")

report.append("## Safe Verification Framework\n")
report.append("Before automating any change:")
report.append("1. Baseline: capture current Nautobot data and current device config.")
report.append("2. Dry run: generate intended config locally only.")
report.append("3. Diff: compare intended config vs current config.")
report.append("4. Review: confirm with network team.")
report.append("5. Apply only on test device first.")
report.append("6. Validate after change.")
report.append("7. Keep rollback command ready.")

output = "\n".join(report)

with open("ORG_NAUTOBOT_DISCOVERY.md", "w") as f:
    f.write(output)

print("Created ORG_NAUTOBOT_DISCOVERY.md")
