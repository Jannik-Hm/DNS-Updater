from typing import Type

from .abstract import Provider
from .hetzner import HetznerProvider

providerMap: dict[str, Type[Provider]] = {
    "HETZNER": HetznerProvider,
}
