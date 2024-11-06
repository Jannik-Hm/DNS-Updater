from discord_webhook import DiscordWebhook, DiscordEmbed
from typing import Optional
from enum import Enum
from abc import ABC, abstractmethod


class LogLevel(Enum):
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3
    FATAL = 4

    @staticmethod
    def fromString(loglevel: str) -> 'LogLevel':
      match str.lower(loglevel):
        case "debug":
          return LogLevel.DEBUG
        case "info":
          return LogLevel.INFO
        case "warn":
          return LogLevel.WARN
        case "error":
          return LogLevel.ERROR
        case "fatal":
          return LogLevel.FATAL
        case _:
          raise ValueError


def _printLog(message: str, loglevel: LogLevel):
    logprintcolorcode: str
    match loglevel:
        case LogLevel.FATAL:
            logprintcolorcode = "91"
        case LogLevel.ERROR:
            logprintcolorcode = "91"
        case LogLevel.WARN:
            logprintcolorcode = "93"
        case LogLevel.DEBUG:
            logprintcolorcode = "0"
        case _:
            logprintcolorcode = "0"
    print(f"\033[{logprintcolorcode}m[{loglevel.name}]:\033[0m " + message.replace("```", ""))


class LogProvider(ABC):
    loglevel: LogLevel = LogLevel.INFO

    def __init__(
        self,
        loglevel: LogLevel = LogLevel.INFO,
    ):
        self.loglevel = loglevel

    @abstractmethod
    def print(self, message: str, loglevel: LogLevel):
        pass


class PrintLogger(LogProvider):
    def print(self, message: str, loglevel: LogLevel):
        _printLog(message=message, loglevel=loglevel)


class DiscordLogger(LogProvider):
    webhook_url: str

    def __init__(
        self,
        webhook_url: str,
        loglevel: LogLevel = LogLevel.INFO,
    ):
        self.webhook_url = webhook_url
        self.loglevel = loglevel

    def print(self, message: str, loglevel: LogLevel):
        logtitle: str
        logcolor: str
        match loglevel:
            case LogLevel.FATAL:
                logtitle = "Fatal Error"
                logcolor = "ff0000"
            case LogLevel.ERROR:
                logtitle = "Error"
                logcolor = "ff3300"
            case LogLevel.WARN:
                logtitle = "Warning"
                logcolor = "ffa600"
            case LogLevel.DEBUG:
                logtitle = "Debug"
                logcolor = "7a7a7a"
            case _:
                logtitle = "Information"
                logcolor = "03b2f8"
        if self.webhook_url is not None:
            webhook = DiscordWebhook(url=self.webhook_url, rate_limit_retry=True)
            embed = DiscordEmbed(title=logtitle, description=message, color=logcolor)
            webhook.add_embed(embed)
            response = webhook.execute()
            if response.status_code != 200:
                _printLog(
                    message="Discord Webhook Failed. Please check if the Webhook URL is valid.",
                    loglevel=LogLevel.FATAL,
                )


class Logger(object):
    logProviders: list[LogProvider] = []

    def __init__(self, logProviders: list[LogProvider] = []):
        self.logProviders = logProviders

    def log(self, message: str, loglevel: LogLevel = LogLevel.INFO):
        for provider in self.logProviders:
            if provider.loglevel.value <= loglevel.value:
              provider.print(message=message, loglevel=loglevel)
