# Task 2 — Software Version Reconciliation (Nautobot vs Observium)

**Goal:** Fill the empty `software_version` gaps from Task 1 using a system that
already knows the answer — **Observium** (live monitoring).

## What it does
`reconcile_versions.py` joins, on hostname:
- Nautobot Junos devices (the source of truth)
- Observium devices (which OS version each is actually running)

and classifies each device:

| Action | Meaning |
|---|---|
| `BACKFILL` | Nautobot empty, Observium has it → propose adding |
| `MATCH` | Both agree |
| `MISMATCH` | Both set but differ → investigate |
| `NOT_IN_OBSERVIUM` | No Observium match to source from |

It also lists **Junos devices Observium monitors that Nautobot is missing**.

## Run
```bash
python3 reconcile_versions.py
```

## Inputs / Outputs
- **Reads:** Nautobot GraphQL + Observium REST API (creds from `.env.local`).
- **Writes:**
  - `VERSION_RECONCILE.md` — full report
  - `VERSION_RECONCILE.csv` — proposed changes only (`BACKFILL` + `MISMATCH`)

## Key findings
- **17 BACKFILL**, 2 MATCH, **0 MISMATCH** — Observium can fill every gap, no conflicts.
- **22 Junos routers** are in Observium but **missing from Nautobot**.

> Read-only on both systems. The CSV is a *proposed* change list for review —
> nothing is written to production.
