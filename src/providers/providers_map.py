import asyncio
from typing import Any, Type

import aiohttp

from config import Config, ProviderConfig, GlobalConfig
from ip_fetching import getCurrentIPv4Address, getCurrentIPv6Prefix, ipFetchFails
from helper_functions import logging

from .abstract import Provider, AsyncProvider
from .hetzner import HetznerProvider, AsyncHetznerProvider


providerMap: dict[str, Type[AsyncProvider]] = {
    "HETZNER": AsyncHetznerProvider,
}


async def providerFetchAndUpdate(
    config: Config, provider: AsyncProvider, ipv4Address: str | None, ipv6Address: list[str] | None
):
    allowed_fails = provider.config.allowed_consecutive_timeouts or config.global_.allowed_consecutive_provider_timeouts
    try:
        await provider.getCurrentDNSConfig()
        provider.consecutive_fail_counter.fetchFail = 0
    except asyncio.TimeoutError as e:
        provider.consecutive_fail_counter.fetchFail += 1
        if provider.consecutive_fail_counter.fetchFail > allowed_fails:
            provider.logger.log(
                message=f"{type(provider).__name__} Zone Timeout fetching DNS Records {provider.consecutive_fail_counter.fetchFail} time(s) in a row",
                loglevel=logging.LogLevel.FATAL,
            )
        else:
            provider.logger.log(
                message=f"{type(provider)} Zone Timeout fetching DNS Records within allowed limit",
                loglevel=logging.LogLevel.DEBUG
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
            provider.logger.log(
                message=f"{type(provider)} Zone Timeout updating DNS Records {provider.consecutive_fail_counter.updateFail} time(s) in a row",
                loglevel=logging.LogLevel.FATAL,
            )
        else:
            provider.logger.log(
                message=f"{type(provider)} Zone Timeout updating DNS Records within allowed limit",
                loglevel=logging.LogLevel.DEBUG
            )


async def run_all_providers(
    providers: list[AsyncProvider], config: Config, logger: logging.Logger, consecutive_ip_fails: ipFetchFails
):
    ipv4Address = getCurrentIPv4Address(globalConfig=config.global_, logger=logger, consecutive_ip_fails=consecutive_ip_fails)
    ipv6Address = getCurrentIPv6Prefix(config=config, logger=logger, consecutive_ip_fails=consecutive_ip_fails)

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
