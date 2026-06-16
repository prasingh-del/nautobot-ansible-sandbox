# Junos Data-Quality Audit (Nautobot, read-only)

- Source: `https://nautobot.zooxlabs.com` (GraphQL, read-only)
- Junos devices audited: **19**

## Summary of gaps

| Gap | Devices affected |
| --- | --- |
| Missing `software_version` | 17 / 19 |
| Missing `primary_ip4` (mgmt IP) | 3 / 19 |
| Missing `serial` | 1 / 19 |
| Interface inventory mgmt-only | 8 / 19 |
| Blank interface descriptions | 139 / 139 interfaces |

## Per-device detail

| Device | Model | Version | Mgmt IP | Serial | Ifaces | Blank desc | Flags |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clart01 | MX204 | — | 172.17.47.4/24 | HA120 | 1 | 1 | no-version, mgmt-only-ifaces, all-desc-blank |
| clart02 | MX204 | — | 172.17.47.5/24 | HA156 | 1 | 1 | no-version, mgmt-only-ifaces, all-desc-blank |
| fc01rt01 | MX204 | — | 10.252.2.9/28 | FQ110 | 13 | 13 | no-version, all-desc-blank |
| fc01rt02 | MX204 | — | 10.252.2.10/28 | BB681 | 13 | 13 | no-version, all-desc-blank |
| fc01rt03 | MX204 | — | 10.252.2.13/28 | FG964 | 13 | 13 | no-version, all-desc-blank |
| fc01rt04 | MX204 | — | 10.252.2.14/28 | FG916 | 13 | 13 | no-version, all-desc-blank |
| fc01rt05 | MX204 | — | 10.252.2.87/28 | FC181 | 13 | 13 | no-version, all-desc-blank |
| fc02rt01 | MX204 | — | 172.16.80.18/24 | FM279 | 13 | 13 | no-version, all-desc-blank |
| fc02rt02 | MX204 | — | 172.16.168.227/23 | FM288 | 13 | 13 | no-version, all-desc-blank |
| las1rt01 | MX304 | — | — | GQ188 | 0 | 0 | no-version, no-mgmt-ip |
| las1rt02 | MX304 | — | — | — | 1 | 1 | no-version, no-mgmt-ip, no-serial, mgmt-only-ifaces, all-desc-blank |
| mi1rt01 | PTX10001-36MR | 23.4R1.10-EVO | 10.100.168.181/25 | HG220 | 1 | 1 | mgmt-only-ifaces, all-desc-blank |
| mi1rt02 | PTX10001-36MR | 23.4R1.10-EVO | 10.100.168.182/25 | HG042 | 1 | 1 | mgmt-only-ifaces, all-desc-blank |
| sf02rt01 | MX204 | — | 172.16.140.21/24 | FM277 | 13 | 13 | no-version, all-desc-blank |
| sf02rt02 | MX204 | — | 172.16.140.22/24 | FM650 | 13 | 13 | no-version, all-desc-blank |
| sunrt01 | MX304 | — | 10.252.2.71/28 | GR088 | 1 | 1 | no-version, mgmt-only-ifaces, all-desc-blank |
| sunrt02 | MX304 | — | 10.252.2.72/28 | GQ187 | 1 | 1 | no-version, mgmt-only-ifaces, all-desc-blank |
| sunrt03 | MX204 | — | 10.252.2.20/28 | FM293 | 13 | 13 | no-version, all-desc-blank |
| sv5rt01 | MX10003-PREMIUM | — | — | JN5E49045JCB | 2 | 2 | no-version, no-mgmt-ip, mgmt-only-ifaces, all-desc-blank |

## Suggested priorities (propose-only — no writes made)

1. Backfill `software_version` (Observium already has these — see Task 2).
2. Add management IPs for devices flagged `no-mgmt-ip` (needed for automation).
3. Complete interface inventory for `mgmt-only-ifaces` devices.
4. Add interface descriptions (intent) for key uplinks.
