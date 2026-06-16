# Sandbox — Local Nautobot → Ansible → Junos PoC

**Goal:** A safe, local proof-of-concept of the whole idea, where it's OK to
*write* data (unlike production, which is read-only).

## What it is
A local Nautobot in Docker, populated with mock data, then read by Ansible to
render a Juniper Junos config from a Jinja2 template:

```
Nautobot (Docker)  →  Ansible (uri lookup)  →  Jinja2 template  →  Junos config
```

## Files
- `docker-compose.yml` — local Nautobot + Postgres + Redis (port 8080)
- `setup_mock_data.py` — populates Nautobot via API (device, interface, IP, etc.)
- `playbook.yml` + `inventory.yml` — pull data + render config
- `templates/junos_interface.j2` — the Junos interface template
- `ansible.cfg` — points at `inventory.yml`

## Run
```bash
docker compose up -d                  # start local Nautobot (wait until healthy)
python3 setup_mock_data.py            # create mock source-of-truth data
ansible-playbook playbook.yml         # renders compiled_config.txt
```

## Notes
- This is the original learning exercise; the step-by-step log is in
  `KT/LEARNING_LOG.md`.
- `compiled_config.txt` is generated output (gitignored).
- Safe to experiment here — it never touches production.
