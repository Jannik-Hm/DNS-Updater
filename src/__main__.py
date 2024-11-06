import requests
import ipaddress as ipaddress
import yaml as yaml
import argparse

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
from helper_functions import ipv6, logging

parser = argparse.ArgumentParser()

parser.add_argument("-d", "--dryrun", action='store_true', dest="dryrun", help="perform a dry run, printing changes without executing")
parser.add_argument("-f", "--config-file", dest="config_path", default="dns_config.yaml", help="specify the path to the config file")
parser.add_argument("--disable-ipv4", dest="disable_ipv4", action='store_true', help="disable ipv4 updates")
parser.add_argument("--disable-ipv6", dest="disable_ipv6", action='store_true', help="disable ipv6 updates")

args = parser.parse_args()

config_file = open(args.config_path, "r")
config = yaml.safe_load(config_file)
config_file.close()

global_config: globalConfig = globalConfig(
    ttl=config["global"]["ttl"], prefix_offset=config["global"]["current_prefix_offset"]
)

dryrun: bool = args.dryrun or config["global"]["dry-run"]
disable_ipv4: bool = args.disable_ipv4 or config["global"]["disable-ipv4"]
disable_ipv6: bool = args.disable_ipv6 or config["global"]["disable-ipv6"]

ipv4Address: Optional[str] = None
ipv6Address: Optional[str] = None
ipv6Prefix: Optional[list[str]] = None

logProviders: list[logging.LogProvider] = []

for logProvider in config["global"]["logging"]:
    loglevel: logging.LogLevel = logging.LogLevel.fromString(logProvider["loglevel"])
    match str.lower(logProvider["provider"]):
        case "print":
            logProviders.append(logging.PrintLogger(loglevel=loglevel))
        case "discord":
            logProviders.append(logging.DiscordLogger(webhook_url=logProvider["provider_config"]["webhook_url"],loglevel=loglevel))

logger = logging.Logger(logProviders=logProviders)

if dryrun:
    logger.log(message="This is a dryrun. No Updates will be applied.", loglevel=logging.LogLevel.INFO)
if not disable_ipv4:
    try:
        ipv4Address = requests.get("https://api.ipify.org", timeout=5).text
    except requests.exceptions.ConnectTimeout:
        logger.log(message="Timeout getting current IPv4 Address", loglevel=logging.LogLevel.FATAL)
    except requests.exceptions.ConnectionError:
        logger.log(message="Unable to establish connection getting current IPv4 Address", loglevel=logging.LogLevel.FATAL)
if not disable_ipv6:
    try:
        ipv6Address = requests.get("https://api6.ipify.org", timeout=5).text
        if ipv6Address is not None:
            ipv6Prefix = ipv6.calculateIPv6Address(
                prefix=ipaddress.IPv6Address(ipv6Address).exploded.split(":"),
                prefixOffset="-" + str(global_config.prefix_offset), # negative Offset
                currentAddressOrFixedSuffix="::",
            ).split(":")
    except requests.exceptions.ConnectTimeout:
        logger.log(message="Timeout getting current IPv6 Address", loglevel=logging.LogLevel.FATAL)
    except requests.exceptions.ConnectionError:
        logger.log(message="Unable to establish connection getting current IPv6 Address", loglevel=logging.LogLevel.FATAL)
    except ValueError as e:
        logger.log(message=str(e.args), loglevel=logging.LogLevel.FATAL)

if ipv4Address is not None or ipv6Address is not None:
    for provider in config["providers"]:
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
                    dryrun=dryrun,
                    logger=logger
                )
