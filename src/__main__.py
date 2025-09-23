import requests
import ipaddress as ipaddress
import yaml as yaml
import argparse

from typing import Optional

import providers
from helper_functions import ipv6, logging

from global_objects.config import Config

parser = argparse.ArgumentParser()

parser.add_argument("-d", "--dryrun", action='store_true', dest="dryrun", help="perform a dry run, printing changes without executing")
parser.add_argument("-f", "--config-file", dest="config_path", default="dns_config.yaml", help="specify the path to the config file")
parser.add_argument("--disable-ipv4", dest="disable_ipv4", action='store_true', help="disable ipv4 updates")
parser.add_argument("--disable-ipv6", dest="disable_ipv6", action='store_true', help="disable ipv6 updates")

args = parser.parse_args()

config_file = open(args.config_path, "r")
config_json = yaml.safe_load(config_file)
config_file.close()

# global_config: globalConfig = globalConfig(
#     ttl=config_json["global"]["ttl"], prefix_offset=config_json["global"]["current_prefix_offset"]
# )

config: Config = Config.model_validate(config_json)

dryrun: bool = args.dryrun or config.global_.dry_run
disable_ipv4: bool = args.disable_ipv4 or config.global_.disable_v4
disable_ipv6: bool = args.disable_ipv6 or config.global_.disable_v6

ipv4Address: Optional[str] = None
ipv6Address: Optional[str] = None
ipv6Prefix: Optional[list[str]] = None

logProviders: list[logging.LogProvider] = []

for logProvider in config.global_.logging:
    loglevel: logging.LogLevel = logging.LogLevel.fromString(logProvider.loglevel)
    match str.lower(logProvider.provider):
        case "print":
            logProviders.append(logging.PrintLogger(loglevel=loglevel))
        case "discord":
            if logProvider.provider_config is not None:
                # TODO: validate discord logger config
                logProviders.append(logging.DiscordLogger(webhook_url=logProvider.provider_config["webhook_url"],loglevel=loglevel))

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
                prefixOffset="-" + str(config.global_.current_prefix_offset), # negative Offset
                currentAddressOrFixedSuffix="::",
            ).split(":")
    except requests.exceptions.ConnectTimeout:
        logger.log(message="Timeout getting current IPv6 Address", loglevel=logging.LogLevel.FATAL)
    except requests.exceptions.ConnectionError:
        logger.log(message="Unable to establish connection getting current IPv6 Address", loglevel=logging.LogLevel.FATAL)
    except ValueError as e:
        logger.log(message=str(e.args), loglevel=logging.LogLevel.FATAL)

if ipv4Address is not None or ipv6Address is not None:
    for providerConfig in config.providers:
        provider: providers.Provider = providers.providerMap[providerConfig.provider.upper()](providerConfig=providerConfig, globalConfig=config.global_, logger=logger)

        provider.getCurrentDNSConfig()
        provider.updateDNSRecordsLocally(currentIPv4=ipv4Address, currentIPv6Prefix=ipv6Address.split(":") if ipv6Address else None)
        provider.updateDNSConfig()
