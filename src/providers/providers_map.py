from typing import Type

from .abstract import Provider, AsyncProvider
from .hetzner import HetznerProvider, AsyncHetznerProvider

providerMap: dict[str, Type[AsyncProvider]] = {
    "HETZNER": AsyncHetznerProvider,
}
