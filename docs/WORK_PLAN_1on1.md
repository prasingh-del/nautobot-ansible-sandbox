# Work Plan — Nautobot + Ansible (Intern) — for 1:1

> Goal: legit, beginner-friendly work I can complete in a day and explain to my manager.
> Focus: Nautobot (source of truth) + Ansible automation, tested against a Juniper MX204.
> Golden rule: **Production Nautobot and live devices are READ-ONLY.** I only *write* in my
> local sandbox. Against the real network I produce **reports and proposed changes**, never edits.

---

## Part A — What I already built (my last ~2 weeks story)

A working local proof-of-concept that demonstrates the whole idea end to end:

```
Nautobot (source of truth)  ->  Ansible (uri lookup)  ->  Jinja2 template  ->  Junos config
```

- Local Nautobot in Docker (`docker-compose.yml`), populated via `setup_mock_data.py`.
- `playbook.yml` pulls interface + IP data for a mock MX204 (`fc01rt01`) and renders
  `compiled_config.txt` using `templates/junos_interface.j2`.
- Documented every step in `LEARNING_LOG.md`.

**One-line pitch to manager:** "I built a working Nautobot→Ansible→Junos pipeline in a local
lab, and this week I'm pointing the same idea at our real data (read-only) to find and report
data-quality gaps, and testing it against the MX204."

---

## Part B — What I found in the REAL tools (evidence, gathered today)

Pulled live from production Nautobot (read-only), Observium, and Confluence.

### Juniper/Junos fleet (19 Junos devices in Nautobot, 12 are MX204)
| Gap | Finding | Why it matters |
|---|---|---|
| `software_version` empty | **17 of 19** Junos devices have NO software version in Nautobot (only `mi1rt01/02` set) | Can't track OS compliance / EOL from the source of truth |
| Interface descriptions | **Every** interface description is blank ("") | No documented intent for what each link connects to |
| Missing `primary_ip4` | `las1rt01`, `las1rt02`, `sv5rt01` | Automation can't reach a device with no management IP |
| Missing `serial` | `las1rt02` | Asset tracking gap |
| Incomplete interfaces | Many devices only have `fxp0.0` modeled (mgmt only), while `fc01rt01` has full `et-`/`xe-` ports | Interface inventory is partial |

### Cross-tool gold: Observium already knows the versions Nautobot is missing
Observium has **27 Junos devices, all up**, each with its real OS version, e.g.:
- `fc01rt01` = `21.4R3.15`, `sunrt03` = `22.4R2-S1.6`, `clart01` = `22.4R3-S3.3`, `fk01rt01` = `24.4R2-S2.5`

So Observium is a ready data source to **fill the empty `software_version` field in Nautobot**.

---

## Part C — Today's plan (4 tasks, each self-contained)

Each task lists: **What / Why / How / Deliverable / Safety.**

### Task 1 — Nautobot Junos data-quality audit (READ-ONLY)
- **What:** A Python script that reads all Junos devices from Nautobot and produces a report of
  the gaps in Part B (missing version, blank descriptions, missing IP/serial).
- **Why:** Turns "the data is messy" into a concrete, prioritized list — exactly the kind of
  cleanup an intern owns. Builds on my existing `discover_nautobot.py`.
- **How:** Reuse the read-only pattern (requests + token) to call the Nautobot REST API,
  count gaps, write Markdown.
- **Deliverable:** `JUNOS_AUDIT.md` (a table the manager can read in 10 seconds).
- **Safety:** Read-only GET calls only.

### Task 2 — Observium ↔ Nautobot version reconciliation (READ-ONLY)
- **What:** Compare each Junos device's `software_version` in Nautobot against the version
  Observium reports, and list the mismatches/missing.
- **Why:** Demonstrates cross-tool thinking and produces a real "proposed change" list:
  "set these 17 versions in Nautobot." High-value, low-risk.
- **How:** Read Nautobot versions + Observium versions, join on hostname, output differences.
- **Deliverable:** `VERSION_RECONCILE.md` / `.csv`.
- **Safety:** Read-only on both systems. We do NOT write to prod; we hand the manager the list.

### Task 3 — MX204 hands-on via Ansible (READ-ONLY against the test device)
- **What:** Use Ansible's Juniper modules to gather facts from my MX204 test device and run
  safe `show` commands (version, interface descriptions), then compare to Nautobot.
- **Why:** Proves I can drive a real router with Ansible and validate SoT vs reality
  (does Nautobot's serial/model/version match the actual box?).
- **How:** `junipernetworks.junos` collection; `junos_facts` + `junos_command`. No config push.
- **Deliverable:** `mx204_facts.json` + a short `MX204_VS_NAUTOBOT.md` comparison.
- **Safety:** Only `get`/`show` (operational) commands. Zero configuration changes.
- **Needs from me:** MX204 hostname/IP + login (placed in `.env.local`, not in chat).

### Task 4 — Stretch (WRITE, but only in my LOCAL sandbox)
- **What:** In the local Docker Nautobot, write back the fixes (set software_version + an
  interface description on `fc01rt01`), then re-run `playbook.yml` to show the richer config.
- **Why:** Shows the complete loop: detect gap → fix in SoT → automation reflects it.
- **Deliverable:** Updated `compiled_config.txt` with a real description + version note.
- **Safety:** Local sandbox only (localhost:8080). Never production.

---

## Part D — How I'll present it in the 1:1
1. "Here's the pipeline I built (demo `compiled_config.txt`)."
2. "Here's what I found in the real data" → show `JUNOS_AUDIT.md`.
3. "Here's a ready-to-apply fix list using Observium as the source" → `VERSION_RECONCILE.md`.
4. "Here's me validating against the real MX204" → `MX204_VS_NAUTOBOT.md`.
5. "Next, with your approval, I can propose writing these fixes into Nautobot via a reviewed job."

---

## Part E — Understanding checkpoints (what success looks like)
- I can explain **why Nautobot is the source of truth** and what "intended vs actual" means.
- I can read the Nautobot REST API and explain one GET call.
- I can explain what `junos_facts` returns and why read-only is safe.
- End state today: 3 short reports + 1 sandbox demo, all reproducible by re-running scripts.

## Open questions for my manager / to confirm
1. Am I allowed to write to **production** Nautobot later, or only propose changes? (Assuming propose-only for now.)
2. MX204 test device: hostname/IP + which auth (SSH password or key)?
3. Is Observium an approved source to backfill `software_version`, or is there another system of record?
