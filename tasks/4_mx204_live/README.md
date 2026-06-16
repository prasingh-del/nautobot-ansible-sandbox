# Task 4 — Live MX204 vs Nautobot

**Goal:** Prove the end-to-end Ansible workflow against a **real** Juniper MX204,
read-only, and compare what the box actually reports to Nautobot.

## What it does
1. `playbook_mx204.yml` SSHes into the MX204 (over `network_cli`, no NETCONF) and
   runs read-only `show` commands, saving each to `mx204_output/`:
   - `show version`, `show chassis hardware`, `show interfaces terse`,
     `show configuration interfaces | display set`
2. `compare_mx204.py` parses those outputs (model, serial, OS version, interfaces)
   and compares against the matching Nautobot device, writing a diff report.

## Run
```bash
# from this folder (its ansible.cfg points at inventory_mx204.yml):
set -a && . ../../.env.local && set +a      # MX204_HOST / USER / PASSWORD
ansible-playbook playbook_mx204.yml          # needs VPN + device reachability
python3 compare_mx204.py
```

## Inputs / Outputs
- **Reads:** the live MX204 (SSH) + Nautobot GraphQL.
- **Writes:**
  - `mx204_output/*.txt` — raw show-command output (gitignored; may contain serials)
  - `MX204_VS_NAUTOBOT.md` — the comparison report

## Notes
- The test box reports hostname `TEST-JUNOS` (serial `FG969`, Junos `21.4R2-S1.4`).
- Nautobot has **no** `test-junos` record — expected, it's a lab device not in
  production. Set `MX204_NAUTOBOT_NAME` in `.env.local` to compare against a
  specific production device name instead.
- `junos_facts` needs NETCONF; this playbook deliberately uses generic
  `cli_command` over SSH so it works with plain SSH access.

## Why two layers
This is the **one-device deep dive** (SSH). The fleet-wide gaps in Tasks 1–3 come
from **reading APIs**, not logging into every device.

> Read-only: only `show` commands are run. No device or Nautobot changes.
