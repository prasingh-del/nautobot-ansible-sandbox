# Junos OS Version Reconciliation: Nautobot vs Observium

Read-only comparison. No changes were made to either system.

- Nautobot Junos devices: **19**
- Observium devices indexed: **590**

## Outcome counts

| Action | Meaning | Count |
| --- | --- | --- |
| BACKFILL | Nautobot empty, Observium has version → propose adding | 17 |
| MATCH | Already agree | 2 |
| MISMATCH | Both set but differ → investigate | 0 |
| NOT_IN_OBSERVIUM | No Observium match to source from | 0 |

## Proposed backfills / mismatches (the action list)

| Device | Nautobot | Observium | Action |
| --- | --- | --- | --- |
| clart01 | — | 22.4R3-S3.3 | BACKFILL |
| clart02 | — | 22.4R3-S3.3 | BACKFILL |
| fc01rt01 | — | 21.4R3.15 | BACKFILL |
| fc01rt02 | — | 21.4R3.15 | BACKFILL |
| fc01rt03 | — | 21.4R3.15 | BACKFILL |
| fc01rt04 | — | 21.4R3.15 | BACKFILL |
| fc01rt05 | — | 20.4R3-S3.4 | BACKFILL |
| fc02rt01 | — | 21.4R3-S2.3 | BACKFILL |
| fc02rt02 | — | 21.4R3-S2.3 | BACKFILL |
| las1rt01 | — | 22.2R3-S1.9 | BACKFILL |
| las1rt02 | — | 22.2R3-S1.9 | BACKFILL |
| sf02rt01 | — | 21.4R3-S2.3 | BACKFILL |
| sf02rt02 | — | 21.4R3-S2.3 | BACKFILL |
| sunrt01 | — | 22.2R3-S2.8 | BACKFILL |
| sunrt02 | — | 22.2R3-S2.8 | BACKFILL |
| sunrt03 | — | 22.4R2-S1.6 | BACKFILL |
| sv5rt01 | — | 21.4R3-S1.5 | BACKFILL |

## Full comparison

| Device | Nautobot | Observium | Action |
| --- | --- | --- | --- |
| clart01 | — | 22.4R3-S3.3 | BACKFILL |
| clart02 | — | 22.4R3-S3.3 | BACKFILL |
| fc01rt01 | — | 21.4R3.15 | BACKFILL |
| fc01rt02 | — | 21.4R3.15 | BACKFILL |
| fc01rt03 | — | 21.4R3.15 | BACKFILL |
| fc01rt04 | — | 21.4R3.15 | BACKFILL |
| fc01rt05 | — | 20.4R3-S3.4 | BACKFILL |
| fc02rt01 | — | 21.4R3-S2.3 | BACKFILL |
| fc02rt02 | — | 21.4R3-S2.3 | BACKFILL |
| las1rt01 | — | 22.2R3-S1.9 | BACKFILL |
| las1rt02 | — | 22.2R3-S1.9 | BACKFILL |
| mi1rt01 | 23.4R1.10-EVO | 23.4R1.10-EVO | MATCH |
| mi1rt02 | 23.4R1.10-EVO | 23.4R1.10-EVO | MATCH |
| sf02rt01 | — | 21.4R3-S2.3 | BACKFILL |
| sf02rt02 | — | 21.4R3-S2.3 | BACKFILL |
| sunrt01 | — | 22.2R3-S2.8 | BACKFILL |
| sunrt02 | — | 22.2R3-S2.8 | BACKFILL |
| sunrt03 | — | 22.4R2-S1.6 | BACKFILL |
| sv5rt01 | — | 21.4R3-S1.5 | BACKFILL |

## Bonus: Junos devices in Observium but NOT in Nautobot

These are monitored but missing from the source of truth.

| Observium hostname | Version | Status |
| --- | --- | --- |
| atl14rt01 | 24.4R2-S2.6-EVO | up |
| atl14rt02 | 24.4R2-S2.6-EVO | up |
| aus11rt01 | 23.4R1.10-EVO | up |
| aus11rt02 | 23.4R1.10-EVO | up |
| da11msw01 | 24.4R2-S3.6 | up |
| da11rt01 | 24.4R2-S3.7-EVO | up |
| da11rt02 | 24.4R2-S3.7-EVO | up |
| fk01rt01 | 24.4R2-S2.5 | up |
| fk01rt02 | 24.4R2-S2.5 | up |
| la1rt01 | 24.4R2.18-EVO | up |
| la1rt02 | 24.4R2.18-EVO | up |
| las1fw02 | 21.4R3-S7.9 | up |
| phx1msw01 | 24.4R2-S4.10 | up |
| phx1rt01 | 24.4R2-S4.11-EVO | up |
| phx1rt02 | 24.4R2-S4.11-EVO | up |
| sfo10rt01 | 24.4R2-S2.6-EVO | up |
| sfo10rt02 | 24.4R2-S2.6-EVO | up |
| sv4fw02 | 21.4R3-S7.9 | up |
| sv4rt01 | 21.4R3.15 | up |
| sv4rt02 | 21.4R3.15 | up |
| sv5fw02 | 21.4R3-S7.9 | up |
| sv5rt02 | 21.4R3-S1.5 | up |

> Next step (with approval): apply BACKFILL rows to Nautobot via a reviewed change.
> This script wrote nothing to production.