# Task 3 — Cacti Reconciliation (Nautobot vs Cacti)

**Goal:** Use **Cacti** (graphing / weathermap) as a third "actual state" source
to find devices and interface labels Nautobot is missing.

## What it does
Cacti has **no REST API** at Zoox, so this reuses the read-only **guest** web
client from `mcp/cacti_mcp.py` (Weathermap gallery + Graphs list — no Console
password needed). `reconcile_cacti.py` then:
1. Collects device hostnames Cacti graphs/maps.
2. Compares them to Nautobot's device list (coverage gap).
3. Parses graph titles for human-meaningful interface labels and proposes
   description backfills where Nautobot's description is blank.

## Run
```bash
python3 reconcile_cacti.py
```
(Imports `cacti_mcp` from `../../mcp/` automatically.)

## Inputs / Outputs
- **Reads:** Nautobot GraphQL + Cacti guest web UI (`CACTI_*` in `.env.local`).
- **Writes:**
  - `CACTI_VS_NAUTOBOT.md` — report (coverage gap + bonus descriptions + caveats)
  - `CACTI_IFACE_BACKFILL.csv` — machine-readable proposed changes

## Key findings
- **22 devices** are graphed in Cacti but **missing from Nautobot** — strongly
  overlaps the Task 2 Observium-only list (independent cross-validation).
- Junos devices already in Nautobot use a `HOST - Traffic - <iface>` graph naming
  with **no per-interface description**, so 0 direct backfills (honest, not a bug).
- The rich interface descriptions live on **edge/WAN routers** (`sv4rt02`,
  `sv5rt02`) that aren't in Nautobot — captured as a ready-made onboarding sheet.

## Caveat
Cacti's list view **truncates long titles (~40 chars)**, so some descriptions are
cut off. Full text is on each graph's edit page if needed.

> Read-only on both systems. Nothing is written to production.
