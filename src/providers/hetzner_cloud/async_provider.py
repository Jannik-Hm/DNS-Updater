import asyncio
import json
from types import CoroutineType
from pydantic import BaseModel, ValidationError
from typing import Any
from urllib.parse import quote

import aiohttp

from config.config_models import ProviderConfig
from custom_logging.logger import Logger
from providers import AsyncProvider

from .api_pydantic_models import *


class HetznerCloudProviderConfigConfig(BaseModel):
    api_token: str


class AsyncHetznerCloudProvider(AsyncProvider):
    config: ProviderConfig[HetznerCloudProviderConfigConfig]
    zone_records: dict[str, dict[str, HetznerCloudRRSet]] = {}
    updated_zone_records: dict[str, dict[str, HetznerCloudRRSet]] = {}
    created_zone_records: dict[str, dict[str, CreateHetznerCloudRRSet]] = {}

    def validateConfig(self, config: ProviderConfig[Any]) -> ProviderConfig[Any]:
        return ProviderConfig[HetznerCloudProviderConfigConfig].model_validate(config)

    async def __getZoneRecords(self, zone: str, apiTimeout: aiohttp.ClientTimeout):
        logger = Logger.getDNSUpdaterLogger()
        zone_encoded = quote(zone)
        getRecords = await self.aioSession.get(
            url=f"https://api.hetzner.cloud/v1/zones/{zone_encoded}/rrsets",
            headers={
                "Authorization": f"Bearer {self.config.provider_config.api_token}",
            },
            timeout=apiTimeout,  # wait longer for bigger responses in case of a lot of records
        )
        if getRecords.status >= 400:
            match getRecords.status:
                case 401:
                    logger.error(f"Get Hetzner Records - {getRecords.reason}")
                    return
                case 406:
                    logger.error(f"Get Hetzner Records - {getRecords.reason}")
                    return
                case _:
                    logger.error(
                        f"Get Hetzner Records - Unknown Error Code {getRecords.status}"
                    )
                    return
        try:
            records: HetznerCloudRecords = HetznerCloudRecords.model_validate(
                await getRecords.json()
            )
            for entry in records.rrsets:
                if (entry.type == "A" and not self.globalConfig.disable_v4) or (
                    entry.type == "AAAA" and not self.globalConfig.disable_v6
                ):
                    self.zone_records[str(entry.zone)][entry.type + "-" + entry.name] = entry
        except ValidationError as e:
            logger.error(
                "Hetzner Records Endpoint responded with invalid Response Body",
            )
            raise e

    async def getCurrentDNSConfig(self):
        api_token: str = self.config.provider_config.api_token
        logger = Logger.getDNSUpdaterLogger()

        apiTimeout = aiohttp.ClientTimeout(total=10)
        # TODO: pagination handling
        getZones = await self.aioSession.get(
            url="https://api.hetzner.cloud/v1/zones",
            headers={
                "Authorization": f"Bearer {api_token}",
            },
            timeout=apiTimeout,
        )

        if getZones.status >= 400:
            match getZones.status:
                case 400:
                    logger.error(
                        "Get Hetzner Zones - Pagination selectors are mutually exclusive"
                    )
                case 401:
                    logger.error(f"Get Hetzner Zones - {getZones.reason}")
                    return
                case 406:
                    logger.error(f"Get Hetzner Zones - {getZones.reason}")
                    return
                case _:
                    logger.error(
                        f"Get Hetzner Zones - Unknown Error Code {getZones.status}"
                    )
                    return
        try:
            zones: HetznerCloudZones = HetznerCloudZones.model_validate(
                await getZones.json()
            )
            for entry in zones.zones:
                self.zone_records[str(entry.id)] = {}
                self.zone_ids[entry.name] = str(entry.id)
        except ValidationError as e:
            logger.error(
                f"Hetzner Zones Endpoint responded with invalid Response Body:\n```{(await getZones.text())}```",
            )
            raise e

        # query zone records in parallel
        zone_record_fetch_tasks: list[CoroutineType] = []
        for zone in self.config.zones:
            if not zone.name in self.zone_ids:
                logger.error(
                    f"Get Hetzner Cloud Records for Zone {zone.name} failed: Zone not found in Hetzner Cloud Zones"
                )
                continue
            zone_record_fetch_tasks.append(self.__getZoneRecords(zone.name, apiTimeout))
        await asyncio.gather(*zone_record_fetch_tasks, return_exceptions=False)

    def createDNSRecord(self, type: str, name: str, value: str, zoneName: str):
        if not self.zone_ids[zoneName] in self.created_zone_records:
            self.created_zone_records[self.zone_ids[zoneName]] = {}
        self.created_zone_records[self.zone_ids[zoneName]][f"{type}-{name}"] = (
            CreateHetznerCloudRRSet(
                name=name,
                type=type,
                ttl=self.globalConfig.ttl,
                records=[
                    HetznerCloudRRSetRecord(
                        value=value, comment="Managed by DNS Updater"
                    )
                ],
            )
        )

    def updateDNSRecord(self, type: str, name: str, value: str, zoneName: str):
        temp_record = self.zone_records[self.zone_ids[zoneName]][f"{type}-{name}"]

        if (
            temp_record.records
            == [HetznerCloudRRSetRecord(value=value, comment="Managed by DNS Updater")]
            and temp_record.ttl == self.globalConfig.ttl
        ):
            # skip if record value is unchanged
            return False

        temp_record.records = [
            HetznerCloudRRSetRecord(value=value, comment="Managed by DNS Updater")
        ]
        temp_record.ttl = self.globalConfig.ttl
        if not self.zone_ids[zoneName] in self.updated_zone_records:
            self.updated_zone_records[self.zone_ids[zoneName]] = {}
        self.updated_zone_records[self.zone_ids[zoneName]][
            f"{type}-{name}"
        ] = temp_record

    async def createDNSRecordAPI(
        self,
        zone: str,
        record: CreateHetznerCloudRRSet,
        apiTimeout: aiohttp.ClientTimeout,
    ) -> tuple[str, str | None]:
        zone_encoded = quote(zone)
        createResponse = await self.aioSession.post(
            url=f"https://api.hetzner.cloud/v1/zones/{zone_encoded}/rrsets",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.provider_config.api_token}",
            },
            data=record.model_dump_json(),
            timeout=apiTimeout,
        )

        if createResponse.status >= 400:
            match createResponse.status:
                case 401:
                    return "", f"Create Hetzner Records Error - {createResponse.reason}"
                case 403:
                    return "", f"Create Hetzner Records Error - {createResponse.reason}"
                case 404:
                    return "", f"Create Hetzner Records Error - {createResponse.reason}"
                case 406:
                    return "", f"Create Hetzner Records Error - {createResponse.reason}"
                case 409:
                    return "", f"Create Hetzner Records Error - {createResponse.reason}"
                case 422:
                    return "", "Create Hetzner Records Error - Unprocessable entity"
                case _:
                    return "", f"Undefined Error Code: {createResponse.status}"
        else:
            response = await createResponse.json()
            return json.dumps(response["rrset"]), None

    async def updateDNSRecordTTLAPI(
        self, record: HetznerCloudRRSet, apiTimeout: aiohttp.ClientTimeout
    ) -> tuple[str, str | None]:
        name_encoded = quote(record.name)
        type_encoded = quote(record.type.upper())
        updateTTLResponse = await self.aioSession.post(
            url=f"https://api.hetzner.cloud/v1/zones/{record.zone}/rrsets/{name_encoded}/{type_encoded}/actions/change_ttl",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.provider_config.api_token}",
            },
            data=json.dumps({"ttl": record.ttl}),
            timeout=apiTimeout,
        )

        if updateTTLResponse.status >= 400:
            match updateTTLResponse.status:
                case 401:
                    return (
                        "",
                        f"Update Hetzner Records TTL Error - {updateTTLResponse.reason}",
                    )
                case 403:
                    return (
                        "",
                        f"Update Hetzner Records TTL Error - {updateTTLResponse.reason}",
                    )
                case 404:
                    return (
                        "",
                        f"Update Hetzner Records TTL Error - {updateTTLResponse.reason}",
                    )
                case 406:
                    return (
                        "",
                        f"Update Hetzner Records TTL Error - {updateTTLResponse.reason}",
                    )
                case 409:
                    return (
                        "",
                        f"Update Hetzner Records TTL Error - {updateTTLResponse.reason}",
                    )
                case 422:
                    return "", "Update Hetzner Records TTL Error - Unprocessable entity"
                case _:
                    return (
                        "",
                        f"Update Hetzner Records TTL Undefined Error Code: {updateTTLResponse.status}",
                    )
        else:
            response: dict = await updateTTLResponse.json()
            if response.get("error") is None:
                return (
                    json.dumps(
                        {
                            "type": record.type,
                            "name": record.name,
                            "zone": record.zone,
                            "ttl": record.ttl,
                        }
                    ),
                    None,
                )
            else:
                return "", f"Update Hetzner Records TTL Error - {response["error"]}"

    async def updateDNSRecordValuesAPI(
        self, record: HetznerCloudRRSet, apiTimeout: aiohttp.ClientTimeout
    ) -> tuple[str, str | None]:
        name_encoded = quote(record.name)
        type_encoded = quote(record.type.upper())
        updateValuesResponse = await self.aioSession.post(
            url=f"https://api.hetzner.cloud/v1/zones/{record.zone}/rrsets/{name_encoded}/{type_encoded}/actions/set_records",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.provider_config.api_token}",
            },
            data=json.dumps({"records": [record.model_dump() for record in record.records]}),
            timeout=apiTimeout,
        )

        if updateValuesResponse.status >= 400:
            match updateValuesResponse.status:
                case 401:
                    return (
                        "",
                        f"Update Hetzner Records Values Error - {updateValuesResponse.reason}",
                    )
                case 403:
                    return (
                        "",
                        f"Update Hetzner Records Values Error - {updateValuesResponse.reason}",
                    )
                case 404:
                    return (
                        "",
                        f"Update Hetzner Records Values Error - {updateValuesResponse.reason}",
                    )
                case 406:
                    return (
                        "",
                        f"Update Hetzner Records Values Error - {updateValuesResponse.reason}",
                    )
                case 409:
                    return (
                        "",
                        f"Update Hetzner Records Values Error - {updateValuesResponse.reason}",
                    )
                case 422:
                    return (
                        "",
                        "Update Hetzner Records Values Error - Unprocessable entity",
                    )
                case _:
                    return (
                        "",
                        f"Update Hetzner Records Values Undefined Error Code: {updateValuesResponse.status}",
                    )
        else:
            response: dict = await updateValuesResponse.json()
            if response.get("error") is None:
                return (
                    json.dumps(
                        {
                            "type": record.type,
                            "name": record.name,
                            "zone": record.zone,
                            "values": [record.value for record in record.records],
                        }
                    ),
                    None,
                )
            else:
                return "", f"Update Hetzner Records Values Error - {response["error"]}"

    async def updateDNSConfig(self):
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
                f"These Records would be updated:\n```{json.dumps(
                    [record.model_dump() for record in updated_zone_records]
                )}```"
            )
        elif len(updated_zone_records) > 0:
            update_record_tasks: list[
                CoroutineType[Any, Any, tuple[str, str | None]]
            ] = []
            for zone_id, zone in self.updated_zone_records.items():
                for record in zone.values():
                    if record.ttl != self.globalConfig.ttl:
                        update_record_tasks.append(
                            self.updateDNSRecordTTLAPI(
                                record=record, apiTimeout=apiTimeout
                            )
                        )
                    if (
                        record.records
                        != self.zone_records[zone_id][
                            f"{record.type}-{record.name}"
                        ]
                    ):
                        update_record_tasks.append(
                            self.updateDNSRecordValuesAPI(
                                record=record, apiTimeout=apiTimeout
                            )
                        )
            results = await asyncio.gather(
                *update_record_tasks, return_exceptions=False
            )
            error_list: list[str] = []
            success_list: list[str] = []
            for response in results:
                success = response[0]
                error = response[1]
                if error is not None:
                    error_list.append(error)
                else:
                    success_list.append(success)
            if len(error_list) > 0:
                logger.error("\n".join(error_list))
            else:
                logger.info(
                    f"These Records were updated:\n```{"\n".join(success_list)}```"
                )

        created_zone_records = [
            record
            for zone in self.created_zone_records.values()
            for record in zone.values()
        ]
        if globalConfig.dry_run:
            logger.info(
                f"These Records would be created:\n```{json.dumps([record.model_dump() for record in created_zone_records])}```"
            )
        elif len(created_zone_records) > 0:
            create_record_tasks: list[
                CoroutineType[Any, Any, tuple[str, str | None]]
            ] = []
            for zone_id, zone in self.created_zone_records.items():
                for record in zone.values():
                    create_record_tasks.append(
                        self.createDNSRecordAPI(
                            zone=zone_id, record=record, apiTimeout=apiTimeout
                        )
                    )
            results = await asyncio.gather(
                *create_record_tasks, return_exceptions=False
            )
            error_list: list[str] = []
            success_list: list[str] = []
            for response in results:
                success = response[0]
                error = response[1]
                if error is not None:
                    error_list.append(error)
                else:
                    success_list.append(success)
            if len(error_list) > 0:
                logger.error("\n".join(error_list))
            else:
                logger.info(
                    f"These Records were created:\n```{"\n".join(success_list)}```"
                )
