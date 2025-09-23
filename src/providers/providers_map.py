from enum import Enum
from typing import Type

from .abstract import Provider
from .hetzner import HetznerProvider

class ProviderMapping(Enum):
  HETZNER = HetznerProvider

  @property
  def provider_class(self) -> Type[Provider]:
    # .value is known to be a subtype of Provider
    return self.value