import asyncio
from typing import Any, Type

import aiohttp

from config import Config, ProviderConfig, GlobalConfig
from ip_fetching import getCurrentIPv4Address, getCurrentIPv6Prefix
from helper_functions import logging

from .abstract import Provider, AsyncProvider
from .hetzner import HetznerProvider, AsyncHetznerProvider


providerMap: dict[str, Type[AsyncProvider]] = {
    "HETZNER": AsyncHetznerProvider,
}


async def providerFetchAndUpdate(
    provider: AsyncProvider, ipv4Address: str | None, ipv6Address: list[str] | None
):
    await provider.getCurrentDNSConfig()
    provider.updateDNSRecordsLocally(
        currentIPv4=ipv4Address,
        currentIPv6Prefix=ipv6Address,
    )
    await provider.updateDNSConfig()


async def run_all_providers(
    providers: list[AsyncProvider], config: Config, logger: logging.Logger
):
    ipv4Address = getCurrentIPv4Address(logger=logger)
    ipv6Address = getCurrentIPv6Prefix(config=config, logger=logger)

    if ipv4Address is not None or ipv6Address is not None:
        # schedule all providers in parallel as tasks
        tasks = [
            providerFetchAndUpdate(
                ipv4Address=ipv4Address,
                ipv6Address=ipv6Address,
                provider=provider,
            )
            for provider in providers
        ]
        # wait for all to complete (gather returns their results or raises if one fails)
        await asyncio.gather(*tasks, return_exceptions=False)
