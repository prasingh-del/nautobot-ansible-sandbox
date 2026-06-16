# Cacti vs Nautobot Reconciliation (read-only)

Cacti = graphing/weathermap (actual). Nautobot = source of truth (intended).
No changes were made to either system.

## Totals

| Metric | Count |
| --- | --- |
| Nautobot devices | 484 |
| Cacti weathermaps | 6 |
| Cacti graphs | 1837 |
| Distinct hosts seen in Cacti | 70 |
| Hosts in BOTH | 48 |
| In Cacti but NOT in Nautobot | 22 |
| In Nautobot but NOT in Cacti | 436 |
| Proposed interface-description backfills | 0 |

## Graphed in Cacti but missing from Nautobot

These devices are actively monitored/graphed but absent from the source of truth.

| Cacti host |
| --- |
| atl14rt01 |
| atl14rt02 |
| aus11rt01 |
| aus11rt02 |
| la1rt01 |
| la1rt02 |
| sfo10rt01 |
| sfo10rt02 |
| sunfw01a |
| sunfw05a |
| sunzbsw01 |
| sunzbsw02 |
| sunzbsw03 |
| sunzbsw04 |
| sunzbsw05 |
| sunzbsw06 |
| sunzbsw08 |
| sv4fw03 |
| sv4rt01 |
| sv4rt02 |
| sv5fw03 |
| sv5rt02 |

## Bonus: interface descriptions Cacti knows for Cacti-only devices

These devices aren't in Nautobot yet; Cacti already documents their links —

ready-made descriptions for when they're onboarded.

| Cacti host | Interface | Cacti description |
| --- | --- | --- |
| sv4rt02 | et-0/1/3 | Cust: AWS [100Gb] {dxcon-fh4xc6qn} (CAS- |
| sv4rt02 | et-0/1/3.3201 | sv4-2-public-ipv4 |
| sv4rt02 | et-0/1/3.3202 | sv4-2-public-ipv6 |
| sv4rt02 | et-0/1/3.3203 | sv4-2-usw1-vpc-default-10_1_0_0-16 |
| sv4rt02 | et-0/1/3.3204 | sv4-2-usw2-vpc-default-10_3_0_0-16 |
| sv4rt02 | et-0/1/3.3205 | sv4-2-usw2-vpc-eksctldev-10_4_32_0-23 |
| sv4rt02 | et-0/1/3.3206 | sv4-2-use1-vpc-10_8_0_0-16 |
| sv4rt02 | et-0/1/3.3207 | sv4-2-usw2-vpc-sap-10_7_4_0-23 |
| sv4rt02 | et-0/1/3.3208 | sv4-2-usw2-vpc-10_4_48_0-20 |
| sv4rt02 | et-0/1/3.3209 | sv4-2-usw2-vpc-redshift-10_4_64_0-24 |
| sv4rt02 | et-0/1/3.3210 | sv4-2-usw2-vpc-itservices-10_10_0_0-16 |
| sv4rt02 | et-0/1/3.3212 | sv4-2-usw1-vpc-dispatch-10_2_0_0-20 |
| sv4rt02 | et-0/1/3.3213 | sv4-2-usw1-vpc-teleops-10_2_16_0-20 |
| sv4rt02 | et-0/1/3.3214 | sv4-2-usw1-vpc-it-test-10_2_32_0-24 |
| sv4rt02 | et-0/1/3.3215 | sv4-2-usw1-vpc-it-10_4_128_0-17 |
| sv4rt02 | et-0/1/3.3216 | sv4-2-usw1-vpc-corp-172_30_0_0-16 |
| sv4rt02 | et-0/1/3.3217 | sv4-2-usw2-vpc-kraken-10_4_0_0-19 |
| sv4rt02 | et-0/1/3.3218 | sv4-2-usw2-vpc-it-security-logging-10_7_ |
| sv4rt02 | et-0/1/3.3219 | sv4-2-use1-vpc-it-10_11_0_0-21 |
| sv4rt02 | et-0/1/3.3220 | sv4-2-euw1-vpc-htec-10_9_8_0-21 |
| sv4rt02 | et-0/1/3.3221 | sv4-2-netsec-commercial-prod-tgw-024ea58 |
| sv4rt02 | et-0/1/3.3222 | sv4-2-use1-vpc-auth_prod-10_21_216_0-23 |
| sv4rt02 | et-0/1/3.3223 | sv4-2-ntwk-prod-tgw-0a1c94e8fdbead7d4 |
| sv4rt02 | et-0/1/3.3224 | sv4-2-ntwk-rnd-dev-tgw-04ceec374612155f7 |
| sv4rt02 | et-0/1/3.3225 | sv4-2-use1-vpc-it-core-prod-10_21_192_0- |
| sv4rt02 | et-0/1/3.3226 | sv4-2-use1-vpc-pipedream-storage-vpc-10_ |
| sv5rt02 | et-0/1/3 | Cust: AWS [100Gb] {dxcon-fgo3jomj} (2215 |
| sv5rt02 | et-0/1/3.3201 | sv5-2-public-ipv4 |
| sv5rt02 | et-0/1/3.3202 | sv5-2-public-ipv6 |
| sv5rt02 | et-0/1/3.3203 | sv5-2-usw1-vpc-default-10_1_0_0-16 |
| sv5rt02 | et-0/1/3.3204 | sv5-2-usw2-vpc-default-10_3_0_0-16 |
| sv5rt02 | et-0/1/3.3205 | sv5-2-usw2-vpc-eksctldev-10_4_32_0-23 |
| sv5rt02 | et-0/1/3.3206 | sv5-2-use1-vpc-10_8_0_0-16 |
| sv5rt02 | et-0/1/3.3207 | sv5-2-usw2-vpc-sap-10_7_4_0-23 |
| sv5rt02 | et-0/1/3.3208 | sv5-2-usw2-vpc-10_4_48_0-20 |
| sv5rt02 | et-0/1/3.3209 | sv5-2-usw2-vpc-redshift-10_4_64_0-24 |
| sv5rt02 | et-0/1/3.3210 | sv5-2-usw2-vpc-itservices-10_10_0_0-16 |
| sv5rt02 | et-0/1/3.3212 | sv5-2-usw1-vpc-dispatch-10_2_0_0-20 |
| sv5rt02 | et-0/1/3.3213 | sv5-2-usw1-vpc-teleops-10_2_16_0-20 |
| sv5rt02 | et-0/1/3.3214 | sv5-2-usw1-vpc-it-test-10_2_32_0-24 |
| sv5rt02 | et-0/1/3.3215 | sv5-2-usw1-vpc-it-10_4_128_0-17 |
| sv5rt02 | et-0/1/3.3216 | sv5-2-usw1-vpc-corp-172_30_0_0-16 |
| sv5rt02 | et-0/1/3.3217 | sv5-2-usw2-vpc-kraken-10_4_0_0-19 |
| sv5rt02 | et-0/1/3.3218 | sv5-2-usw2-vpc-it-security-logging-10_7_ |
| sv5rt02 | et-0/1/3.3219 | sv5-2-use1-vpc-it-10_11_0_0-21 |
| sv5rt02 | et-0/1/3.3220 | sv5-2-euw1-vpc-htec-10_9_8_0-21 |
| sv5rt02 | et-0/1/3.3221 | sv5-2-netsec-commercial-prod-tgw-024ea58 |
| sv5rt02 | et-0/1/3.3222 | sv5-2-use1-vpc-auth_prod-10_21_216_0-23 |
| sv5rt02 | et-0/1/3.3223 | sv5-2-ntwk-prod-tgw-0a1c94e8fdbead7d4 |
| sv5rt02 | et-0/1/3.3224 | sv5-2-ntwk-rnd-dev-tgw-04ceec374612155f7 |
| sv5rt02 | et-0/1/3.3225 | sv5-2-use1-vpc-it-core-prod-10_21_192_0- |
| sv5rt02 | et-0/1/3.3226 | sv5-2-use1-vpc-pipedream-storage-vpc-10_ |

## Hosts in both systems (sanity)

aus01csw01, aus01csw02, clart01, clart02, fc01rt01, fc01rt02, fc01rt03, fc01rt04, fc01rt05, fc02rt01, fc02rt02, fc07csw01, las1rt01, las1rt02, mi1rt01, mi1rt02, mia101csw01, mia101csw02, sf02rt01, sf02rt02, sun-arspine04a, sun-arspine04b, sun-arspine05a, sun-arspine05b, sun-arspine06a, sun-arspine06b, sun-spine01a, sun-spine01b, sun-spine02a, sun-spine02b, sun-spine03a, sun-spine03b, sun-spine07a, sun-spine07b, sun-spine08a, sun-spine08b, sun-spine09a, sun-spine09b, suncsw01, suncsw02, sunits01, sunits02, sunrt01, sunrt02, sunrt03, sunzbcsw01, sunzbcsw02, sv5rt01

## Notes & caveats

- Cacti's Graphs **list view truncates long titles** (~40 chars), so some
  descriptions above are cut off (e.g. `...(CAS-`). Full text is on each graph's
  edit page; a follow-up can fetch complete labels if needed.
- Junos devices already in Nautobot use a `HOST - Traffic - <iface>` graph naming
  that carries **no per-interface description**, so 0 direct backfills — honest, not a bug.
- The rich descriptions live on **edge/WAN routers** (e.g. `sv4rt02`, `sv5rt02`)
  which are **not in Nautobot** — captured in the bonus table for onboarding.
- The 22 Cacti-only devices strongly overlap the 22 **Observium-only** Junos routers
  found earlier (Atlanta, Austin, LA, SFO, etc.) — independent cross-validation of the
  same source-of-truth coverage gap.

> Next step (with approval): onboard the genuinely-missing devices, then backfill
> descriptions from this data via a reviewed Nautobot change.
> This script wrote nothing to production.