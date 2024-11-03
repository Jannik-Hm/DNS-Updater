import requests
import ipaddress as ipaddress
import json as json

# from typing import List, Dict

from global_objects import Record
import providers
import providers.hetzner

config_file = open("dns_config.json", "r")
config = json.load(config_file)
config_file.close()

provider: str = config["provider"]
# TODO: add your own token & tld in json files
ttl: int = config["ttl"]

ipv4_config: list[dict[str, object]] = config["ipv4"]["config"]
prefix_offset: int = int(config["ipv6"]["prefix_offset"], 16)
ipv6_config: list[dict[str, object]] = config["ipv6"]["config"]


ipv4: str = requests.get("https://api.ipify.org").text
ipv6: str = requests.get("https://api6.ipify.org").text

ipv6_exploded: str = ipaddress.IPv6Address(ipv6).exploded
ipv6_parts: list[int] = list(map(lambda x: int(x, 16), ipv6_exploded.split(sep=":")))

provider_config = config["provider_config"]

match provider:
    case "hetzner":
        providers.hetzner.updateHetznerEntries(providerConfig=provider_config)

print(prefix_offset)

print()

print(ipv4)
print(ipv6_parts)

print()

print(ipv4_config)
print(ipv6_config)
