from pydantic import BaseModel, Field, model_validator
from typing import Any, TypeVar, Generic

ProviderConfigConfig = TypeVar('ProviderConfigConfig')

class LoggingConfig(BaseModel):
  provider: str
  loglevel: str
  provider_config: Any | None = None

class GlobalConfig(BaseModel):
  cron: str = "*/1 * * * *"
  ttl: int = 60
  current_prefix_offset: str | None = None # hexadecimal, only required when ipv6 is enabled
  dry_run: bool = Field(False, alias="dry-run") # no dry run by default
  disable_v4: bool = Field(False, alias="disable-ipv4") # enable ipv4 by default
  disable_v6: bool = Field(True, alias="disable-ipv6") # disable ipv6 by default
  logging: list[LoggingConfig]

  @model_validator(mode="after")
  def check_ipv6_requirement(self):
      if not self.disable_v6 and self.current_prefix_offset is None:
          raise ValueError("`current_prefix_offset` is required when IPv6 is enabled (disable-ipv6 == False)")
      return self

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
