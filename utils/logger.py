import logging
from logging.handlers import RotatingFileHandler

from config import settings


def setup_logging() -> None:
    settings.log_dir.mkdir(exist_ok=True)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    file_handler = RotatingFileHandler(
        settings.log_dir / "bot.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level, logging.INFO))
    root.handlers = [file_handler, stream]
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
