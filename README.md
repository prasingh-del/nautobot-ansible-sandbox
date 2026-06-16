# Nautobot + Ansible — Network Tooling (Intern Work)

Read-only tooling that uses **Nautobot** (source of truth) together with
**Observium** and **Cacti** (live monitoring) to find and report network
data-quality gaps, plus an Ansible workflow validated against a live Juniper
MX204. Everything against production is **read-only / propose-only** — no
changes are written to production systems.

## Repository layout

```
.
├── KT/                     Knowledge & reference notes (for understanding)
│   ├── LEARNING_LOG.md         step-by-step build log of the local sandbox
│   ├── ZOOX_TOOLING_KNOWLEDGE.md  Nautobot/Zabbix/Observium/Cacti/Grafana notes
│   ├── TEAM_MEMBERS.md         teammates + live tickets mapping
│   └── ORG_NAUTOBOT_DISCOVERY.md  inventory dump of the org's Nautobot
│
├── docs/                   Manager-facing write-ups
│   ├── WORK_PLAN_1on1.md       the plan + what was built
│   └── ONE_ON_ONE_SUMMARY.md   1:1 summary of deliverables & findings
│
├── mcp/                    Read-only MCP connectors (registered in ~/.cursor/mcp.json)
│   ├── observium_mcp.py        Observium REST API
│   └── cacti_mcp.py            Cacti (guest Weathermap + graphs; no API at Zoox)
│
├── tasks/                  The actual work — each task is self-contained (code + report)
│   ├── 0_discovery/            discover_nautobot.py  (generates the KT inventory)
│   ├── 1_junos_audit/          audit_junos.py        → JUNOS_AUDIT.md
│   ├── 2_version_reconcile/    reconcile_versions.py → VERSION_RECONCILE.md/.csv
│   ├── 3_cacti_reconcile/      reconcile_cacti.py    → CACTI_VS_NAUTOBOT.md + .csv
│   └── 4_mx204_live/           playbook_mx204.yml + compare_mx204.py → MX204_VS_NAUTOBOT.md
│
└── sandbox/                Original local proof-of-concept (Docker Nautobot → Ansible → Junos)
    ├── docker-compose.yml, setup_mock_data.py, playbook.yml, inventory.yml, templates/
    └── ansible.cfg
```

## Key findings (read-only, from production)

- **17 / 19** Junos routers in Nautobot have **no `software_version`**.
- **All** sampled Junos interface descriptions are **blank**.
- **Observium** already knows every router's OS version → ready backfill list.
- **22 routers** are monitored in **Observium *and* Cacti** but are **missing
  from Nautobot** (independent cross-validation of the same coverage gap).
- The live **MX204** (`TEST-JUNOS`, Junos `21.4R2-S1.4`) is also not in Nautobot.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.local.example .env.local   # then fill in tokens/creds (gitignored)
```

Secrets live in `.env.local` at the repo root (gitignored). Every script
searches upward for it, so they work from any subfolder.

## Running the tasks (all read-only)

```bash
python3 tasks/1_junos_audit/audit_junos.py
python3 tasks/2_version_reconcile/reconcile_versions.py
python3 tasks/3_cacti_reconcile/reconcile_cacti.py

# Live MX204 (needs VPN + device reachability):
cd tasks/4_mx204_live && ansible-playbook playbook_mx204.yml && python3 compare_mx204.py
```

Each script writes its report next to itself, inside its task folder.

## Safety posture

Production Nautobot and live devices are **read-only**. Fixes are produced as
**proposed change lists** (CSV/Markdown) for review — nothing is written to
production. Write practice happens only in the local `sandbox/`.
