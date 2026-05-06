import logging
import sys


def setup_logging(level: str = "INFO"):
    """Настройка логирования для приложения"""

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Логгер для модуля"""
    return logging.getLogger(name)
