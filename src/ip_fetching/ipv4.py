import requests

from config import GlobalConfig
from custom_logging import Logger

from .fail_counter import ipFetchFails


def getCurrentIPv4Address(
    globalConfig: GlobalConfig, consecutive_ip_fails: ipFetchFails
) -> str | None:
    logger = Logger.getDNSUpdaterLogger()
    logger.debug("Getting current IPv4 Address")
    try:
        ipv4Address = requests.get("https://api.ipify.org", timeout=5).text
        consecutive_ip_fails.ipV4Fail = 0
        return ipv4Address
    except requests.exceptions.ConnectTimeout:
        consecutive_ip_fails.ipV4Fail += 1
        if (
            consecutive_ip_fails.ipV4Fail
            > globalConfig.allowed_consecutive_ip_fetch_timeouts
        ):
            logger.error(
                f"Timeout getting current IPv4 Address {consecutive_ip_fails.ipV4Fail} time(s) in a row"
            )
    except requests.exceptions.ConnectionError:
        consecutive_ip_fails.ipV4Fail += 1
        if (
            consecutive_ip_fails.ipV4Fail
            > globalConfig.allowed_consecutive_ip_fetch_timeouts
        ):
            logger.error(
                f"Unable to establish connection {consecutive_ip_fails.ipV4Fail} time(s) in a row getting current IPv4 Address",
            )
