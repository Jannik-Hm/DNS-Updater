import logging
from pydantic import ValidationError

from config import GlobalConfig, handleValidationError

from .provider_map import providerMap


class Logger(object):

    @classmethod
    def initLoggerHandlers(cls, config: GlobalConfig) -> logging.Logger:
        logger: logging.Logger
        if config.python_root_logger:
            logger = logging.getLogger()
        else:
            logger = cls.getDNSUpdaterLogger()
        logger.setLevel(
            logging.DEBUG
        )  # listen to all messages, let the logProvider decide what to send
        for loggerConfig in config.logging:
            if loggerConfig.provider.upper() not in providerMap:
                print(
                    f"Skipping unknown log provider '{loggerConfig.provider}' in config"
                )
                continue
            try:
                logger.addHandler(
                    providerMap[loggerConfig.provider.upper()].initHandler(
                        loggingConfig=loggerConfig.provider_config,
                        loglevel=loggerConfig.loglevel.upper(),
                    )
                )
            except ValidationError as e:
                handleValidationError(e, f"{loggerConfig.provider} logprovider config")
        return logger

    @staticmethod
    def getDNSUpdaterLogger() -> logging.Logger:
        return logging.getLogger("DNS Updater")
