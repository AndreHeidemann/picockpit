"""Persistencia de viagens."""

from __future__ import annotations

import sqlite3
from dataclasses import replace

from picockpit.core.trip import Trip


def _row_to_trip(row: sqlite3.Row) -> Trip:
    """Converte uma linha do banco em ``Trip``."""
    codes = row["fault_codes"]
    return Trip(
        trip_id=row["id"],
        started_at=row["started_at"],
        ended_at=row["ended_at"],
        duration_s=row["duration_s"],
        moving_s=row["moving_s"],
        distance_km=row["distance_km"],
        fuel_used_l=row["fuel_used_l"],
        max_speed_kmh=row["max_speed_kmh"],
        fuel=row["fuel"],
        fault_codes=tuple(code for code in codes.split(",") if code),
    )


class TripRepository:
    """Guarda e recupera viagens."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Inicializa o repositorio.

        Args:
            connection: Conexao ja migrada.
        """
        self._connection = connection

    def save(self, trip: Trip) -> Trip:
        """Grava uma viagem.

        Args:
            trip: Viagem a gravar.

        Returns:
            A mesma viagem, agora com o identificador atribuido.
        """
        cursor = self._connection.execute(
            """
            INSERT INTO trips (
                started_at, ended_at, duration_s, moving_s,
                distance_km, fuel_used_l, max_speed_kmh, fuel, fault_codes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trip.started_at,
                trip.ended_at,
                trip.duration_s,
                trip.moving_s,
                trip.distance_km,
                trip.fuel_used_l,
                trip.max_speed_kmh,
                trip.fuel,
                ",".join(trip.fault_codes),
            ),
        )
        self._connection.commit()

        return replace(trip, trip_id=cursor.lastrowid)

    def recent(self, limit: int = 20) -> list[Trip]:
        """Lista as viagens mais recentes.

        Args:
            limit: Quantidade maxima de registros.

        Returns:
            Viagens da mais recente para a mais antiga.
        """
        rows = self._connection.execute(
            "SELECT * FROM trips ORDER BY started_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [_row_to_trip(row) for row in rows]

    def count(self) -> int:
        """Quantidade de viagens gravadas."""
        return int(self._connection.execute("SELECT COUNT(*) FROM trips").fetchone()[0])

    def totals(self) -> dict[str, float]:
        """Somatorios de todas as viagens.

        Returns:
            Distancia, combustivel, tempo e consumo medio acumulados.
        """
        row = self._connection.execute("""
            SELECT
                COALESCE(SUM(distance_km), 0) AS distance_km,
                COALESCE(SUM(fuel_used_l), 0) AS fuel_used_l,
                COALESCE(SUM(duration_s), 0) AS duration_s
            FROM trips
            """).fetchone()

        distance = float(row["distance_km"])
        fuel = float(row["fuel_used_l"])
        return {
            "distance_km": distance,
            "fuel_used_l": fuel,
            "duration_s": float(row["duration_s"]),
            "average_consumption_km_l": distance / fuel if fuel > 0 else 0.0,
        }

    def delete_all(self) -> None:
        """Apaga todo o historico."""
        self._connection.execute("DELETE FROM trips")
        self._connection.commit()
