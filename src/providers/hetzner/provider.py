import json
from pydantic import BaseModel, ValidationError
from typing import Any

import requests

from helper_functions import logging
from global_objects.config import GlobalConfig, ProviderConfig
from providers import Provider

from .api_pydantic_models import *


class HetznerProviderConfigConfig(BaseModel):
    api_token: str


class HetznerProvider(Provider):
    config: ProviderConfig[HetznerProviderConfigConfig]
    zone_records: dict[str, dict[str, HetznerRecord]] = {}
    updated_zone_records: dict[str, dict[str, HetznerRecord]] = {}
    created_zone_records: dict[str, dict[str, HetznerRecord]] = {}

    def validateConfig(self, config: ProviderConfig[Any]) -> ProviderConfig[Any]:
        return ProviderConfig[HetznerProviderConfigConfig].model_validate(config)

    def getCurrentDNSConfig(self):
        api_token: str = self.config.provider_config.api_token
        logger = self.logger
        globalConfig = self.globalConfig

        try:

            getZones = requests.get(
                url="https://dns.hetzner.com/api/v1/zones",
                headers={
                    "Auth-API-Token": api_token,
                },
                timeout=10,
            )

            if getZones.status_code != 200:
                match getZones.status_code:
                    case 400:
                        logger.log(
                            message="Get Hetzner Zones - Pagination selectors are mutually exclusive",
                            loglevel=logging.LogLevel.FATAL,
                        )
                        return
                    case 401:
                        logger.log(
                            message="Get Hetzner Zones - " + getZones.reason,
                            loglevel=logging.LogLevel.FATAL,
                        )
                        return
                    case 406:
                        logger.log(
                            message="Get Hetzner Zones - " + getZones.reason,
                            loglevel=logging.LogLevel.FATAL,
                        )
                        return
            try:
                zones: HetznerZones = HetznerZones.model_validate(getZones.json())
                for entry in zones.zones:
                    self.zone_records[entry.id] = {}
                    self.zone_ids[entry.name] = entry.id
            except ValidationError as e:
                logger.log(
                    message="Hetzner Zones Endpoint responded with invalid Response Body",
                    loglevel=logging.LogLevel.ERROR,
                )
                raise e

            getRecords = requests.get(
                url="https://dns.hetzner.com/api/v1/records",
                headers={
                    "Auth-API-Token": api_token,
                },
                timeout=10,  # wait longer for bigger responses in case of a lot of records
            )
            if getRecords.status_code != 200:
                match getRecords.status_code:
                    case 401:
                        logger.log(
                            message="Get Hetzner Records - " + getRecords.reason,
                            loglevel=logging.LogLevel.FATAL,
                        )
                        return
                    case 406:
                        logger.log(
                            message="Get Hetzner Records - " + getRecords.reason,
                            loglevel=logging.LogLevel.FATAL,
                        )
                        return
            try:
                records: HetznerRecords = HetznerRecords.model_validate(
                    getRecords.json()
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
        except requests.exceptions.Timeout as e:
            logger.log(
                message=f"Hetzner Zone Timeout during calling {e.request.url if e.request is not None else ''}",
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

    def updateDNSConfig(self):
        api_token: str = self.config.provider_config.api_token
        logger = self.logger
        globalConfig = self.globalConfig

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
                    + json.dumps([record.model_dump() for record in updated_zone_records])
                    + "```",
                    loglevel=logging.LogLevel.INFO,
                )
            elif len(updated_zone_records) > 0:
                updateResponse = requests.put(
                    url="https://dns.hetzner.com/api/v1/records/bulk",
                    headers={
                        "Content-Type": "application/json",
                        "Auth-API-Token": api_token,
                    },
                    data=json.dumps({"records": [record.model_dump() for record in updated_zone_records]}),
                    timeout=10,
                )

                if updateResponse.status_code != 200:
                    match updateResponse.status_code:
                        case 401:
                            logger.log(
                                message="Update A Records Error - "
                                + updateResponse.reason,
                                loglevel=logging.LogLevel.FATAL,
                            )
                        case 403:
                            logger.log(
                                message="Update A Records Error - "
                                + updateResponse.reason,
                                loglevel=logging.LogLevel.FATAL,
                            )
                        case 406:
                            logger.log(
                                message="Update A Records Error - "
                                + updateResponse.reason,
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
                        + json.dumps(updateResponse.json()["records"])
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
                    + json.dumps([record.model_dump() for record in created_zone_records])
                    + "```",
                    loglevel=logging.LogLevel.INFO,
                )
            elif len(created_zone_records) > 0:
                createResponse = requests.post(
                    url="https://dns.hetzner.com/api/v1/records/bulk",
                    headers={
                        "Content-Type": "application/json",
                        "Auth-API-Token": api_token,
                    },
                    data=json.dumps({"records": [record.model_dump() for record in created_zone_records]}),
                    timeout=10,
                )

                if createResponse.status_code != 200:
                    match createResponse.status_code:
                        case 401:
                            logger.log(
                                message="Update AAAA Records Error - "
                                + createResponse.reason,
                                loglevel=logging.LogLevel.FATAL,
                            )
                        case 403:
                            logger.log(
                                message="Update AAAA Records Error - "
                                + createResponse.reason,
                                loglevel=logging.LogLevel.FATAL,
                            )
                        case 404:
                            logger.log(
                                message="Update AAAA Records Error - "
                                + createResponse.reason,
                                loglevel=logging.LogLevel.FATAL,
                            )
                        case 406:
                            logger.log(
                                message="Update AAAA Records Error - "
                                + createResponse.reason,
                                loglevel=logging.LogLevel.FATAL,
                            )
                        case 409:
                            logger.log(
                                message="Update AAAA Records Error - "
                                + createResponse.reason,
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
                        + json.dumps(createResponse.json()["records"])
                        + "```",
                        loglevel=logging.LogLevel.INFO,
                    )

        except requests.exceptions.ConnectionError as e:
            logger.log(
                message=f"Hetzner Zone Timeout during calling {e.request.url if e.request is not None else ''}",
                loglevel=logging.LogLevel.FATAL,
            )
