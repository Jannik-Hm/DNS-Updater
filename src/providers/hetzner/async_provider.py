import json
from pydantic import BaseModel, ValidationError
from typing import Any

import aiohttp
import asyncio

from helper_functions import logging
from config.config_models import ProviderConfig
from providers import AsyncProvider

from .api_pydantic_models import *


class HetznerProviderConfigConfig(BaseModel):
    api_token: str


class AsyncHetznerProvider(AsyncProvider):
    config: ProviderConfig[HetznerProviderConfigConfig]
    zone_records: dict[str, dict[str, HetznerRecord]] = {}
    updated_zone_records: dict[str, dict[str, HetznerRecord]] = {}
    created_zone_records: dict[str, dict[str, HetznerRecord]] = {}

    def validateConfig(self, config: ProviderConfig[Any]) -> ProviderConfig[Any]:
        return ProviderConfig[HetznerProviderConfigConfig].model_validate(config)

    async def getCurrentDNSConfig(self):
        api_token: str = self.config.provider_config.api_token
        logger = self.logger
        globalConfig = self.globalConfig

        apiTimeout = aiohttp.ClientTimeout(total=10)

        try:

            getZones = await self.aioSession.get(
                url="https://dns.hetzner.com/api/v1/zones",
                headers={
                    "Auth-API-Token": api_token,
                },
                timeout=apiTimeout,
            )

            if getZones.status != 200:
                match getZones.status:
                    case 400:
                        logger.log(
                            message="Get Hetzner Zones - Pagination selectors are mutually exclusive",
                            loglevel=logging.LogLevel.FATAL,
                        )
                        return
                    case 401:
                        logger.log(
                            message=f"Get Hetzner Zones - {getZones.reason}",
                            loglevel=logging.LogLevel.FATAL,
                        )
                        return
                    case 406:
                        logger.log(
                            message=f"Get Hetzner Zones - {getZones.reason}",
                            loglevel=logging.LogLevel.FATAL,
                        )
                        return
            try:
                zones: HetznerZones = HetznerZones.model_validate(await getZones.json())
                for entry in zones.zones:
                    self.zone_records[entry.id] = {}
                    self.zone_ids[entry.name] = entry.id
            except ValidationError as e:
                logger.log(
                    message="Hetzner Zones Endpoint responded with invalid Response Body",
                    loglevel=logging.LogLevel.ERROR,
                )
                raise e

            getRecords = await self.aioSession.get(
                url="https://dns.hetzner.com/api/v1/records",
                headers={
                    "Auth-API-Token": api_token,
                },
                timeout=apiTimeout,  # wait longer for bigger responses in case of a lot of records
            )
            if getRecords.status != 200:
                match getRecords.status:
                    case 401:
                        logger.log(
                            message=f"Get Hetzner Zones - {getRecords.reason}",
                            loglevel=logging.LogLevel.FATAL,
                        )
                        return
                    case 406:
                        logger.log(
                            message=f"Get Hetzner Zones - {getRecords.reason}",
                            loglevel=logging.LogLevel.FATAL,
                        )
                        return
            try:
                records: HetznerRecords = HetznerRecords.model_validate(
                    await getRecords.json()
                )
                for entry in records.records:
                    if (entry.type == "A" and not globalConfig.disable_v4) or (
                        entry.type == "AAAA" and not globalConfig.disable_v6
                    ):
                        self.zone_records[entry.zone_id][
                            entry.type + "-" + entry.name
                        ] = entry
            except ValidationError as e:
                logger.log(
                    message="Hetzner Records Endpoint responded with invalid Response Body",
                    loglevel=logging.LogLevel.ERROR,
                )
                raise e
        except asyncio.TimeoutError as e:
            logger.log(
                message=f"Hetzner Zone Timeout getting current DNS Config",
                loglevel=logging.LogLevel.FATAL,
            )

    def createDNSRecord(self, type: str, name: str, value: str, zoneName: str):
        if not self.zone_ids[zoneName] in self.created_zone_records:
            self.created_zone_records[self.zone_ids[zoneName]] = {}
        self.created_zone_records[self.zone_ids[zoneName]][f"{type}-{name}"] = (
            HetznerRecord(
                ttl=60,
                name=name,
                value=value,
                type=type,
                zone_id=self.zone_ids[zoneName],
            )
        )

    async def updateDNSConfig(self):
        api_token: str = self.config.provider_config.api_token
        logger = self.logger
        globalConfig = self.globalConfig

        apiTimeout = aiohttp.ClientTimeout(total=10)

        try:

            updated_zone_records = [
                record
                for zone in self.updated_zone_records.values()
                for record in zone.values()
            ]
            if globalConfig.dry_run:
                logger.log(
                    message="These Records would be updated:\n"
                    + "```"
                    + json.dumps(
                        [record.model_dump() for record in updated_zone_records]
                    )
                    + "```",
                    loglevel=logging.LogLevel.INFO,
                )
            elif len(updated_zone_records) > 0:
                updateResponse = await self.aioSession.put(
                    url="https://dns.hetzner.com/api/v1/records/bulk",
                    headers={
                        "Content-Type": "application/json",
                        "Auth-API-Token": api_token,
                    },
                    data=json.dumps(
                        {
                            "records": [
                                record.model_dump() for record in updated_zone_records
                            ]
                        }
                    ),
                    timeout=apiTimeout,
                )

                if updateResponse.status != 200:
                    match updateResponse.status:
                        case 401:
                            logger.log(
                                message=f"Update A Records Error - {updateResponse.reason}",
                                loglevel=logging.LogLevel.FATAL,
                            )
                        case 403:
                            logger.log(
                                message=f"Update A Records Error - {updateResponse.reason}",
                                loglevel=logging.LogLevel.FATAL,
                            )
                        case 406:
                            logger.log(
                                message=f"Update A Records Error - {updateResponse.reason}",
                                loglevel=logging.LogLevel.FATAL,
                            )
                        case 422:
                            logger.log(
                                message="Update A Records Error - Unprocessable entity",
                                loglevel=logging.LogLevel.FATAL,
                            )
                else:
                    logger.log(
                        message="These Records were updated:\n"
                        + "```"
                        + json.dumps((await updateResponse.json())["records"])
                        + "```",
                        loglevel=logging.LogLevel.INFO,
                    )

            created_zone_records = [
                record
                for zone in self.created_zone_records.values()
                for record in zone.values()
            ]
            if globalConfig.dry_run:
                logger.log(
                    message="These Records would be created:\n"
                    + "```"
                    + json.dumps(
                        [record.model_dump() for record in created_zone_records]
                    )
                    + "```",
                    loglevel=logging.LogLevel.INFO,
                )
            elif len(created_zone_records) > 0:
                createResponse = await self.aioSession.post(
                    url="https://dns.hetzner.com/api/v1/records/bulk",
                    headers={
                        "Content-Type": "application/json",
                        "Auth-API-Token": api_token,
                    },
                    data=json.dumps(
                        {
                            "records": [
                                record.model_dump() for record in created_zone_records
                            ]
                        }
                    ),
                    timeout=apiTimeout,
                )

                if createResponse.status != 200:
                    match createResponse.status:
                        case 401:
                            logger.log(
                                message=f"Update AAAA Records Error - {createResponse.reason}",
                                loglevel=logging.LogLevel.FATAL,
                            )
                        case 403:
                            logger.log(
                                message=f"Update AAAA Records Error - {createResponse.reason}",
                                loglevel=logging.LogLevel.FATAL,
                            )
                        case 404:
                            logger.log(
                                message=f"Update AAAA Records Error - {createResponse.reason}",
                                loglevel=logging.LogLevel.FATAL,
                            )
                        case 406:
                            logger.log(
                                message=f"Update AAAA Records Error - {createResponse.reason}",
                                loglevel=logging.LogLevel.FATAL,
                            )
                        case 409:
                            logger.log(
                                message=f"Update AAAA Records Error - {createResponse.reason}",
                                loglevel=logging.LogLevel.FATAL,
                            )
                        case 422:
                            logger.log(
                                message="Update AAAA Records Error - Unprocessable entity",
                                loglevel=logging.LogLevel.FATAL,
                            )
                else:
                    logger.log(
                        message="These Records were created:\n"
                        + "```"
                        + json.dumps((await createResponse.json())["records"])
                        + "```",
                        loglevel=logging.LogLevel.INFO,
                    )

        except asyncio.TimeoutError as e:
            logger.log(
                message=f"Hetzner Zone Timeout updating DNS Records",
                loglevel=logging.LogLevel.FATAL,
            )
