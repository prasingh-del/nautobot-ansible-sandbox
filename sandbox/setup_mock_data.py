#!/usr/bin/env python3

import sys
import time
import requests

NAUTOBOT_URL = "http://localhost:8080"
API_TOKEN = "0123456789abcdef0123456789abcdef01234567"

API = f"{NAUTOBOT_URL}/api"
HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

session = requests.Session()
session.headers.update(HEADERS)


def wait_for_nautobot(timeout=120):
    print(f"Checking Nautobot API at {API}/ ...")
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            response = session.get(f"{API}/", timeout=5)
            print(f"  HTTP {response.status_code}")
            if response.status_code in (200, 403):
                return
        except requests.RequestException as exc:
            print(f"  waiting: {exc}")

        time.sleep(5)

    sys.exit("ERROR: Nautobot API did not respond in time.")


def api_get(endpoint, params):
    response = session.get(f"{API}/{endpoint}", params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("results", [])


def get_or_create(endpoint, lookup, payload):
    existing = api_get(endpoint, lookup)

    if existing:
        obj = existing[0]
        print(f"EXISTS  {endpoint} -> {obj.get('display') or obj.get('name') or obj.get('id')}")
        return obj

    response = session.post(f"{API}/{endpoint}", json=payload, timeout=30)

    if response.status_code not in (200, 201):
        print(f"ERROR creating {endpoint}")
        print(f"Payload: {payload}")
        print(f"Status : {response.status_code}")
        print(f"Body   : {response.text}")
        sys.exit(1)

    obj = response.json()
    print(f"CREATED {endpoint} -> {obj.get('display') or obj.get('name') or obj.get('id')}")
    return obj


def main():
    wait_for_nautobot()

    print("\nCreating Nautobot mock data...")

    active = get_or_create(
        "extras/statuses/",
        {"name": "Active"},
        {
            "name": "Active",
            "color": "4caf50",
            "content_types": [
                "dcim.device",
                "dcim.interface",
                "ipam.ipaddress",
                "ipam.prefix",
                "dcim.location",
            ],
        },
    )

    location_type = get_or_create(
        "dcim/location-types/",
        {"name": "Site"},
        {
            "name": "Site",
            "content_types": ["dcim.device"],
        },
    )

    site = get_or_create(
        "dcim/locations/",
        {"name": "Foster City"},
        {
            "name": "Foster City",
            "location_type": location_type["id"],
            "status": active["id"],
        },
    )

    manufacturer = get_or_create(
        "dcim/manufacturers/",
        {"name": "Juniper"},
        {"name": "Juniper"},
    )

    role = get_or_create(
        "extras/roles/",
        {"name": "Router"},
        {
            "name": "Router",
            "color": "2196f3",
            "content_types": ["dcim.device"],
        },
    )

    device_type = get_or_create(
        "dcim/device-types/",
        {"model": "MX204"},
        {
            "model": "MX204",
            "manufacturer": manufacturer["id"],
        },
    )

    device = get_or_create(
        "dcim/devices/",
        {"name": "fc01rt01"},
        {
            "name": "fc01rt01",
            "device_type": device_type["id"],
            "role": role["id"],
            "location": site["id"],
            "status": active["id"],
        },
    )

    interface = get_or_create(
        "dcim/interfaces/",
        {"device": device["id"], "name": "et-0/0/1"},
        {
            "device": device["id"],
            "name": "et-0/0/1",
            "type": "10gbase-t",
            "mtu": 1518,
            "status": active["id"],
        },
    )

    namespace = get_or_create(
        "ipam/namespaces/",
        {"name": "Global"},
        {"name": "Global"},
    )

    get_or_create(
        "ipam/prefixes/",
        {"prefix": "10.255.1.82/31"},
        {
            "prefix": "10.255.1.82/31",
            "namespace": namespace["id"],
            "status": active["id"],
        },
    )

    ip_address = get_or_create(
        "ipam/ip-addresses/",
        {"address": "10.255.1.82/31"},
        {
            "address": "10.255.1.82/31",
            "namespace": namespace["id"],
            "status": active["id"],
        },
    )

    get_or_create(
        "ipam/ip-address-to-interface/",
        {"interface": interface["id"], "ip_address": ip_address["id"]},
        {
            "interface": interface["id"],
            "ip_address": ip_address["id"],
        },
    )

    print("\nDone. Created mock data:")
    print("  Site/Location : Foster City")
    print("  Manufacturer  : Juniper")
    print("  Device Type   : MX204")
    print("  Device        : fc01rt01")
    print("  Interface     : et-0/0/1")
    print("  MTU           : 1518")
    print("  IP Address    : 10.255.1.82/31")


if __name__ == "__main__":
    main()
