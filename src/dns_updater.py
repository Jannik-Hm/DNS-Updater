import ipaddress as ipaddress
from pydantic import BaseModel
import yaml as yaml
import os

import asyncio
import signal
import aiocron

import providers
from custom_logging import Logger

from config import Config, load_config
from ip_fetching import ipFetchFails

config_location = os.getenv("CONFIG_PATH", "/etc/dns_updater/config.yaml")

print("[INFO]: Loading Config from file")

config: Config = load_config(config_location)

logger = Logger.initLoggerHandlers(config=config.global_)

logger.info("Configured Loggers")

if config.global_.dry_run:
    logger.info("This is a dryrun. No Updates will be applied.")


async def shutdown(
    signal, loop: asyncio.AbstractEventLoop, providerList: list[providers.AsyncProvider]
):
    logger.info(f"Received exit signal {signal.name}…")
    # if you have any shared resources, clean up, cancel tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for t in tasks:
        t.cancel()
    logger.info("Cancelling outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Closing all open aiohttp Sessions")
    for provider in providerList:
        await provider.aioSession.close()
    loop.stop()


async def initProviders() -> list[providers.AsyncProvider]:
    return [
        providers.providerMap[providerConfig.provider.upper()](
            providerConfig=providerConfig,
            globalConfig=config.global_,
        )
        for providerConfig in config.providers
    ]


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    print("Initialising DNS Providers...")

    providerList: list[providers.AsyncProvider] = loop.run_until_complete(
        initProviders()
    )

    # Hook signals for graceful shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, lambda s=sig: asyncio.create_task(shutdown(s, loop, providerList))
        )

    print("Starting Cron Job...")

    consecutive_ip_fails = ipFetchFails()

    # Schedule the cron job every minute
    cron_job = aiocron.crontab(
        config.global_.cron,
        func=lambda: providers.run_all_providers(
            providers=providerList,
            config=config,
            consecutive_ip_fails=consecutive_ip_fails,
        ),
        start=True,
    )

    try:
        # Keep loop running
        loop.run_forever()
    finally:
        loop.close()


if __name__ == "__main__":
    main()
