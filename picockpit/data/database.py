"""Conexao e esquema do banco SQLite.

O esquema evolui por migracoes numeradas guardadas no proprio banco
(``PRAGMA user_version``). Sem isso, atualizar o PiCockpit num carro ja
instalado exigiria apagar o historico - inaceitavel para um dado que so se
acumula com o tempo.
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Sequence
from pathlib import Path

logger = logging.getLogger(__name__)

#: Migracoes em ordem. O indice na lista e a versao resultante.
MIGRATIONS: Sequence[str] = (
    """
    CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        started_at REAL NOT NULL,
        ended_at REAL NOT NULL,
        duration_s REAL NOT NULL,
        moving_s REAL NOT NULL,
        distance_km REAL NOT NULL,
        fuel_used_l REAL NOT NULL,
        max_speed_kmh REAL NOT NULL,
        fuel TEXT NOT NULL DEFAULT 'gasoline',
        fault_codes TEXT NOT NULL DEFAULT ''
    );
    CREATE INDEX IF NOT EXISTS idx_trips_started_at ON trips (started_at DESC);
    """,
)


def connect(path: Path | str) -> sqlite3.Connection:
    """Abre o banco, criando diretorio e esquema quando necessario.

    Args:
        path: Caminho do arquivo, ou ``:memory:`` para banco temporario.

    Returns:
        Conexao pronta para uso.
    """
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(path), check_same_thread=False)
    connection.row_factory = sqlite3.Row

    # WAL reduz a quantidade de reescrita do mesmo bloco, o que importa em
    # cartao SD. NORMAL abre mao do fsync a cada commit: no pior caso perde-se
    # a ultima viagem numa queda de energia, o que e barato perto de gastar a
    # vida do cartao.
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    connection.execute("PRAGMA foreign_keys=ON")

    migrate(connection)
    return connection


def migrate(connection: sqlite3.Connection) -> int:
    """Aplica as migracoes pendentes.

    Args:
        connection: Conexao aberta.

    Returns:
        Versao final do esquema.
    """
    version = connection.execute("PRAGMA user_version").fetchone()[0]

    for index, statement in enumerate(MIGRATIONS[version:], start=version):
        logger.info("Aplicando migracao %d do banco", index + 1)
        connection.executescript(statement)
        connection.execute(f"PRAGMA user_version = {index + 1}")
        connection.commit()

    return connection.execute("PRAGMA user_version").fetchone()[0]
