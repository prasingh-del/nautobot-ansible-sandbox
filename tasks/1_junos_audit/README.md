# Task 1 — Junos Data-Quality Audit

**Goal:** Find where Nautobot's record for Juniper/Junos devices is incomplete.

## What it does
`audit_junos.py` asks Nautobot's GraphQL API for every `juniper_junos` device and
flags missing/empty important fields:
- `software_version`
- `primary_ip4` (management IP)
- `serial`
- interface inventory that is **management-only** (real uplinks not modeled)
- **blank interface descriptions**

It writes a human-readable report, sorted so the worst offenders are first.

## Run
```bash
python3 audit_junos.py
```
(`.env.local` at the repo root is found automatically.)

## Inputs / Outputs
- **Reads:** Nautobot GraphQL (`NAUTOBOT_URL`, `NAUTOBOT_TOKEN`).
- **Writes:** `JUNOS_AUDIT.md` (in this folder).

## Key findings
- **17 / 19** Junos devices have **no `software_version`**.
- **139 / 139** sampled interface descriptions are **blank**.
- **3** devices missing a management IP; **1** missing a serial.

## Where the fix comes from
Task 2 shows Observium already knows the missing versions → ready backfill list.

> Read-only. Nothing is written to Nautobot.
