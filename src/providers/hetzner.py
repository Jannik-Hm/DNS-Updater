# from typing import Dict
import requests
from global_objects import Record


# TODO: maybe add to global_objects if it can be reused
class Zone_Data(object):
    name: str = ""
    records: list[Record] = []

    def __init__(self, name: str, records: list[Record]):
        self.name = name
        self.records = records

    def __repr__(self):
        return str({"name": self.name, "records": self.records})


def updateHetznerEntries(providerConfig: dict[str, str]) -> None:
    hetzner_api_token: str = providerConfig["api_token"]

    getZones = requests.get(
        url="https://dns.hetzner.com/api/v1/zones",
        headers={
            "Auth-API-Token": hetzner_api_token,
        },
    )
    # zone_ids: List[str] = zones.json()["zones"]
    dns_data: dict[str, Zone_Data] = {}

    for entry in getZones.json()["zones"]:
        dns_data[entry["id"]] = Zone_Data(name=entry["name"], records=[])

    getRecords = requests.get(
        url="https://dns.hetzner.com/api/v1/records",
        headers={
            "Auth-API-Token": hetzner_api_token,
        },
    )

    for entry in getRecords.json()["records"]:
        if entry["type"] == "A" or entry["type"] == "AAAA":
            dns_data[entry["zone_id"]].records.append(
                Record(
                    type=entry["type"],
                    id=entry["id"],
                    name=entry["name"],
                    ttl=entry["ttl"],
                    value=entry["value"],
                )
            )

    print(dns_data)

    return
