import requests
import ipaddress as ipaddress
import json as json

from typing import Optional

from global_objects import (
    dnsV4Config,
    dnsV4ConfigRecord,
    dnsV6Config,
    dnsV6ConfigRecord,
    globalConfig,
)
import providers
import providers.hetzner
from helper_functions import ipv6

config_file = open("dns_config.json", "r")
config = json.load(config_file)
config_file.close()

global_config: globalConfig = globalConfig(
    ttl=config["global"]["ttl"], prefix_offset=config["global"]["current_prefix_offset"]
)

ipv4Address: Optional[str] = None
ipv6Address: Optional[str] = None
ipv6Prefix: Optional[list[str]] = None

try:
    ipv4Address = requests.get("https://api.ipify.org", timeout=5).text
except requests.exceptions.ConnectTimeout:
    print("Timeout")  # TODO: perform Logging of timeout
try:
    ipv6Address = requests.get("https://api6.ipify.org", timeout=5).text
    if ipv6Address is not None:
        ipv6Prefix = ipv6.calculateIPv6Address(
            prefix=ipaddress.IPv6Address(ipv6Address).exploded.split(":"),
            prefixOffset="-" + str(global_config.prefix_offset), # negative Offset
            currentAddressOrFixedSuffix="::",
        ).split(":")
except requests.exceptions.ConnectTimeout:
    print("Timeout")  # TODO: perform Logging of timeout


for provider in config["providers"]:
    # TODO: add your own token & tld in json files

    ipv4_config: list[dnsV4Config] = []
    ipv6_config: list[dnsV6Config] = []

    for zone in provider["zones"]:

        ipv4_config.append(
            dnsV4Config(
                zone["name"],
                list(
                    map(
                        lambda x: dnsV4ConfigRecord(name=x["name"]),
                        zone["ipv4_records"],
                    )
                ),
            )
        )

        ipv6_config.append(
            dnsV6Config(
                zone["name"],
                list(
                    map(
                        lambda x: dnsV6ConfigRecord(
                            name=x["name"],
                            prefixOffset=x["prefixOffset"],
                            suffix=x["suffix"],
                        ),
                        zone["ipv6_records"],
                    )
                ),
            )
        )

    # ipv6_config: list[dict[str, object]] = provider["ipv6"]["config"]

    provider_config = provider["provider_config"]

    match provider["provider"]:
        case "hetzner":
            providers.hetzner.updateHetznerEntries(
                providerConfig=provider_config,
                dnsV4Config=ipv4_config,
                ipv4Address=ipv4Address,
                dnsV6Config=ipv6_config,
                ipv6Prefix=ipv6Prefix,
                globalConfig=global_config,
            )
