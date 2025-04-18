import logging
import sys
from pathlib import Path
from logging import INFO, Logger, getLogger, WARNING, Formatter
from logging.handlers import RotatingFileHandler
from typing import Final
from uvicorn.logging import ColourizedFormatter
from configs.constants import BASE_DIR

DEFAULT_LOGGER_NAME: Final[str] = "root"
LOG_DIR_PATH: Final[Path] = BASE_DIR / 'logs'
LLM_LOG_DIR_PATH: Final[Path] = LOG_DIR_PATH / 'llm_logs'

_DATE_FMT: Final[str] = '%Y-%m-%d %H:%M:%S'

def setup_logging(
    default_level: int = INFO,
) -> Logger:
    LOG_DIR_PATH.mkdir(exist_ok=True)
    logger: Final = getLogger()
    logger.handlers = []
    logger.setLevel(default_level)

    file_handler = RotatingFileHandler(
        filename=LOG_DIR_PATH / 'app.log',
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(WARNING)
    file_formatter = Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt=_DATE_FMT,
    )
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(default_level)
    console_formatter = ColourizedFormatter(
        fmt="%(levelprefix)s %(module)s:%(lineno)-3d %(message)s",
        use_colors=True,
    )
    console_handler.setFormatter(console_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
