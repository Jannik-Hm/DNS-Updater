import asyncio
from typing import Type

from config import Config
from ip_fetching import getCurrentIPv4Address, getCurrentIPv6Prefix, ipFetchFails
from custom_logging import Logger

from .abstract import AsyncProvider
from .hetzner import AsyncHetznerProvider


providerMap: dict[str, Type[AsyncProvider]] = {
    "HETZNER": AsyncHetznerProvider,
}


async def providerFetchAndUpdate(
    config: Config,
    provider: AsyncProvider,
    ipv4Address: str | None,
    ipv6Address: list[str] | None,
):
    logger = Logger.getDNSUpdaterLogger()
    allowed_fails = (
        provider.config.allowed_consecutive_timeouts
        or config.global_.allowed_consecutive_provider_timeouts
    )
    try:
        await provider.getCurrentDNSConfig()
        provider.consecutive_fail_counter.fetchFail = 0
    except asyncio.TimeoutError as e:
        provider.consecutive_fail_counter.fetchFail += 1
        if provider.consecutive_fail_counter.fetchFail > allowed_fails:
            logger.error(
                f"{type(provider).__name__} Zone Timeout fetching DNS Records {provider.consecutive_fail_counter.fetchFail} time(s) in a row",
            )
        else:
            logger.debug(
                f"{type(provider).__name__} Zone Timeout fetching DNS Records within allowed limit",
            )
        return
    provider.updateDNSRecordsLocally(
        currentIPv4=ipv4Address,
        currentIPv6Prefix=ipv6Address,
    )
    try:
        await provider.updateDNSConfig()
        provider.consecutive_fail_counter.updateFail = 0
    except asyncio.TimeoutError as e:
        provider.consecutive_fail_counter.updateFail += 1
        if provider.consecutive_fail_counter.updateFail > allowed_fails:
            logger.error(
                f"{type(provider).__name__} Zone Timeout updating DNS Records {provider.consecutive_fail_counter.updateFail} time(s) in a row",
            )
        else:
            logger.debug(
                f"{type(provider).__name__} Zone Timeout updating DNS Records within allowed limit",
            )
    # clear attributes before next loop iteration
    provider.updated_zone_records = {}
    provider.created_zone_records = {}
    provider.zone_ids = {}
    provider.zone_records = {}


async def run_all_providers(
    providers: list[AsyncProvider], config: Config, consecutive_ip_fails: ipFetchFails
):
    ipv4Address = getCurrentIPv4Address(
        globalConfig=config.global_, consecutive_ip_fails=consecutive_ip_fails
    )
    ipv6Address = getCurrentIPv6Prefix(
        config=config, consecutive_ip_fails=consecutive_ip_fails
    )

    if ipv4Address is not None or ipv6Address is not None:
        # schedule all providers in parallel as tasks
        tasks = [
            providerFetchAndUpdate(
                config=config,
                ipv4Address=ipv4Address,
                ipv6Address=ipv6Address,
                provider=provider,
            )
            for provider in providers
        ]
        # wait for all to complete (gather returns their results or raises if one fails)
        await asyncio.gather(*tasks, return_exceptions=False)
