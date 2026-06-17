# AI Enhancement Ideas — Network Tooling

> Purpose: practical, read-only AI ideas for each tool the team uses, grounded in
> live data I pulled. Each idea names **who it helps** so I can pair with that
> teammate, prototype, and demo. Theme: AI doesn't replace the tools — it reads
> their live data and turns noise into clear, actionable answers.

_Status: ideas only (not built yet). Plan: document → prototype → demo._

---

## How I'll roll this out (per teammate)

| Tool | Teammate to pair with | Their current work |
|---|---|---|
| Observium | On-call / NetOps | alert response, health |
| Nautobot | Melquis / "Mahesh" (Nautobot + D42 docs) | source-of-truth data quality |
| Zabbix | Francis (Arista EOS CVE remediation, site ops) | alerting, onboarding |
| Cacti | TechOps / whoever owns graphs | traffic graphs, weathermap |
| IPAM angle | David P (Meraki rollout, subnets) | IP/VLAN/subnet data |

Each one is a small, self-contained, read-only prototype → easy to show, hard to break.

---

## 1. Observium — "turn 92 alerts into 4 incidents"

**Live state (pulled today):** 590 devices, 566 up / 24 not-up, **92 active alerts**.
Two firewalls (`sv4fw03`, `sv5fw03`) generate **33 of the 92**. Several downs
cluster by site (COMMERCIAL: `comcsw01/02`, `com1030/1056/1080sw01`) and by purpose
(6 AWS staging FWs `usw2*-stg`).

| Idea | What AI does | Helps |
|---|---|---|
| **Alert triage + dedupe** | Collapse 33 firewall alerts into "2 FWs flapping BGP since X" | On-call |
| **Root-cause clustering** | Group the COMMERCIAL-site downs into 1 likely incident | NetOps |
| **Expected-vs-real filter** | Auto-label `*-stg` staging downs as expected; surface only real ones | Everyone |
| **Weekly AI health digest** | One readable summary → Slack/Confluence | Team + manager |
| **Plain-English query** | "down Arista in COMMERCIAL?" answered from live API | Non-experts |

**Recommended first prototype:** AI Alert Triage + Digest — "92 raw alerts → a handful of plain-English incidents." Read-only, reuses my Observium MCP.

---

## 2. Nautobot — "AI source-of-truth janitor"

**Live state:** 484 devices, but big documentation gaps — **only 4 cables** for
8,768 interfaces (≈ no device-to-device topology), 17/19 Junos missing
`software_version`, interface descriptions largely blank, IPAM nearly empty, the
Infoblox SSoT sync **disabled**.

| Idea | What AI does | Helps |
|---|---|---|
| **Data-quality scorecard** | AI scores each device's record (missing version/IP/serial/desc/cables) and explains *why each gap matters*, ranked | Melquis / docs owner |
| **Cross-source autofill drafts** | AI proposes field values from Observium/Cacti/live device, as a **reviewable diff** (never auto-writes) | Docs owner |
| **Topology inference** | AI reads LLDP/CDP neighbors + Cacti weathermap links and **proposes the missing cable/connection records** | Whoever maps DC |
| **Natural-language inventory** | "show MX204s in Foster City missing a mgmt IP" → GraphQL behind the scenes | Everyone |
| **Onboarding draft assistant** | New device → AI drafts the Nautobot fields + the right role/platform/site from naming conventions | NetOps |
| **D42 ↔ Nautobot diff** | AI reconciles the dual-documentation pain (D42 vs Nautobot) and lists conflicts | Melquis |

**Why strong:** builds directly on my existing audit/reconcile scripts; turns them
from one-off reports into an **ongoing AI quality assistant**.

---

## 3. Zabbix — "AI on-call copilot + onboarding"

**Live state:** Zabbix 7.2.15 reachable, but the **API token is expired/placeholder**
— authenticated reads need a refresh first (itself a quick win to flag). Alerts feed
Slack `#headsups-zapps`; onboarding is **manual** (Google sheet → create host → pick
SNMP template by device type).

| Idea | What AI does | Helps |
|---|---|---|
| **Alert summarizer / dedupe** | Same idea as Observium but for the Slack alert firehose; cluster + explain + suggest next step | On-call / Francis |
| **Nautobot → Zabbix onboarding bot** | AI reads Nautobot (platform + role) and **drafts** the Zabbix host + correct template (Arista/Fortinet/PAN/Cisco), replacing the Google-sheet step | Whoever onboards |
| **Coverage gap report** | AI joins Nautobot ↔ Zabbix: "documented but not monitored" and vice-versa | NetOps + manager |
| **CVE/version assist for Francis** | AI cross-refs running versions vs known-bad (his Arista EOS CVE work) and builds the remediation worklist | **Francis** (live ticket) |
| **Trigger explainer** | New/odd trigger fires → AI explains in plain English what it means and likely cause | Junior on-call |

**Quick win to mention:** "Zabbix API token needs refreshing — once done, all of the
above become possible; I can wire a read-only connector like I did for Observium/Cacti."

---

## 4. Cacti — "make the legacy graphs talk"

**Live state (via my guest connector):** 6 weathermaps, 1,837 graphs. No REST API —
guest web access works. Rich interface descriptions live on edge/WAN routers; manual
device onboarding; overlaps Observium/Grafana.

| Idea | What AI does | Helps |
|---|---|---|
| **Weathermap → plain-English status** | AI reads a weathermap and says "Sunnyvale: all links < 15% except suncsw01→spine at 60%" | NOC at a glance |
| **Graph-title → Nautobot descriptions** | AI mines the 1,837 graph titles for interface intent and proposes Nautobot description backfills (extends my Task 3) | Docs owner |
| **Capacity watch** | AI scans link utilization across maps and flags the few approaching saturation | Capacity planning |
| **Coverage gap** | "graphed in Cacti but missing from Nautobot" (already found 22) → onboarding list | NetOps |
| **Dashboard consolidation advisor** | AI maps which Cacti graphs duplicate Observium/Grafana → what can retire | Tooling owner |

**Why strong:** Cacti is legacy and a bit neglected — small AI touches here look
disproportionately impressive, and I already have the read-only connector.

---

## Cross-tool "big idea" (stretch, great story)

**One AI "Network Assistant" over all four tools.** Ask one question — "what's
wrong in COMMERCIAL right now?" — and it pulls Nautobot (what should be there),
Observium + Zabbix (what's down/alerting), and Cacti (link load), then answers in
plain English with sources. The per-tool MCP connectors I'm building are the
foundation for exactly this.

---

## My approach (and why it earns trust)

1. **Read-only, human-reviewed.** AI summarizes/triages/drafts — never writes to
   production. Every change is a proposed diff for a human.
2. **Grounded in real data**, not slideware — each idea above came from a live pull.
3. **Small, demoable units** per teammate → I get to pair with each person, learn
   their workflow, and ship something they actually use.

**Sequence:** Observium digest (fastest, most visible) → Nautobot quality assistant
(builds on my existing scripts) → Zabbix onboarding/CVE assist (pairs with Francis)
→ Cacti weathermap summarizer → optional unified assistant.
