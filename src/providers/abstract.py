from abc import ABC, abstractmethod
from pydantic import BaseModel, ValidationError
from typing import Any
import aiohttp

from config import ProviderConfig, GlobalConfig, handleValidationError
from ip_fetching import calculateIPv6Address
from custom_logging import Logger


class Record(BaseModel):
    ttl: int | None = None
    name: str
    value: str
    type: str


class ProviderFailCounter(BaseModel):
    fetchFail: int = 0
    updateFail: int = 0


class AsyncProvider(ABC):
    aioSession: aiohttp.ClientSession
    config: ProviderConfig[Any]
    globalConfig: GlobalConfig
    zone_records: dict[str, dict[str, Record]] = (
        {}
    )  # dict[zone_id, dict[type-record_name, Record]]
    zone_ids: dict[str, str] = {}
    updated_zone_records: dict[str, dict[str, Record]] = {}
    created_zone_records: dict[str, dict[str, Record]] = {}
    consecutive_fail_counter: ProviderFailCounter

    def __init__(
        self,
        providerConfig: ProviderConfig[Any],
        globalConfig: GlobalConfig,
    ):
        try:
            self.config = self.validateConfig(providerConfig)
        except ValidationError as e:
            handleValidationError(e, f"{providerConfig.provider} config")
        self.globalConfig = globalConfig
        self.consecutive_fail_counter = ProviderFailCounter()
        self.aioSession = aiohttp.ClientSession()

    @abstractmethod
    def validateConfig(self, config: ProviderConfig[Any]) -> ProviderConfig[Any]:
        pass
        # call ProviderConfig[Specific Config Config].model_validate(self.config)

    @abstractmethod
    async def getCurrentDNSConfig(self):
        pass

    def createDNSRecord(self, type: str, name: str, value: str, zoneName: str):
        self.created_zone_records[self.zone_ids[zoneName]][f"{type}-{name}"] = Record(
            ttl=self.globalConfig.ttl, name=name, value=value, type=type
        )

    def updateDNSRecord(self, type: str, name: str, value: str, zoneName: str):
        temp_record = self.zone_records[self.zone_ids[zoneName]][
            f"{type}-{name}"
        ]

        if temp_record.value == value and temp_record.ttl == self.globalConfig.ttl:
            # skip if record value is unchanged
            return False

        temp_record.value = value
        temp_record.ttl = self.globalConfig.ttl
        if not self.zone_ids[zoneName] in self.updated_zone_records:
            self.updated_zone_records[self.zone_ids[zoneName]] = {}
        self.updated_zone_records[self.zone_ids[zoneName]][
            f"{type}-{name}"
        ] = temp_record

    def _updateSingleDNSRecordLocally(
        self, zoneName: str, recordName: str, type: str, value: str
    ) -> bool:
        if zoneName in self.zone_ids and f"{type}-{recordName}" in self.zone_records[self.zone_ids[zoneName]]:
            self.updateDNSRecord(
                type=type,
                name=recordName,
                value=value,
                zoneName=zoneName,
            )
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
                try:
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
                except ValueError as e:
                    # log if error when calculating ipv6 address
                    Logger.getDNSUpdaterLogger().error(e.args[0])

    @abstractmethod
    async def updateDNSConfig(self):
        pass
