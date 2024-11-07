from loguru import logger
from singletons.config import Config
from typing import Optional
import threading


class LoggerSingleton:
    _instance: Optional['LoggerSingleton'] = None
    _lock = threading.Lock()
    _logger = None

    def __new__(cls) -> 'LoggerSingleton':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._configure_logger()
        return cls._instance

    def _configure_logger(self) -> None:
        if self._logger is not None:
            return

        config = Config()
        logger.remove()
        logger.add(
            config.get("log_file"),
            level=config.get("log_level"),
            rotation="1 MB",
            encoding="utf-8",
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
        self._logger = logger

    def get_logger(self):
        return self._logger


def get_logger():
    """Get configured logger instance"""
    return LoggerSingleton().get_logger()