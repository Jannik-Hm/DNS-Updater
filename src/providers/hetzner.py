# from typing import Dict
import requests


def updateHetznerEntries(providerConfig: dict[str, str]) -> None:
    hetzner_api_token: str = providerConfig["api_token"]

    zones = requests.get(
        url="https://dns.hetzner.com/api/v1/zones",
        headers={
            "Auth-API-Token": hetzner_api_token,
        },
    )
    # zone_ids: List[str] = zones.json()["zones"]
    zone_ids: dict[str, str] = {}

    for entry in zones.json()["zones"]:
        zone_ids[entry["name"]] = entry["id"]

    print(zone_ids)

    return
