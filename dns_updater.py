import requests
import ipaddress as ipaddress
import json as json
from typing import List

ttl: int = 60
prefix_offset: int = int("51", 16)
api_token: str = "<token>"  # TODO: add your own token & tld in json files

ipv4_config_file = open("ipv4-records.json", "r")
ipv6_config_file = open("ipv6-records.json", "r")

ipv4_config: list[dict[str, object]] = json.load(ipv4_config_file)
ipv6_config: list[dict[str, object]] = json.load(ipv6_config_file)

ipv4_config_file.close()
ipv6_config_file.close()

ipv4: str = requests.get("https://api.ipify.org").text
ipv6: str = requests.get("https://api6.ipify.org").text

ipv6_exploded: str = ipaddress.IPv6Address(ipv6).exploded
ipv6_parts: list[int] = list(map(lambda x: int(x, 16), ipv6_exploded.split(sep=":")))

zones = requests.get(
    url="https://dns.hetzner.com/api/v1/zones",
    headers={
        "Auth-API-Token": api_token,
    },
)

#zone_ids: List[str] = zones.json()["zones"]
zone_ids: dict[str, str] = {}

for entry in zones.json()["zones"]:
    zone_ids[entry["name"]] = entry["id"]

print(zone_ids)
print()

print(ipv4)
print(ipv6_parts)

print()

print(ipv4_config)
print(ipv6_config)
