from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any
import aiohttp

from config.config_models import ProviderConfig, GlobalConfig
from helper_functions import logging
from ip_fetching import calculateIPv6Address

# TODO: allow consecutive fails (for timeout cases)


class Record(BaseModel):
    ttl: int | None = None
    name: str
    value: str
    type: str


class Provider(ABC):
    config: ProviderConfig[Any]
    globalConfig: GlobalConfig
    logger: logging.Logger
    zone_records: dict[str, dict[str, Record]] = (
        {}
    )  # dict[zone_id, dict[type-record_name, Record]]
    zone_ids: dict[str, str] = {}
    updated_zone_records: dict[str, dict[str, Record]] = {}
    created_zone_records: dict[str, dict[str, Record]] = {}

    def __init__(
        self,
        providerConfig: ProviderConfig[Any],
        globalConfig: GlobalConfig,
        logger: logging.Logger,
    ):
        self.config = self.validateConfig(providerConfig)
        self.globalConfig = globalConfig
        self.logger = logger

    @abstractmethod
    def validateConfig(self, config: ProviderConfig[Any]) -> ProviderConfig[Any]:
        pass
        # call ProviderConfig[Specific Config Config].model_validate(self.config)

    @abstractmethod
    def getCurrentDNSConfig(self):
        pass

    def createDNSRecord(self, type: str, name: str, value: str, zoneName: str):
        self.created_zone_records[self.zone_ids[zoneName]][f"{type}-{name}"] = Record(
            ttl=60, name=name, value=value, type=type
        )

    def _updateSingleDNSRecordLocally(
        self, zoneName: str, recordName: str, type: str, value: str
    ) -> bool:
        if f"{type}-{recordName}" in self.zone_records[self.zone_ids[zoneName]]:
            temp_record = self.zone_records[self.zone_ids[zoneName]][
                f"{type}-{recordName}"
            ]

            if temp_record.value == value and temp_record.ttl == self.globalConfig.ttl:
                # skip if record value is unchanged
                return False

            temp_record.value = value
            temp_record.ttl = self.globalConfig.ttl
            if not self.zone_ids[zoneName] in self.updated_zone_records:
                self.updated_zone_records[self.zone_ids[zoneName]] = {}
            self.updated_zone_records[self.zone_ids[zoneName]][
                f"{type}-{recordName}"
            ] = temp_record
        else:
            self.createDNSRecord(
                type=type,
                name=recordName,
                value=value,
                zoneName=zoneName,
            )
        return True

    def updateDNSRecordsLocally(
        self, currentIPv4: str | None, currentIPv6Prefix: list[str] | None
    ):
        for zone in self.config.zones:
            if not self.globalConfig.disable_v4 and currentIPv4:
                for record in zone.ipv4_records:
                    self._updateSingleDNSRecordLocally(
                        zoneName=zone.name,
                        recordName=record.name,
                        type="A",
                        value=currentIPv4,
                    )
            if not self.globalConfig.disable_v6 and currentIPv6Prefix:
                for record in zone.ipv6_records:
                    self._updateSingleDNSRecordLocally(
                        zoneName=zone.name,
                        recordName=record.name,
                        type="AAAA",
                        value=calculateIPv6Address(
                            prefix=currentIPv6Prefix,
                            prefixOffset=record.prefixOffset,
                            currentAddressOrFixedSuffix=record.suffix,
                        ),
                    )

    @abstractmethod
    def updateDNSConfig(self):
        pass


class AsyncProvider(Provider):
    aioSession: aiohttp.ClientSession

    def __init__(
        self,
        providerConfig: ProviderConfig[Any],
        globalConfig: GlobalConfig,
        logger: logging.Logger,
    ):
        self.aioSession = aiohttp.ClientSession()
        super().__init__(providerConfig, globalConfig, logger)

    @abstractmethod
    async def getCurrentDNSConfig(self):
        pass

    @abstractmethod
    async def updateDNSConfig(self):
        pass
