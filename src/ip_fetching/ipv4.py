import requests

from config import GlobalConfig
from helper_functions import logging

from .fail_counter import ipFetchFails

def getCurrentIPv4Address(globalConfig: GlobalConfig, logger: logging.Logger, consecutive_ip_fails: ipFetchFails) -> str | None:
    logger.log("Getting current IPv4 Address", loglevel=logging.LogLevel.DEBUG)
    try:
        ipv4Address = requests.get("https://api.ipify.org", timeout=5).text
        consecutive_ip_fails.ipV4Fail = 0
        return ipv4Address
    except requests.exceptions.ConnectTimeout:
        consecutive_ip_fails.ipV4Fail += 1
        if consecutive_ip_fails.ipV4Fail > globalConfig.allowed_consecutive_ip_fetch_timeouts:
            logger.log(
                message=f"Timeout getting current IPv4 Address {consecutive_ip_fails.ipV4Fail} time(s) in a row",
                loglevel=logging.LogLevel.FATAL,
            )
    except requests.exceptions.ConnectionError:
        consecutive_ip_fails.ipV4Fail += 1
        if consecutive_ip_fails.ipV4Fail > globalConfig.allowed_consecutive_ip_fetch_timeouts:
            logger.log(
                message=f"Unable to establish connection {consecutive_ip_fails.ipV4Fail} time(s) in a row getting current IPv4 Address",
                loglevel=logging.LogLevel.FATAL,
            )
