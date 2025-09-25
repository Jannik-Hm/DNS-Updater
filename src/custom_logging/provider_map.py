from typing import Type
from .providers import *

providerMap: dict[str, Type[LogProvider]] = {
    "DISCORD": DiscordLogProvider,
    "STDIO": StdioLogProvider,
}
