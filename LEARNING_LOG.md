# Nautobot to Ansible Learning Log

This document tracks the sandbox build step by step. Use it as a revision guide:
what was asked, what command was run, what output was expected, what actually
happened, and the short explanation of why it matters.

## Project Goal

Build a local Nautobot-to-Ansible sandbox that stores network device data in
Nautobot and uses Ansible/Jinja2 to generate Juniper Junos configuration.

## Running Notes

| Step | Your Ask / Question | What We Did | Expected Output | Actual Output / Status | Short Note |
| --- | --- | --- | --- | --- | --- |
| 0 | Reset everything and start from zero | Removed old Compose containers, volume, network, and project folder | No old project folder, containers, volumes, or network remain | Confirmed clean in terminal | This gives us a fresh starting point and avoids old database/config issues. |
| 1 | Create a fresh project folder | Created `~/nautobot-ansible-sandbox` and `templates/` | `pwd` shows `/Users/prasingh/nautobot-ansible-sandbox`; `ls -la` shows `templates/` | Confirmed | This folder will hold Docker, Python, Ansible, and Jinja2 files. |
| 2 | Create and validate Docker Compose | Created `docker-compose.yml`, then ran `docker compose config` | Compose prints the resolved configuration with no errors | Confirmed valid | This checks the YAML and service wiring before starting containers. |
| 3 | Start the sandbox containers | Ran `docker compose up -d`, then checked `docker compose ps` | Images pull if missing; network, volume, and containers are created; Postgres and Redis become healthy; Nautobot listens on port `8080` | Step 3 is fully complete. The latest `docker compose ps` shows Nautobot `Up About a minute (healthy)`, Postgres `healthy`, Redis `healthy`, and Nautobot mapped to `0.0.0.0:8080->8080/tcp` plus `[::]:8080->8080/tcp`. | Nautobot web/API should now be ready for browser/API testing before any data population. |
| 4 | Diagnose `curl -I http://localhost:8080` reset and verify login | Changed Compose port mapping to `8080:8000`, reran `docker compose up -d`, then retried `curl -I http://localhost:8080` | Nautobot should answer HTTP on host port `8080` | First `curl` briefly reset, then the second returned `HTTP/1.1 302 Found` with `Location: /login/?next=/`. | The port mapping fix succeeded. `302 Found` is expected because Nautobot redirects unauthenticated browser/API root access to login. Next step: verify browser login with `admin`/`admin`, or proceed to Python tooling setup. |
| 5 | Fix Nautobot login credentials | Created the `admin` superuser manually with `docker compose exec nautobot nautobot-server createsuperuser` | Browser login should work with `admin` / `admin` | Login succeeded after accepting the simple password warning | The lab image did not auto-create the expected user from env vars, so we created it directly inside Nautobot. |
| 6 | Create and activate the Python virtual environment | First mistyped `spython3 -m venv .venv`, then ran `python3 -m venv .venv`, `source .venv/bin/activate`, and `python3 --version` | Prompt shows `(.venv)` and Python prints its version | `(.venv)` is active and `python3 --version` returned `Python 3.11.9` | The typo was harmless because zsh only reported command not found. The venv was created and activated successfully; next create `requirements.txt` and install `requests` plus `ansible-core`. |
| 7 | Install and verify Python/Ansible dependencies | Installed dependencies from `requirements.txt`, then verified `requests` import and `ansible-playbook --version` | `requests` imports successfully and Ansible reports its installed version from the venv | Install completed successfully with `requests-2.32.3` and `ansible-core-2.17.14`; `python -c "import requests; print('requests OK')"` printed `requests OK`; `ansible-playbook --version` reported `ansible-playbook [core 2.17.14]` from `.venv/bin/ansible-playbook` using Python `3.11.9`. | Dependencies are installed and verified. Next step: create `setup_mock_data.py` to populate Nautobot through the API. |
| 8 | Create `setup_mock_data.py` for mock Nautobot data | Created `setup_mock_data.py`, then ran `python3 -m py_compile setup_mock_data.py` | Python should report no syntax errors | Syntax verification completed successfully | The script will create/support Nautobot API objects: status `Active`, location type `Site`, Foster City location, Juniper manufacturer, Router role, MX204 device type, device `fc01rt01`, interface `et-0/0/1` with MTU `1518`, namespace/prefix/IP `10.255.1.82/31`, and IP-to-interface assignment. Next step: run `python3 setup_mock_data.py`. |
| 9 | Confirm mock data population after creating admin API token | Reran `python3 setup_mock_data.py` | API check should return `HTTP 200`, and the script should create or reuse the Nautobot source-of-truth objects | `HTTP 200`; status `Active` and namespace `Global` already existed; location type `Site`, location `Foster City`, manufacturer `Juniper`, role `Router`, device type `Juniper MX204`, device `fc01rt01`, interface `et-0/0/1`, prefix `10.255.1.82/31`, IP address `10.255.1.82/31`, and the IP-to-interface assignment were created. Final summary printed MTU `1518` and IP Address `10.255.1.82/31`. | Nautobot is now populated with source-of-truth mock data. Next step: create the Ansible config, inventory, Jinja2 template, and playbook to generate Junos config. |
| 10 | Create Ansible config, inventory, template, and playbook | Created `ansible.cfg`, `inventory.yml`, `templates/junos_interface.j2`, and `playbook.yml`; ran `ansible-playbook --syntax-check playbook.yml` | Syntax check should print `playbook: playbook.yml` | Syntax check passed | Ansible files are valid and ready to pull Nautobot data and render Junos config. |
| 11 | Generate Junos config from Nautobot data | Ran `ansible-playbook playbook.yml`, then `cat compiled_config.txt` | Playbook should find interface/IP data and create a Junos config file | Playbook completed with `failed=0`; debug showed device `fc01rt01`, interface `et-0/0/1`, MTU `1518`, IP `10.255.1.82/31`; `compiled_config.txt` was generated | End-to-end proof is complete: Nautobot source-of-truth data was pulled by Ansible and rendered into Junos configuration. |
| 12 | Manually add Nautobot data and pull it from terminal | In progress / next exercise | Add a second device manually in the Nautobot UI, then pull it with API/Ansible | Pending | This proves the workflow works without the Python mock-data script: UI data entry -> terminal/API retrieval -> generated config. |

## Step-by-Step Workflow

We will move one step at a time. After each step:

1. Run only the commands for that step.
2. Compare your terminal output with the expected output.
3. Paste or summarize the output.
4. Continue only after the step is confirmed correct.

## Question Notes

Use this section for short revision notes when questions come up during the
build.

| Question | Short Answer |
| --- | --- |
| Why start from zero? | It removes old containers, networks, volumes, and files so we can debug cleanly. |
| Why create `templates/` now? | Ansible will later look there for the Junos Jinja2 template. |
| What does `health: starting` mean? | Docker has started the container, but the health check has not passed yet. For Nautobot this is normal at first; wait and check readiness/logs before API or data population steps. |
| Why did `curl` return `302 Found`? | Nautobot was reachable and redirected unauthenticated access to `/login/`, which is expected. |
| Why did `admin/admin` fail at first? | The lab image did not create the expected superuser automatically, so we created it manually with `createsuperuser`. |
| Why did the API script return `403 Forbidden`? | The browser login worked, but the static API token was not attached to the manually created admin user. Creating the token fixed API access. |
| What if `Router`, `Juniper`, or `Foster City` already exists in Nautobot? | Reuse the existing object instead of creating a duplicate. Nautobot enforces unique names for many object types. |
| What does the final config prove? | It proves Nautobot can store network intent and Ansible can pull that intent to generate Juniper Junos configuration. |

## Important Concepts

### Nautobot

Nautobot is the network source of truth. It stores devices, device types,
interfaces, IP addresses, sites/locations, roles, and other network inventory
data.

### Ansible

Ansible reads data and performs automation. In this sandbox, Ansible does not
connect to a real router. It reads data from Nautobot and renders a local config
file.

### Jinja2 Template

Jinja2 is the template language Ansible uses. We will create a Junos interface
template and fill it with values from Nautobot, such as interface name, MTU, and
IP address.

### Docker Compose

Docker Compose starts the local services needed for Nautobot:

- Nautobot application
- Postgres database
- Redis cache/queue

### Juniper MX204

MX204 is a Juniper router model. We use it as the mock device type in Nautobot
for Junos configuration testing.

## Final Working Outcome

The sandbox currently works end to end:

```text
Nautobot source-of-truth
        ↓
Ansible API lookup
        ↓
Jinja2 Junos template
        ↓
compiled_config.txt
```

The generated config contains:

```text
interfaces {
    et-0/0/1 {
        description "Managed by Nautobot/Ansible";
        mtu 1518;
        unit 0 {
            family inet {
                address 10.255.1.82/31;
            }
        }
    }
}
```

## Current Next Step

For manual practice, add a new device/interface/IP in the Nautobot UI, then pull
that data from the terminal using the API or Ansible.

Suggested manual test object:

- Device: `fc01rt02`
- Interface: `et-0/0/2`
- MTU: `1518`
- IP Address: `10.255.1.84/31`

## GitHub Status

GitHub CLI (`gh`) is not installed yet. To connect GitHub later, install it and
authenticate:

```bash
brew install gh
gh auth login
```
