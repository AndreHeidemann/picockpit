"""Testes da configuracao de logging."""

import logging
from pathlib import Path

from picockpit.core.logging_setup import setup_logging


def test_console_only_by_default() -> None:
    root = setup_logging(level="INFO")
    assert root.level == logging.INFO
    assert len(root.handlers) == 1


def test_file_handler_created_when_dir_given(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    setup_logging(level="DEBUG", log_dir=log_dir)

    logging.getLogger("teste").debug("mensagem")

    assert (log_dir / "picockpit.log").is_file()


def test_setup_is_idempotent(tmp_path: Path) -> None:
    setup_logging(log_dir=tmp_path)
    handlers_first = len(logging.getLogger().handlers)
    setup_logging(log_dir=tmp_path)

    assert len(logging.getLogger().handlers) == handlers_first
