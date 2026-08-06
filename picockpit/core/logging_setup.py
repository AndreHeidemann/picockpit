"""Configuracao de logging com console e arquivo rotacionado.

O destino padrao fica em tmpfs (ver ``core.config.default_log_dir``): o Pi
roda em cartao SD, e log e o dado que mais se escreve e menos se le. A rotacao
mantem no maximo 4 MB, o suficiente para diagnosticar a sessao corrente sem
ocupar memoria a toa.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: str = "INFO",
    log_dir: Path | None = None,
    max_bytes: int = 1024 * 1024,
    backup_count: int = 3,
) -> logging.Logger:
    """Configura o logger raiz de forma idempotente.

    Args:
        level: Nivel raiz (ex.: ``DEBUG``, ``INFO``).
        log_dir: Diretorio para ``picockpit.log``. Se ``None``, so console.
        max_bytes: Tamanho maximo por arquivo antes da rotacao.
        backup_count: Quantidade de arquivos historicos mantidos.

    Returns:
        O logger raiz configurado.
    """
    root = logging.getLogger()
    root.setLevel(level.upper())

    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formatter)
    root.addHandler(console)

    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / "picockpit.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    return root
