from loguru import logger
from singletons.config import Config
import threading


class LoggerSingleton:
    _instance = None
    _lock = threading.Lock()  # Ensures thread safety for singleton instantiation

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super().__new__(cls)
                    cls._instance._configure_logger()
        return cls._instance

    def _configure_logger(self):
        config = Config()
        log_file = config.get("log_file")
        log_level = config.get("log_level")

        # Set up the logger with configurations from `Config`
        logger.remove()  # Clear any previous handlers
        logger.add(
            log_file,
            level=log_level,
            rotation="1 MB",
            encoding="utf-8",
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
        self.logger = logger

    def get_logger(self):
        return self.logger


# Global access method for the logger instance
def get_logger():
    return LoggerSingleton().get_logger()
