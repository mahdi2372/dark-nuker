"""Logging setup."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(level: str = "INFO", log_dir: str = "logs") -> logging.Logger:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("nukebot")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    file_handler = RotatingFileHandler(
        Path(log_dir) / "nukebot.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    audit = logging.getLogger("nukebot.audit")
    audit.setLevel(logging.INFO)
    audit_handler = RotatingFileHandler(
        Path(log_dir) / "audit.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    audit_handler.setFormatter(formatter)
    audit.addHandler(audit_handler)
    audit.propagate = False
    return logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"nukebot.{name}")


def audit(action: str, **fields: object) -> None:
    parts = [f"{key}={value}" for key, value in fields.items()]
    logging.getLogger("nukebot.audit").info("%s | %s", action, " | ".join(parts))
