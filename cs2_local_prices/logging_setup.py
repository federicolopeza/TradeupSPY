from __future__ import annotations

import logging
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(level: str = "INFO") -> None:
    """Configure Rich logging with the given level.

    Parameters
    ----------
    level: str
        Logging level name (e.g., "DEBUG", "INFO", "WARNING").
    """
    console = Console(force_terminal=True)
    handler = RichHandler(console=console, rich_tracebacks=True, show_time=True, show_level=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
        handlers=[handler],
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name if name else __name__)
