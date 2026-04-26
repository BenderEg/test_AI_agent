import logging
import sys


def setup_logging(level: str = "INFO"):
    """Настройка логирования для приложения"""
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    

def get_logger(name: str) -> logging.Logger:
    """Логгер для модуля"""
    return logging.getLogger(name)