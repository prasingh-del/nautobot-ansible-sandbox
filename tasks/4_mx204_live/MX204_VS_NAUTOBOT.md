# MX204: Real Device vs Nautobot (read-only)

- Device hostname (from box): `TEST-JUNOS`
- Device model/serial/version: `mx204` / `FG969` / `21.4R2-S1.4`
- Compared against Nautobot device: `test-junos`

> Nautobot has no device named `test-junos`. Set MX204_NAUTOBOT_NAME in .env.local to compare against a specific device.

Device reports **40** physical interfaces:

cbp0, demux0, em2, em3, em4, et-0/0/0, et-0/0/1, et-0/0/2, fti0, fti1, fti2, fti3, fti4, fti5, fti6, fti7, fxp0, gr-0/0/0, ip-0/0/0, lc-0/0/0, lo0, lt-0/0/0, mt-0/0/0, pd-0/0/0, pe-0/0/0, pfe-0/0/0, pfh-0/0/0, pip0, pp0, ud-0/0/0, ut-0/0/0, vt-0/0/0, xe-0/1/0, xe-0/1/1, xe-0/1/2, xe-0/1/3, xe-0/1/4, xe-0/1/5, xe-0/1/6, xe-0/1/7