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

def updateHetznerEntries(
    providerConfig: dict[str, str],
    dnsV4Config: list[dnsV4Config],
    dnsV6Config: list[dnsV6Config],
    globalConfig: globalConfig,
    ipv4Address: str | None = None,
    ipv6Prefix: list[str] | None = None,
) -> None:
    hetzner_api_token: str = providerConfig["api_token"]

    # TODO: log errors instead of just printing
    getZones = requests.get(
        url="https://dns.hetzner.com/api/v1/zones",
        headers={
            "Auth-API-Token": hetzner_api_token,
        },
        timeout=5,
    )
    # zone_ids: List[str] = zones.json()["zones"]
    dns_records_data: dict[str, dict[str, Record]] = {}
    zone_id_map: dict[str, str] = {}

    if getZones.status_code != 200:
        match getZones.status_code:
            case 400:
                print("Get Zones - Pagination selectors are mutually exclusive")
                return
            case 401:
                print("Get Zones - " + getZones.reason)
                return
            case 406:
                print("Get Zones - " + getZones.reason)
                return
    else:
        for entry in getZones.json()["zones"]:
            dns_records_data[entry["id"]] = {}
            zone_id_map[entry["name"]] = entry["id"]

        getRecords = requests.get(
            url="https://dns.hetzner.com/api/v1/records",
            headers={
                "Auth-API-Token": hetzner_api_token,
            },
            timeout=10,  # wait longer for bigger responses in case of a lot of records
        )

        if getRecords.status_code != 200:
            match getRecords.status_code:
                case 401:
                    print("Get Records - " + getRecords.reason)
                    return
                case 406:
                    print("Get Records - " + getRecords.reason)
                    return
        else:
            for entry in getRecords.json()["records"]:
                if (entry["type"] == "A" and ipv4Address is not None) or (
                    entry["type"] == "AAAA"
                    and ipv6Prefix is not None
                    and ipv6Prefix.__len__() >= 4
                ):
                    dns_records_data[entry["zone_id"]][
                        entry["type"] + "-" + entry["name"]
                    ] = Record(
                        type=entry["type"],
                        id=entry["id"],
                        zone_id=entry["zone_id"],
                        name=entry["name"],
                        ttl=entry["ttl"],
                        value=entry["value"],
                    )

            createRecordsBody: list = []
            updateRecordsBody: list = []

            if ipv4Address is not None:
                for zone in dnsV4Config:
                    zone_id: str = zone_id_map[zone.zone]
                    for record in zone.records:
                        if dns_records_data[zone_id].__contains__("A-" + record.name):
                            if (
                                ipv4Address
                                != dns_records_data[zone_id]["A-" + record.name].value
                            ):
                                updateRecordsBody.append(
                                    {
                                        "id": dns_records_data[zone_id][
                                            "A-" + record.name
                                        ].id,
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
                        record_exists: bool = dns_records_data[zone_id].__contains__(
                            "AAAA-" + record.name
                        )
                        ipv6Address: str = ipv6.calculateIPv6Address(
                            prefix=ipv6Prefix,
                            prefixOffset=record.prefixOffset,
                            currentAddressOrFixedSuffix=(
                                record.suffix
                                or dns_records_data[zone_id][
                                    "AAAA-" + record.name
                                ].value
                            ),
                        )
                        if record_exists:
                            if (
                                ipv6Address
                                != dns_records_data[zone_id][
                                    "AAAA-" + record.name
                                ].value
                            ):
                                updateRecordsBody.append(
                                    {
                                        "id": dns_records_data[zone_id][
                                            "AAAA-" + record.name
                                        ].id,
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

            if updateRecordsBody.__len__() > 0:
                updateResponse = requests.put(
                    url="https://dns.hetzner.com/api/v1/records/bulk",
                    headers={
                        "Content-Type": "application/json",
                        "Auth-API-Token": hetzner_api_token,
                    },
                    data=json.dumps({"records": updateRecordsBody}),
                    timeout=10,
                )

                if updateResponse.status_code != 200:
                    match updateResponse.status_code:
                        case 401:
                            print("Update A Records Error - " + updateResponse.reason)
                        case 403:
                            print("Update A Records Error - " + updateResponse.reason)
                        case 406:
                            print("Update A Records Error - " + updateResponse.reason)
                        case 422:
                            print("Update A Records Error - Unprocessable entity")

            print(createRecordsBody)

            if createRecordsBody.__len__() > 0:
                createResponse = requests.post(
                    url="https://dns.hetzner.com/api/v1/records/bulk",
                    headers={
                        "Content-Type": "application/json",
                        "Auth-API-Token": hetzner_api_token,
                    },
                    data=json.dumps({"records": createRecordsBody}),
                    timeout=10,
                )

                if createResponse.status_code != 200:
                    match createResponse.status_code:
                        case 401:
                            print(
                                "Update AAAA Records Error - " + createResponse.reason
                            )
                        case 403:
                            print(
                                "Update AAAA Records Error - " + createResponse.reason
                            )
                        case 404:
                            print(
                                "Update AAAA Records Error - " + createResponse.reason
                            )
                        case 406:
                            print(
                                "Update AAAA Records Error - " + createResponse.reason
                            )
                        case 409:
                            print(
                                "Update AAAA Records Error - " + createResponse.reason
                            )
                        case 422:
                            print("Update AAAA Records Error - Unprocessable entity")

    return
