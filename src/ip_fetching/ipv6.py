import requests
import ipaddress as ipaddress

from config import Config
from custom_logging import Logger

from .fail_counter import ipFetchFails


def calculateIPv6Address(
    prefix: list[str], prefixOffset: str, currentAddressOrFixedSuffix: str
) -> str:
    prefix_int = int("".join(prefix[:4]), 16)
    prefix_id_int = int(prefixOffset, 10)
    if f"{(prefix_int + prefix_id_int):016x}".__len__() > 16:
        raise ValueError(
            f"The generated prefix for base prefix {':'.join(prefix[:4])} and prefixOffset {prefixOffset} is overflowing. Please check your config."
        )
    new_prefix = f"{(prefix_int + prefix_id_int) & 0xFFFFFFFFFFFFFFFF:016x}"
    return ipaddress.IPv6Address(
        ":".join(new_prefix[i : i + 4] for i in range(0, len(new_prefix), 4))
        + ":"
        + ":".join(
            ipaddress.IPv6Address(currentAddressOrFixedSuffix).exploded.split(sep=":")[
                -4:
            ]
        )
    ).compressed


def getCurrentIPv6Prefix(
    config: Config, consecutive_ip_fails: ipFetchFails
) -> list[str] | None:
    logger = Logger.getDNSUpdaterLogger()
    logger.debug("Getting current IPv6 Address")
    try:
        ipv6Address = requests.get("https://api6.ipify.org", timeout=5).text
        if ipv6Address is not None:
            consecutive_ip_fails.ipV6Fail = 0
            ipv6Prefix = calculateIPv6Address(
                prefix=ipaddress.IPv6Address(ipv6Address).exploded.split(":"),
                prefixOffset="-"
                + str(config.global_.current_prefix_offset),  # negative Offset
                currentAddressOrFixedSuffix="::",
            ).split(":")
            return ipv6Prefix
    except requests.exceptions.ConnectTimeout:
        consecutive_ip_fails.ipV6Fail += 1
        if (
            consecutive_ip_fails.ipV6Fail
            > config.global_.allowed_consecutive_ip_fetch_timeouts
        ):
            logger.error(
                f"Timeout getting current IPv6 Address {consecutive_ip_fails.ipV6Fail} time(s) in a row"
            )
    except requests.exceptions.ConnectionError:
        consecutive_ip_fails.ipV6Fail += 1
        if (
            consecutive_ip_fails.ipV6Fail
            > config.global_.allowed_consecutive_ip_fetch_timeouts
        ):
            logger.error(
                f"Unable to establish connection {consecutive_ip_fails.ipV6Fail} time(s) in a row getting current IPv6 Address",
            )
    except ValueError as e:
        consecutive_ip_fails.ipV6Fail += 1
        if (
            consecutive_ip_fails.ipV6Fail
            > config.global_.allowed_consecutive_ip_fetch_timeouts
        ):
            logger.error(str(e.args))
