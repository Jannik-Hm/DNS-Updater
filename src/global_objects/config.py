from pydantic import BaseModel, Field
from typing import Any, TypeVar, Generic

ProviderConfigConfig = TypeVar('ProviderConfigConfig')

class LoggingConfig(BaseModel):
  provider: str
  loglevel: str
  provider_config: Any | None = None

class GlobalConfig(BaseModel):
  ttl: int
  current_prefix_offset: str #hexadecimal
  dry_run: bool = Field(..., alias="dry-run")
  disable_v4: bool = Field(..., alias="disable-ipv4")
  disable_v6: bool = Field(..., alias="disable-ipv6")
  logging: list[LoggingConfig]

class RecordConfigV4(BaseModel):
  name: str

class RecordConfigV6(BaseModel):
  name: str
  prefixOffset: str
  suffix: str

class ZonesConfig(BaseModel):
  name: str
  ipv4_records: list[RecordConfigV4]
  ipv6_records: list[RecordConfigV6]

class ProviderConfig(BaseModel, Generic[ProviderConfigConfig]):
  provider: str
  provider_config: ProviderConfigConfig
  zones: list[ZonesConfig]

class Config(BaseModel):
  global_: GlobalConfig = Field(..., alias='global')
  providers: list[ProviderConfig[Any]]
