# from typing import Dict
import requests
from global_objects import (
    Record,
    dnsV4Config,
    dnsV4ConfigRecord,
    dnsV6Config,
    dnsV6ConfigRecord,
    globalConfig,
)
from helper_functions import ipv6
import json as json


# TODO: maybe add to global_objects if it can be reused
# maybe remove this object as it is barely used (only records dict)
class Zone_Data(object):
    name: str = ""
    records: dict[str, Record] = {}

    def __init__(self, name: str, records: dict[str, Record]):
        self.name = name
        self.records = records

    def __repr__(self):
        return str({"name": self.name, "records": self.records})


def updateHetznerEntries(
    providerConfig: dict[str, str],
    dnsV4Config: list[dnsV4Config],
    dnsV6Config: list[dnsV6Config],
    globalConfig: globalConfig,
    ipv4Address: str | None = None,
    ipv6Prefix: list[str] | None = None,
) -> None:
    hetzner_api_token: str = providerConfig["api_token"]

# TODO: add Timeouts to all requests + error handling
    getZones = requests.get(
        url="https://dns.hetzner.com/api/v1/zones",
        headers={
            "Auth-API-Token": hetzner_api_token,
        },
    )
    # zone_ids: List[str] = zones.json()["zones"]
    dns_data: dict[str, Zone_Data] = {}
    zone_id_map: dict[str, str] = {}

    for entry in getZones.json()["zones"]:
        dns_data[entry["id"]] = Zone_Data(name=entry["name"], records={})
        zone_id_map[entry["name"]] = entry["id"]

    getRecords = requests.get(
        url="https://dns.hetzner.com/api/v1/records",
        headers={
            "Auth-API-Token": hetzner_api_token,
        },
    )

    for entry in getRecords.json()["records"]:
        if (entry["type"] == "A" and ipv4Address is not None) or (
            entry["type"] == "AAAA" and ipv6Prefix is not None and ipv6Prefix.__len__() >= 4
        ):
            dns_data[entry["zone_id"]].records[entry["type"] + "-" + entry["name"]] = (
                Record(
                    type=entry["type"],
                    id=entry["id"],
                    zone_id=entry["zone_id"],
                    name=entry["name"],
                    ttl=entry["ttl"],
                    value=entry["value"],
                )
            )

    createRecordsBody: list = []
    updateRecordsBody: list = []

    if ipv4Address is not None:
        for zone in dnsV4Config:
            zone_id: str = zone_id_map[zone.zone]
            for record in zone.records:
                if dns_data[zone_id].records.__contains__("A-" + record.name):
                    if(ipv4Address != dns_data[zone_id].records["A-" + record.name].value):
                        updateRecordsBody.append(
                            {
                                "id": dns_data[zone_id].records["A-" + record.name].id,
                                "zone_id": zone_id,
                                "type": "A",
                                "name": record.name,
                                "value": ipv4Address,
                                "ttl": globalConfig.ttl,
                            }
                        )
                else:
                    createRecordsBody.append(
                        {
                            "zone_id": zone_id,
                            "type": "A",
                            "name": record.name,
                            "value": ipv4Address,
                            "ttl": globalConfig.ttl,
                        }
                    )

    if ipv6Prefix is not None and ipv6Prefix.__len__() >= 4:
        for zone in dnsV6Config:
            zone_id: str = zone_id_map[zone.zone]
            for record in zone.records:
                record_exists: bool = dns_data[zone_id].records.__contains__(
                    "AAAA-" + record.name
                )
                ipv6Address: str = ipv6.calculateIPv6Address(
                    prefix=ipv6Prefix,
                    prefixOffset=record.prefixOffset,
                    currentAddressOrFixedSuffix=(record.suffix or dns_data[zone_id].records["AAAA-" + record.name].value)
                )
                if record_exists:
                    if(ipv6Address != dns_data[zone_id].records["AAAA-" + record.name].value):
                        updateRecordsBody.append(
                            {
                                "id": dns_data[zone_id].records["AAAA-" + record.name].id,
                                "zone_id": zone_id,
                                "type": "AAAA",
                                "name": record.name,
                                "value": ipv6Address,
                                "ttl": globalConfig.ttl,
                            }
                        )
                else:
                    createRecordsBody.append(
                        {
                            "zone_id": zone_id,
                            "type": "AAAA",
                            "name": record.name,
                            "value": ipv6Address,
                            "ttl": globalConfig.ttl,
                        }
                    )

    print(updateRecordsBody)

    if(updateRecordsBody.__len__() > 0):
        updateResponse = requests.put(
                url="https://dns.hetzner.com/api/v1/records/bulk",
                headers={
                    "Content-Type": "application/json",
                    "Auth-API-Token": hetzner_api_token,
                },
                data=json.dumps({
                    "records": updateRecordsBody
                })
            )

    print(createRecordsBody)

    if(createRecordsBody.__len__() > 0):
        createResponse = requests.post(
                url="https://dns.hetzner.com/api/v1/records/bulk",
                headers={
                    "Content-Type": "application/json",
                    "Auth-API-Token": hetzner_api_token,
                },
                data=json.dumps({
                    "records": createRecordsBody
                })
            )

    return
