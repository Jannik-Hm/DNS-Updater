import ipaddress as ipaddress
from pydantic import BaseModel
import yaml as yaml
import os

import asyncio
import signal
import aiocron

import providers
from helper_functions import logging

from config import Config, load_config
from ip_fetching import ipFetchFails

config_location = os.getenv("CONFIG_PATH", "/etc/dns_updater/config.yaml")

print("[INFO]: Loading Config from file")

config: Config = load_config(config_location)

# TODO: switch to logging lib?

logProviders: list[logging.LogProvider] = []

for logProvider in config.global_.logging:
    loglevel: logging.LogLevel = logging.LogLevel.fromString(logProvider.loglevel)
    match str.lower(logProvider.provider):
        case "print":
            logProviders.append(logging.PrintLogger(loglevel=loglevel))
        case "discord":
            if logProvider.provider_config is not None:
                # TODO: validate discord logger config
                logProviders.append(
                    logging.DiscordLogger(
                        webhook_url=logProvider.provider_config["webhook_url"],
                        loglevel=loglevel,
                    )
                )

logger = logging.Logger(logProviders=logProviders)

logger.log(message="Configured Loggers", loglevel=logging.LogLevel.INFO)

if config.global_.dry_run:
    logger.log(
        message="This is a dryrun. No Updates will be applied.",
        loglevel=logging.LogLevel.INFO,
    )


async def shutdown(signal, loop: asyncio.AbstractEventLoop, providerList: list[providers.AsyncProvider]):
    logger.log(f"Received exit signal {signal.name}…", logging.LogLevel.INFO)
    # if you have any shared resources, clean up, cancel tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for t in tasks:
        t.cancel()
    logger.log("Cancelling outstanding tasks", logging.LogLevel.INFO)
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.log("Closing all open aiohttp Sessions", logging.LogLevel.INFO)
    for provider in providerList:
        await provider.aioSession.close()
    loop.stop()


async def initProviders() -> list[providers.AsyncProvider]:
    return [
        providers.providerMap[providerConfig.provider.upper()](
            providerConfig=providerConfig,
            globalConfig=config.global_,
            logger=logger,
        )
        for providerConfig in config.providers
    ]


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    print("Initialising DNS Providers...")

    providerList: list[providers.AsyncProvider] = loop.run_until_complete(initProviders())

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
            providers=providerList, config=config, logger=logger, consecutive_ip_fails=consecutive_ip_fails
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
