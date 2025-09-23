from abc import ABC, abstractmethod
from pydantic import BaseModel
from global_objects.config import ProviderConfig, GlobalConfig
from typing import Any
from helper_functions.ipv6 import calculateIPv6Address

#TODO: allow consecutive fails (for timeout cases)

class Record(BaseModel):
    ttl: int | None = None
    name: str
    value: str
    type: str


class Provider(ABC):
    config: ProviderConfig[Any]
    zone_records: dict[str, dict[str, Record]] = (
        {}
    )  # dict[zone_id, dict[type-record_name, Record]]
    zone_ids: dict[str, str] = {}
    updated_zone_records: dict[str, dict[str, Record]] = {}
    created_zone_records: dict[str, dict[str, Record]] = {}

    def __init__(self, providerConfig: ProviderConfig[Any]):
        self.config = self.validateConfig(providerConfig)

    @abstractmethod
    def validateConfig(self, config: ProviderConfig[Any]) -> ProviderConfig[Any]:
        pass
        # call ProviderConfig[Specific Config Config].model_validate(self.config)

    @abstractmethod
    def getCurrentDNSConfig(self, globalConfig: GlobalConfig):
        pass

    def createDNSRecord(self, type: str, name: str, value: str, zoneName: str):
        self.created_zone_records[self.zone_ids[zoneName]][f"{type}-{name}"] = Record(
            ttl=60, name=name, value=value, type=type
        )

    def updateDNSRecordsLocally(
        self, globalConfig: GlobalConfig, currentIPv4: str | None, currentIPv6Prefix: list[str] | None
    ):
        for zone in self.config.zones:
            if not globalConfig.disable_v4 and currentIPv4:
                for record in zone.ipv4_records:
                    if (
                        f"AAAA-{record.name}"
                        in self.zone_records[self.zone_ids[zone.name]]
                    ):
                        temp_record = self.zone_records[self.zone_ids[zone.name]][
                            f"A-{record.name}"
                        ]

                        if temp_record.value == currentIPv4:
                            continue

                        temp_record.value = currentIPv4
                        if not self.zone_ids[zone.name] in self.updated_zone_records:
                            self.updated_zone_records[self.zone_ids[zone.name]] = {}
                        self.updated_zone_records[self.zone_ids[zone.name]][
                            f"A-{record.name}"
                        ] = temp_record
                    else:
                        self.createDNSRecord(
                            type="A",
                            name=record.name,
                            value=currentIPv4,
                            zoneName=zone.name,
                        )
            if not globalConfig.disable_v6 and currentIPv6Prefix:
                for record in zone.ipv6_records:
                    if (
                        f"AAAA-{record.name}"
                        in self.zone_records[self.zone_ids[zone.name]]
                    ):
                        temp_record = self.zone_records[self.zone_ids[zone.name]][
                            f"AAAA-{record.name}"
                        ]

                        ipv6_value = calculateIPv6Address(
                            prefix=currentIPv6Prefix,
                            prefixOffset=record.prefixOffset,
                            currentAddressOrFixedSuffix=(
                                record.suffix
                                or self.zone_records[self.zone_ids[zone.name]][
                                    "AAAA-" + record.name
                                ].value
                            ),
                        )

                        if temp_record.value == ipv6_value:
                            continue

                        temp_record.value = ipv6_value
                        if not self.zone_ids[zone.name] in self.updated_zone_records:
                            self.updated_zone_records[self.zone_ids[zone.name]] = {}
                        self.updated_zone_records[self.zone_ids[zone.name]][
                            f"AAAA-{record.name}"
                        ] = temp_record
                    else:
                        self.createDNSRecord(
                            type="AAAA",
                            name=record.name,
                            value=calculateIPv6Address(
                                prefix=currentIPv6Prefix,
                                prefixOffset=record.prefixOffset,
                                currentAddressOrFixedSuffix=record.suffix,
                            ),
                            zoneName=zone.name,
                        )

    @abstractmethod
    def updateDNSConfig(self, globalConfig: GlobalConfig):
        pass
