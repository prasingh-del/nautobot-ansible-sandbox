# Task 0 — Nautobot Discovery

**Goal:** Get a first, full picture of what already lives in the org's production
Nautobot, so later tasks know what to audit.

## What it does
`discover_nautobot.py` walks Nautobot's REST API (read-only) and dumps an
inventory summary: device counts, platforms, roles, sites, racks, circuits, etc.
The output became the reference doc `KT/ORG_NAUTOBOT_DISCOVERY.md`.

## Run
```bash
set -a && . ../../.env.local && set +a   # load NAUTOBOT_URL / NAUTOBOT_TOKEN
python3 discover_nautobot.py
```

## Inputs / Outputs
- **Reads:** Nautobot REST API (`NAUTOBOT_URL`, `NAUTOBOT_TOKEN`).
- **Writes:** prints a report (saved as `KT/ORG_NAUTOBOT_DISCOVERY.md`).

## Why it matters
This is the "what do we have?" baseline. It's how I learned the fleet is
Arista-heavy (211), with 19 Junos routers, 484 devices total — the starting
point for every data-quality task that follows.

> Read-only. Nothing is written to Nautobot.
