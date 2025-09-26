from abc import ABC, abstractmethod
from typing import Any
import logging


class LogProvider(ABC):
    @classmethod
    @abstractmethod
    def initHandler(
        cls, loggingConfig: Any, loglevel: int | str = logging.INFO
    ) -> logging.Handler:
        pass

    @staticmethod
    @abstractmethod
    def validateConfig(loggingConfig: Any) -> Any:
        pass
