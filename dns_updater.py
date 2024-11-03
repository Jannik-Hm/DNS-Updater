import requests
import ipaddress as ipaddress
import json as json
from typing import List, Optional


config_file = open("dns_config.json", "r")
config = json.load(config_file)
config_file.close()


hetzner_api_token: str = config["provider_config"]["api_token"]  # TODO: add your own token & tld in json files
ttl: int = config["ttl"]

ipv4_config: list[dict[str, object]] = config["ipv4"]["config"]
prefix_offset: int = int(config["ipv6"]["prefix_offset"], 16)
ipv6_config: list[dict[str, object]] = config["ipv6"]["config"]


ipv4: str = requests.get("https://api.ipify.org").text
ipv6: str = requests.get("https://api6.ipify.org").text

ipv6_exploded: str = ipaddress.IPv6Address(ipv6).exploded
ipv6_parts: list[int] = list(map(lambda x: int(x, 16), ipv6_exploded.split(sep=":")))

zones = requests.get(
    url="https://dns.hetzner.com/api/v1/zones",
    headers={
        "Auth-API-Token": hetzner_api_token,
    },
)

#zone_ids: List[str] = zones.json()["zones"]
zone_ids: dict[str, str] = {}

for entry in zones.json()["zones"]:
    zone_ids[entry["name"]] = entry["id"]

class Record(object):
    ttl: int = 0
    name: str = ""
    value: str = ""
    type: str = ""
    id: Optional[str]

    def __init__(self, type: str, name: str, value: str, ttl: int, id: str | None = None):
        self.ttl = ttl
        self.name = name
        self.value = value
        self.type = type
        self.id = id

    def __str__(self):
        return "name: "+self.name+", value: "+self.value+", type: "+self.type+", ttl: "+str(self.ttl)+", id: "+str(self.id)

temp: Record = Record(type="A", name="test", value="1.2.3.4", ttl=ttl)

print(temp)

print(prefix_offset)

print(zone_ids)
print()

print(ipv4)
print(ipv6_parts)

print()

print(ipv4_config)
print(ipv6_config)
