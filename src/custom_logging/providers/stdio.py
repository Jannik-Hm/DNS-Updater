from typing import Any
import logging

from .abstract import LogProvider


class CustomStreamFormatter(logging.Formatter):
    # ANSI escape sequences
    RESET = "\033[0m"
    COLOR_MAP = {
        logging.DEBUG: "\033[90m",  # grey
        logging.INFO: "\033[0m",  # default color / no color
        logging.WARNING: "\033[33m",  # yellow
        logging.ERROR: "\033[31m",  # red
        logging.CRITICAL: "\033[1;31m",  # bold red
    }

    def __init__(self, fmt, *args, **kwargs):
        super().__init__(fmt, *args, **kwargs)

    def format(self, record):
        # get the color for this record's level
        color = self.COLOR_MAP.get(record.levelno, self.RESET)
        # temporarily modify levelname to include color
        original = record.levelname
        record.levelname = f"{color}{original}{self.RESET}"
        try:
            return super().format(record)
        finally:
            # restore it (so other handlers/formatters don't get the colored version)
            record.levelname = original


class StdioLogProvider(LogProvider):
    @classmethod
    def initHandler(
        cls, loggingConfig: Any, loglevel: int | str = logging.INFO
    ) -> logging.Handler:
        handler = logging.StreamHandler()
        handler.setLevel(loglevel)
        handler.setFormatter(CustomStreamFormatter("[%(levelname)s]: %(message)s"))
        return handler

    @staticmethod
    def validateConfig(loggingConfig: Any) -> Any:
        # no provider specific config required
        return None
