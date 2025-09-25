import json
from pydantic import BaseModel, ValidationError
from typing import Any

import aiohttp
import asyncio

from config.config_models import ProviderConfig
from custom_logging.logger import Logger
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
        logger = Logger.getDNSUpdaterLogger()
        globalConfig = self.globalConfig

        apiTimeout = aiohttp.ClientTimeout(total=10)

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
                    logger.error(
                        "Get Hetzner Zones - Pagination selectors are mutually exclusive",
                    )
                    return
                case 401:
                    logger.error(
                        f"Get Hetzner Zones - {getZones.reason}",
                    )
                    return
                case 406:
                    logger.error(
                        f"Get Hetzner Zones - {getZones.reason}",
                    )
                    return
        try:
            zones: HetznerZones = HetznerZones.model_validate(await getZones.json())
            for entry in zones.zones:
                self.zone_records[entry.id] = {}
                self.zone_ids[entry.name] = entry.id
        except ValidationError as e:
            logger.error(
                "Hetzner Zones Endpoint responded with invalid Response Body",
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
                    logger.error(
                        f"Get Hetzner Zones - {getRecords.reason}",
                    )
                    return
                case 406:
                    logger.error(
                        f"Get Hetzner Zones - {getRecords.reason}",

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
            logger.error(
                "Hetzner Records Endpoint responded with invalid Response Body",
            )
            raise e

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
        logger = Logger.getDNSUpdaterLogger()
        globalConfig = self.globalConfig

        apiTimeout = aiohttp.ClientTimeout(total=10)

        updated_zone_records = [
            record
            for zone in self.updated_zone_records.values()
            for record in zone.values()
        ]
        if globalConfig.dry_run:
            logger.info(
                "These Records would be updated:\n"
                + "```"
                + json.dumps(
                    [record.model_dump() for record in updated_zone_records]
                )
                + "```",
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
                        logger.error(
                            f"Update A Records Error - {updateResponse.reason}",
                            
                        )
                    case 403:
                        logger.error(
                            f"Update A Records Error - {updateResponse.reason}",
                            
                        )
                    case 406:
                        logger.error(
                            f"Update A Records Error - {updateResponse.reason}",
                            
                        )
                    case 422:
                        logger.error(
                            "Update A Records Error - Unprocessable entity",
                            
                        )
            else:
                logger.info(
                    "These Records were updated:\n"
                    + "```"
                    + json.dumps((await updateResponse.json())["records"])
                    + "```",
                )

        created_zone_records = [
            record
            for zone in self.created_zone_records.values()
            for record in zone.values()
        ]
        if globalConfig.dry_run:
            logger.info(
                "These Records would be created:\n"
                + "```"
                + json.dumps(
                    [record.model_dump() for record in created_zone_records]
                )
                + "```",
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
                        logger.error(
                            f"Update AAAA Records Error - {createResponse.reason}",
                            
                        )
                    case 403:
                        logger.error(
                            f"Update AAAA Records Error - {createResponse.reason}",
                            
                        )
                    case 404:
                        logger.error(
                            f"Update AAAA Records Error - {createResponse.reason}",
                            
                        )
                    case 406:
                        logger.error(
                            f"Update AAAA Records Error - {createResponse.reason}",
                            
                        )
                    case 409:
                        logger.error(
                            f"Update AAAA Records Error - {createResponse.reason}",
                            
                        )
                    case 422:
                        logger.error(
                            "Update AAAA Records Error - Unprocessable entity",
                            
                        )
            else:
                logger.info(
                    "These Records were created:\n"
                    + "```"
                    + json.dumps((await createResponse.json())["records"])
                    + "```",
                )
