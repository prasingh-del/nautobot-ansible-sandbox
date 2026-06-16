# NetOps Team Members — Work & Contribution Map

> Reference notes on teammates and how my (intern) Nautobot+Ansible work can support them.
> Gathered from Jira (jira.zooxlabs.com) on 2026-06-15. Team: NetOps within IT.
> Projects this team uses: ITOPS (IT Operations), ITPROJ (IT Projects), LWCP
> (Light Weight Change Process / maintenance windows), ZPT (Zoox Progress Tracker).

---

## Confirmed teammates

### Francis Delrosario
- Jira: `francis` / `francis@zoox.com` (key x-fdelrosario@zoox.com)
- Focus: hands-on network operations + security remediation
- Recent / current work:
  - **Switch security remediation (new, Jun 2026):** ITOPS-34834 (OpenSSH < 9.8 RCE),
    ITOPS-34835 (OpenSSH < 10.3), ITOPS-34836 (TCP/IP blind reset DoS),
    ITOPS-34837 (**Arista EOS libresolv overflow RCE, SA0017**),
    ITOPS-34838 (**Arista EOS DNS heap overflow RCE, SA0030**)
  - EOS upgrade work: LWCP-1316 (Update EOS on lv03idf3s01)
  - Site connectivity / deploy "wall connection" problems (many ZPT tickets, Oak Grove SF)
  - MDF/IDF clean-up, remote-site spares inventory, Meraki wireless floorplans,
    switch replacements (LWCP-1248), Meraki MT-15 switchport ID (ITOPS-35082)
- **How I can help:** EOS/Junos version reporting feeds his remediation directly.
  Produce "current OS version vs fixed version" device lists (Observium has the
  versions; Nautobot is missing them).

### David Pasurishvili  ("David P")
- Jira: `dpasurishvili` / `dpasurishvili@zoox.com` (key JIRAUSER47726)
- Focus: Meraki environmental sensor rollout + IPAM/switchport provisioning
- Recent / current work:
  - ITOPS-34414 Create All Sites for Meraki MT-12 and MT-15 Deployment (Done)
  - ITOPS-34415 Identify and Provide PoE Switchports for Meraki MT-15 Sensors (On Hold)
  - ITOPS-34657 Create Subnet for Power and Enviro Devices at Oak Grove (New)
- **How I can help:** Read-only Nautobot reports of available/unused PoE switchports
  per MDF/IDF, and subnet/prefix utilization reports for the power/enviro subnets.

---

## Unconfirmed — "Mahesh"
- No Jira user matched `mahesh`. User skipped confirmation.
- Closest NetOps candidate: **Melquis Naveo** (`x-mnaveo` / x-mnaveo@zoox.com,
  key JIRAUSER55323). Does PDU/UPS work (LWCP-1291) AND is tasked in DCOps weekly
  notes with **documenting rooms/racks/PDUs in Nautobot + D42**.
- **How I can help (if Mahesh == Melquis):** my data-quality audit output is his
  "what's missing in Nautobot" worklist; extend audit to racks/PDUs/locations to
  track documentation completeness over time.
- TODO: confirm Mahesh's real full name / email.

---

## Other NetOps names seen (context, not asked about)
- Angelo Llanos (`angelo`, x-allanos) — PAPN firewall migrations, carrier/SIM changes (LWCP)
- Andy Deshmukh (`adeshmukh`) — Palo Alto / Panorama PAN-OS upgrades & firewall remediation
- Rahul Deshmukh (`rdeshmukh`) — ESXi network port config; also admin on legacy tools
  (Cacti/Observium/netops02 per Confluence)
- Namasivayagam Desikavinayagam (`ndesikavina`) — Panorama upgrades, cert renewals
- Aravind Reddy Kandi (`akandi`), Dale Kiefling (`dkiefling`, networking migrations),
  Alexander Kirby (`x-akirby`, DXGW→Terraform)

---

## Cross-cutting themes I noticed (automation opportunities)
- Lots of **manual, one-device-at-a-time switch maintenance** via LWCP change tickets
  (EOS upgrades, switch replacements) — candidates for Ansible-assisted workflows.
- **OS-version visibility gap**: security remediation (Francis) and upgrades depend on
  knowing current versions, which Nautobot doesn't track but Observium does.
- **Nautobot/D42 dual documentation** is an ongoing manual effort (DCOps weekly notes).

## My safe contribution posture (intern)
Read-only reports and propose-only change lists. No writes to production Nautobot
or live devices without manager sign-off. Sandbox (localhost:8080) is fine for practice.
