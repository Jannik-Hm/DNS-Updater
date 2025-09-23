import requests

from helper_functions import logging

def getCurrentIPv4Address(logger: logging.Logger) -> str | None:
    logger.log("Getting current IPv4 Address", loglevel=logging.LogLevel.DEBUG)
    try:
        ipv4Address = requests.get("https://api.ipify.org", timeout=5).text
        return ipv4Address
    except requests.exceptions.ConnectTimeout:
        logger.log(
            message="Timeout getting current IPv4 Address",
            loglevel=logging.LogLevel.FATAL,
        )
    except requests.exceptions.ConnectionError:
        logger.log(
            message="Unable to establish connection getting current IPv4 Address",
            loglevel=logging.LogLevel.FATAL,
        )
