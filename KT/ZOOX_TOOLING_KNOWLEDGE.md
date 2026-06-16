# Zoox Network Tooling — Knowledge Base

> Gathered 2026-06-10 from live MCP access (Nautobot, Zabbix) and Confluence (ITINT/ITHM spaces).
> Purpose: reference for finding things to fix/improve as a new network automation intern.

---

## 1. Nautobot — Source of Truth (SoT)

- **URL:** https://nautobot.zooxlabs.com | **Access: WORKING (full API via MCP)**
- **What it does:** Database of what the network *should* be — devices, locations, racks, IPs, VLANs, circuits. Ansible/automation reads inventory from it.
- **Version:** 2.4.9 (Django 4.2.21, Python 3.10.12), 1 celery worker on `sun-netops02`

### Current data (as of 2026-06-10)
| Object | Count |
|---|---|
| Devices | 484 |
| Interfaces | 8,768 |
| Locations | 88 (Region → Site → Room hierarchy) |
| Racks | 47 |
| Circuits | 77 |
| Prefixes | 12 (rooted at 10.0.0.0/8) |
| IP addresses | 226 |
| VLANs | 6 |
| Cables | 4 |
| Tenants | 0 |
| Git repositories | 0 |

### Platforms (network OS → device counts)
- `arista_eos` — 211 (dominant; switches; ansible driver `arista.eos.eos`)
- `fortinet` — 23 (firewalls), `juniper_junos` — 19 (routers), `paloalto_panos` — 12 (firewalls)
- `cisco_xe` — 11, `cisco_ios` — 1, `opengear` — 1 (console server)

### Device roles
`asw` (access switch), `csw` (core switch), `leaf`, `spine`, `router`, `firewall`, `oob` (console),
`its`, `dwdm`, `pop_msw`, `pop_pdu`, `travel router`, plus physical: PDU, UPS, Patch Panel, Cable Manager.

### Sites
Foster City campus (FC01–FC07 + Bayside, MDF/IDF rooms), Tracy (AR01), Austin (AUS01/AUS11),
Boston (BO01), Dallas (DA11), Atlanta (ATL14), LA (LA1), Fremont (FK01), Hayward (CLA),
San Carlos (COM), Adelanto (Karco), Atwater, East Liberty OH.

### Plugins installed
- `nautobot_device_onboarding` 4.2.5 — jobs "Sync Devices From Network" + "Sync Network Data From Network" are **enabled**
- `nautobot_ssot` 3.8.1 — Infoblox DDI integration exists but **disabled** (both directions)
- `nautobot_plugin_nornir` 2.2.1, `nautobot_secrets_providers` 3.2.0, `nautobot_bgp_models` 2.3.1

### Tags
`campus`, `mfg`, `office`, `pop`, `SSoT Synced from/to Infoblox`

### Custom fields on devices
`last_network_data_sync` (null on sampled devices — sync may not be running regularly)

### Observed gaps / improvement candidates
- **IPAM is nearly empty** (12 prefixes, 226 IPs, 6 VLANs for 484 devices) — Infoblox is likely the real IPAM; the SSoT Infoblox sync jobs are disabled. Big opportunity: enable/fix the sync.
- **Only 4 cables** documented for 8,768 interfaces — no cable/topology documentation.
- **Zero tenants, zero git repositories** — no config contexts/golden config from Git.
- Recent job results (130 total) are mostly manual "Bulk Delete Objects" — onboarding sync jobs don't appear scheduled.
- Many devices missing `primary_ip4` and `platform` (sampled: AR01CM01 had neither).
- Sample device had empty `serial` — asset data incomplete.
- Nautobot vs Device42 (D42) dual-documentation appears in DCOps meeting notes — data consistency is an ongoing pain point.

---

## 2. Zabbix — Alerting & Monitoring (the "is it broken?" tool)

- **URL:** https://zabbix.zooxlabs.com | **Access: MCP exists but session auth EXPIRED** ("Session terminated, re-login") — only unauthenticated `apiinfo.version` works. Needs MCP credential refresh.
- **Server version:** 7.2.15
- **What it does:** Polls devices (SNMP/agent/ping), evaluates triggers, sends alerts to Slack.
  - Network alerts → tag `slack = headsup-network`
  - Production alerts feed **#headsups-zapps** Slack channel
- **HA setup (FC Zabbix):** `zbxha01-mst-usw2a-p.fc.zooxlabs.com` / `zbxha02-mst-usw2b-p.fc.zooxlabs.com` (AWS, monitors Vegas/sunset/fusion + EC2); MySQL primary `sun-zbxdb01-prod` with replica (Percona Xtrabackup restore runbook exists).

### Onboarding workflow (Confluence "Network Monitoring" page 165124519)
1. Add device to a **Google tracking sheet** first (manual!)
2. Create host at zabbix.zooxlabs.com/hosts.php, groups: `Network Devices` + `Network devices/<site>`
3. SNMP interface w/ DNS name (SNMP must be enabled on device)
4. Template by device type:
   - ITS/Core: `Template Net Arista SNMPv2` (all interfaces)
   - Arista access: `Zoox Template Net Arista 48Port/96Port SNMPv2` (uplinks only)
   - Fortinet: `Template SNMP Fortinet`; Palo Alto: `Template Palo Alto`
   - Cisco: `Template Net Cisco IOS SNMPv2 10GbE`
   - APs: `Template module ICMP Ping` (ping only); Opengear: `Template App SSH service`
5. Tag `slack=headsup-network`, set SNMP macros
- Key docs: "Zabbix System Onboarding Process" (484521378), "Zabbix Monitoring" (460123820), "Zabbix Discovery and Health Checks" (528657567 — Salt deploys custom external scripts)

### Improvement candidates
- Onboarding is fully **manual + Google-sheet tracked** → classic automation target: sync hosts from Nautobot into Zabbix (Nautobot SoT → Zabbix host.create API).
- MCP/API session expired → fix token handling.
- APs are ping-only monitored.

---

## 3. Cacti — Graphing & Weathermap (legacy)

- **URL:** https://cacti.zooxlabs.com | **No direct API access** (UI + SSH only)
- **Host:** ubuntu@ip-10-4-255-155 (AWS)
- **What it does:** SNMP polling → RRD time-series **traffic graphs** per interface. Its main value at Zoox is the **Weathermap plugin** — a visual network map with live link utilization (referenced on "Network & Security (Firewalls)" page).
- **Owners (historical):** Devon (UI), Rahul (admin). "If you have admin to Cacti, you have admin to Weathermap." No creds tied to service.
- **Adding devices:** UI → Console → Management → Devices → + → hostname, SNMP creds, device template (Confluence 504242336).
- **Improvement candidates:** legacy tool, manual device adds, overlaps with Observium/Grafana. Device list could be auto-synced from Nautobot, or the weathermap could be regenerated from Nautobot data.

---

## 4. Observium — Auto-discovery Health Monitoring

- **Host:** `sun-observium01-p` (on-prem server), web UI requires account (request via ITHelp Jira portal 302)
- **No API access from here** — adds are done by SSH-ing into the server.
- **What it does:** SNMP-based health, link utilization, port/MAC inventory. Auto-discovers interfaces once device is added. TechOps uses it for **MAC→port mapping** during desk audits.
- **Adding devices:** ssh to server → `/opt/observium` → `sudo ./add_device.php <hostname>` (needs fping reachability + SNMP community working). Doc: 338241015.
- **Disabling alerts:** device Properties → skip ping / device ignore / disable. Doc: 347611152.
- **Note:** Site pages (Austin, San Diego, Oakgrove, TRC CA, Lincoln Center…) track per-site "monitored in Zabbix + Observium" checklists — coverage is manually tracked per site.
- **Improvement candidates:** same as Cacti — manual onboarding, could be driven from Nautobot; monitoring coverage tracking is manual Confluence tables.

---

## 5. Grafana — Dashboards

- **What it does:** Visualization layer that queries data sources (Prometheus/InfluxDB/Graphite/CloudWatch/etc.). Doesn't poll devices itself.
- **At Zoox:** Both self-hosted legacy (owner: Fermin, per NetOps Tools page; tutorial in Google Doc) and **Grafana Cloud** (INFRA team) — uses PDC (Private Data Source Connect) agent in the Observability AWS account to reach private data sources, incl. CloudWatch via AWS Monitoring account (Confluence 520271580).
- Nautobot exposes `django_prometheus` metrics — could feed Grafana.
- **Improvement candidates:** network team's graphs live in Cacti/Observium, not Grafana — opportunity to consolidate dashboards (e.g., SNMP → Prometheus snmp_exporter → Grafana, inventory-driven by Nautobot).

---

## Other tools discovered (NetOps Tools page 157124922)

- **Rancid** — config backup of network devices (root access: Rahul)
- **Ntopng** — flow analysis (DX links, internet, IX peering, T-Mobile PNIs, SUNDC, PAN FWs); http://ntopng.zooxlabs.com:3000/; creds in zvault (`networks/kv/Network Devices/ntopng`)
- **IP/MAC search tool + BGP alerting scripts** — cron jobs on `sun-netops02` (same box as Nautobot celery worker!); run under a personal account (`monitorBGP.py` under Varsha's account) — fragile, prime cleanup candidate
- **Device42 (D42)** — separate DC infrastructure DB, double-entry alongside Nautobot
- **zvault** — Vault instance for secrets: https://zvault.zooxlabs.com
- **Salt** — used to deploy Zabbix external scripts

## The big picture / where the intern can add value

```
            should-be state                         actual state
  ┌──────────┐   inventory   ┌─────────┐   SNMP/ping   ┌────────────────┐
  │ Nautobot ├──────────────►│ Ansible │               │ Zabbix (alerts)│
  │  (SoT)   │  (not wired   └─────────┘               │ Observium      │
  └────┬─────┘   to monitoring yet)                    │ Cacti+Weathermap│
       │  SSoT plugin (disabled)                       └────────────────┘
       ▼                                                manual onboarding,
   Infoblox (DNS/IPAM)                                  Google-sheet tracking
```

Recurring theme: **Nautobot is the source of truth, but nothing downstream is fed from it automatically.**
Devices are added by hand to Zabbix (+ Google sheet), Observium (SSH script), Cacti (UI), and D42.
Highest-leverage intern projects:
1. Nautobot → Zabbix host sync (API both sides; templates map cleanly from platform+role)
2. Nautobot → Observium add_device automation
3. Enable/validate Infoblox SSoT sync to populate IPAM
4. Populate missing data: primary IPs, platforms, serials, cables
5. Replace per-site Confluence "monitoring coverage" tables with a Nautobot-driven report
6. Move cron scripts on sun-netops02 (BGP monitor, MAC lookup) out of personal accounts into proper automation (Nautobot Jobs)

## Key Confluence pages
- NetOps Tools: pageId=157124922 | Network Monitoring (Zabbix onboarding): 165124519
- Zabbix System Onboarding: 484521378 | Zabbix Discovery & Health Checks: 528657567
- Adding Devices to Cacti: 504242336 | Adding Devices to Observium: 338241015
- Disabling Observium alerts: 347611152 | Grafana Cloud PDC: 520271580
- MDF/IDF Sites Index: 460122288 | Network & Security (Firewalls): 504507963
