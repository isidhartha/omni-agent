"""Structured logging setup for OmniAgent."""

from __future__ import annotations

import logging
import sys
from typing import Any

from .config import get_settings


def _build_formatter() -> logging.Formatter:
    fmt = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
    return logging.Formatter(fmt, datefmt="%Y-%m-%dT%H:%M:%S")


def setup_logging() -> None:
    """Configure root logger for the application."""
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_build_formatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Silence noisy third-party loggers
    for lib in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(lib).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)


class AgentLogger:
    """Thin wrapper that prefixes every log line with the agent name."""

    def __init__(self, agent_name: str) -> None:
        self._log = get_logger(f"agent.{agent_name}")

    def info(self, msg: str, *args: Any, **kw: Any) -> None:
        self._log.info(msg % args if args else msg)

    def warning(self, msg: str, *args: Any, **kw: Any) -> None:
        self._log.warning(msg % args if args else msg)

    def error(self, msg: str, *args: Any, **kw: Any) -> None:
        self._log.error(msg % args if args else msg)

    def debug(self, msg: str, *args: Any, **kw: Any) -> None:
        self._log.debug(msg % args if args else msg)
