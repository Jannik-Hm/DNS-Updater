import requests
import ipaddress as ipaddress
import json as json

from typing import Optional

from global_objects import Record, dnsV4Config, dnsV4ConfigRecord, dnsV6Config, dnsV6ConfigRecord, globalConfig
import providers
import providers.hetzner

config_file = open("dns_config.json", "r")
config = json.load(config_file)
config_file.close()

global_config: globalConfig = globalConfig(ttl=config["global"]["ttl"], prefix_offset=config["global"]["prefix_offset"])

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

    ipv4_config: list[dnsV4Config] = []
    ipv6_config: list[dnsV6Config] = []
    prefix_offset: int = int(config["global"]["prefix_offset"], 16)

    for zone in provider["zones"]:

        ipv4_config.append(dnsV4Config(zone["name"], list(map(lambda x: dnsV4ConfigRecord(name=x["name"]), zone["ipv4_records"]))))

        ipv6_config.append(dnsV6Config(zone["name"], list(map(lambda x: dnsV6ConfigRecord(name=x["name"],prefixOffset=x["prefixOffset"],suffix=x["suffix"]), zone["ipv6_records"]))))

    #ipv6_config: list[dict[str, object]] = provider["ipv6"]["config"]

    if(ipv6 is not None):
        ipv6_exploded: str = ipaddress.IPv6Address(ipv6).exploded
        ipv6_parts: list[str] = ipv6_exploded.split(sep=":")

    provider_config = provider["provider_config"]

    match provider["provider"]:
        case "hetzner":
            providers.hetzner.updateHetznerEntries(providerConfig=provider_config, dnsV4Config=ipv4_config, ipv4Address=ipv4, dnsV6Config=ipv6_config, ipv6Prefix=ipv6_parts[:4], globalConfig=global_config)

    print(prefix_offset)

    print()

    print(ipv4)
    print(ipv6_parts)

    print()

    print(ipv4_config)
    print(ipv6_config)
