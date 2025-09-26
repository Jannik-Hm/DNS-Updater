from pydantic import BaseModel
from typing import Any
import logging
from discord_logging.handler import DiscordHandler

from .abstract import LogProvider


class DiscordLogProviderConfig(BaseModel):
    webhook_url: str


class DiscordLogProvider(LogProvider):
    @classmethod
    def initHandler(
        cls, loggingConfig: Any, loglevel: int | str = logging.INFO
    ) -> logging.Handler:
        config = cls.validateConfig(loggingConfig=loggingConfig)
        handler = DiscordHandler(
            service_name="DNS Updater",
            webhook_url=config.webhook_url,
            emojis={
                None: "",  # Unknown log level
                logging.CRITICAL: "‼️",
                logging.ERROR: "❗️",
                logging.WARNING: "⚠️",
                logging.INFO: "ℹ️",
                logging.DEBUG: "",
            },
        )
        handler.setLevel(loglevel)
        handler.setFormatter(logging.Formatter("%(levelname)s\n%(message)s"))
        return handler

    @staticmethod
    def validateConfig(loggingConfig: Any) -> DiscordLogProviderConfig:
        return DiscordLogProviderConfig.model_validate(loggingConfig or {})
