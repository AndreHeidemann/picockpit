"""Persistencia das preferencias do usuario.

Guardadas no mesmo banco das viagens, e nao num arquivo separado, por tres
motivos: escrita transacional, um unico ponto a copiar no backup e nenhuma
fusao manual de arquivo de configuracao com valores padrao.

O arquivo TOML continua sendo a configuracao de fabrica; o que o usuario muda
na tela vive aqui e tem precedencia.
"""

from __future__ import annotations

import logging
import sqlite3

logger = logging.getLogger(__name__)


class PreferenceStore:
    """Repositorio chave/valor das preferencias."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Inicializa o repositorio.

        Args:
            connection: Conexao ja migrada.
        """
        self._connection = connection

    def get(self, key: str, default: str = "") -> str:
        """Le uma preferencia.

        Args:
            key: Chave.
            default: Valor devolvido quando a chave nao existe.

        Returns:
            Valor guardado, ou ``default``.
        """
        row = self._connection.execute(
            "SELECT value FROM preferences WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set(self, key: str, value: str) -> None:
        """Grava uma preferencia, substituindo o valor anterior.

        Args:
            key: Chave.
            value: Valor a guardar.
        """
        self._connection.execute(
            "INSERT INTO preferences (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self._connection.commit()

    def get_int(self, key: str, default: int) -> int:
        """Le uma preferencia numerica inteira, tolerando valor invalido."""
        try:
            return int(self.get(key, str(default)))
        except ValueError:
            logger.warning("Preferencia %s nao e inteira; usando %d", key, default)
            return default

    def get_float(self, key: str, default: float) -> float:
        """Le uma preferencia numerica, tolerando valor invalido."""
        try:
            return float(self.get(key, str(default)))
        except ValueError:
            logger.warning("Preferencia %s nao e numerica; usando %s", key, default)
            return default

    def all(self) -> dict[str, str]:
        """Todas as preferencias guardadas."""
        rows = self._connection.execute("SELECT key, value FROM preferences").fetchall()
        return {row["key"]: row["value"] for row in rows}

    def clear(self) -> None:
        """Apaga todas as preferencias, voltando aos valores de fabrica."""
        self._connection.execute("DELETE FROM preferences")
        self._connection.commit()
