import requests
import ipaddress as ipaddress
import json as json

from typing import Optional

from global_objects import Record
import providers
import providers.hetzner

config_file = open("dns_config.json", "r")
config = json.load(config_file)
config_file.close()

ttl: int = config["global"]["ttl"]

ipv4: Optional[str] = None
ipv6: Optional[str] = None

try:
    ipv4 = requests.get("https://api.ipify.org", timeout=5).text
except requests.exceptions.ConnectTimeout:
    print("Timeout") #TODO: perform Logging of timeout
try:
    ipv6 = requests.get("https://api6.ipify.org", timeout=5).text
except requests.exceptions.ConnectTimeout:
    print("Timeout") #TODO: perform Logging of timeout


for provider in config["providers"]:
# TODO: add your own token & tld in json files
    print(provider)

    ipv4_config: list[dict[str, object]] = provider["ipv4"]["config"]
    prefix_offset: int = int(config["global"]["prefix_offset"], 16)
    ipv6_config: list[dict[str, object]] = provider["ipv6"]["config"]

    if(ipv6 != None):
        ipv6_exploded: str = ipaddress.IPv6Address(ipv6).exploded
        ipv6_parts: list[int] = list(map(lambda x: int(x, 16), ipv6_exploded.split(sep=":")))

    provider_config = provider["provider_config"]

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
