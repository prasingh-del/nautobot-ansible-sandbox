# 1:1 Summary — Network Automation & Tooling (Intern)

_Prepared 2026-06-16. Focus areas: Nautobot (source of truth) + Ansible, tested against a Juniper MX204._

## TL;DR
Built a working **Nautobot → Ansible → Junos** pipeline in a local lab, then pointed the
same idea at our **real** data (read-only) to find and report data-quality gaps, and
validated it against a **live MX204**. Everything against production was read-only;
proposed fixes only, no changes made.

---

## What I delivered (all reproducible scripts + reports)

| # | Deliverable | What it does |
|---|---|---|
| 1 | `audit_junos.py` → `JUNOS_AUDIT.md` | Read-only audit of all Junos devices in Nautobot; flags missing fields |
| 2 | `reconcile_versions.py` → `VERSION_RECONCILE.md` / `.csv` | Cross-references Nautobot vs Observium to build a version backfill list |
| 3 | `playbook_mx204.yml` + `compare_mx204.py` → `MX204_VS_NAUTOBOT.md` | Ansible pulls live facts from a real MX204 (read-only) and compares to Nautobot |
| — | `WORK_PLAN_1on1.md`, `TEAM_MEMBERS.md` | Plan + teammate/contribution map |

## Key findings (real data)
- **17 of 19** Junos routers have **no software_version** in Nautobot.
- **139 / 139** interfaces have **blank descriptions**.
- **3** devices missing a management IP (`las1rt01`, `las1rt02`, `sv5rt01`); **1** missing serial.
- **Observium already has every router's OS version** → ready to backfill the 17 gaps
  (e.g. `fc01rt01` = 21.4R3.15). 0 conflicts where both systems had data.
- **22 Junos routers are monitored in Observium but appear missing from Nautobot**
  (whole sites: Atlanta, Austin, Dallas, Phoenix, LA, SFO) — a source-of-truth coverage gap.
- The **MX204 test device** (`TEST-JUNOS`, serial FG969, Junos 21.4R2-S1.4) is also **not in
  Nautobot** — same theme.

## Skills / tools demonstrated
- Nautobot REST + GraphQL APIs (read-only), Observium REST API.
- Built a read-only **Observium MCP** connector so the data is queryable.
- Cross-tool data reconciliation (join two systems on hostname).
- **Ansible** against a live Juniper router (read-only `show` + `cli_command`).
- Real troubleshooting: Juniper's `junos_facts` now needs NETCONF; worked around it with
  generic CLI collection over SSH.

## Safety posture (as a new intern)
- Production Nautobot and live devices: **read-only**.
- Fixes are produced as **proposed change lists** for review — nothing written to prod.
- Local Docker sandbox used for any write practice.

## How I can help the team (mapped to live tickets)
- **Francis** (switch CVE remediation, `ITOPS-34837/838` Arista EOS): generate current
  EOS-version lists from Observium to drive/verify remediation.
- **David P** (Meraki sensor rollout, `ITOPS-34415/34657`): read-only reports of available
  PoE switchports and subnet utilization from Nautobot.
- **Nautobot/D42 documentation effort**: my audit output is a ready "what's missing" worklist.

## Proposed next steps (with manager approval)
1. Extend the reconciliation to **Arista EOS** (211 devices) for Francis's security work.
2. Verify the **22 Observium-only routers** and onboard the genuinely missing ones.
3. With sign-off, apply the **software_version backfills** via a reviewed Nautobot job.
4. Re-auth the **Zabbix** API token for live alert visibility (token is currently a placeholder).
5. (Blocked by IT policy) email/Slack programmatic access — needs IT approval; using
   Zabbix/Slack-sanctioned routes instead.

## Open questions for you
- Am I cleared to **write** backfills to production Nautobot later, or keep proposing only?
- Is **Observium** the approved source to backfill `software_version`?
- Priorities: data-quality cleanup vs. supporting Francis's EOS remediation first?
