"""Controlador do historico de viagens."""

from __future__ import annotations

import time
from typing import Any

from PySide6.QtCore import Property, QObject, Slot
from PySide6.QtCore import Signal as QtSignal

from picockpit.core.events import EventBus
from picockpit.core.trip import Trip
from picockpit.data.trip_repository import TripRepository
from picockpit.services.trip_recorder import TOPIC_TRIP_SAVED

#: Quantidade de viagens exibidas no historico.
HISTORY_LIMIT = 30


def _duration(seconds: float) -> str:
    """Formata uma duracao em ``h:mm`` ou ``m min``."""
    minutes = int(seconds // 60)
    if minutes >= 60:
        return f"{minutes // 60}h{minutes % 60:02d}"
    return f"{minutes} min"


def _to_map(trip: Trip) -> dict[str, Any]:
    """Converte uma viagem no mapa consumido pelo QML."""
    return {
        "id": trip.trip_id or 0,
        "date": time.strftime("%d/%m %H:%M", time.localtime(trip.started_at)),
        "distance": f"{trip.distance_km:.1f} km",
        "consumption": f"{trip.average_consumption_km_l:.1f} km/L",
        "duration": _duration(trip.duration_s),
        "averageSpeed": f"{trip.average_speed_kmh:.0f} km/h",
        "maxSpeed": f"{trip.max_speed_kmh:.0f} km/h",
        "fuelUsed": f"{trip.fuel_used_l:.2f} L",
        "faults": list(trip.fault_codes),
    }


class TripsController(QObject):
    """Expoe o historico de viagens ao QML."""

    changed = QtSignal()

    def __init__(
        self,
        repository: TripRepository,
        bus: EventBus,
        parent: QObject | None = None,
    ) -> None:
        """Inicializa o controlador e carrega o historico existente.

        Args:
            repository: Fonte das viagens.
            bus: Barramento, para saber quando uma viagem nova foi gravada.
            parent: Pai Qt opcional.
        """
        super().__init__(parent)
        self._repository = repository
        self._trips: list[dict[str, Any]] = []
        self._totals: dict[str, str] = {}
        self._unsubscribe = bus.subscribe(TOPIC_TRIP_SAVED, self._on_trip_saved)
        self.refresh()

    def _on_trip_saved(self, _trip: Trip) -> None:
        """Recarrega o historico quando uma viagem e gravada."""
        self.refresh()

    @Property("QVariantList", notify=changed)  # type: ignore[operator]
    def trips(self) -> list[dict[str, Any]]:
        """Viagens recentes, da mais nova para a mais antiga."""
        return self._trips

    @Property("QVariantMap", notify=changed)  # type: ignore[operator]
    def totals(self) -> dict[str, str]:
        """Somatorios de todo o historico, ja formatados."""
        return self._totals

    @Property(int, notify=changed)  # type: ignore[operator]
    def count(self) -> int:
        """Quantidade de viagens no historico."""
        return len(self._trips)

    @Slot()
    def refresh(self) -> None:
        """Recarrega historico e somatorios do banco."""
        self._trips = [_to_map(trip) for trip in self._repository.recent(HISTORY_LIMIT)]
        totals = self._repository.totals()
        self._totals = {
            "distance": f"{totals['distance_km']:.1f} km",
            "fuel": f"{totals['fuel_used_l']:.1f} L",
            "consumption": f"{totals['average_consumption_km_l']:.1f} km/L",
            "duration": _duration(totals["duration_s"]),
        }
        self.changed.emit()

    @Slot()
    def clearHistory(self) -> None:  # noqa: N802 - nome consumido pelo QML
        """Apaga todo o historico de viagens."""
        self._repository.delete_all()
        self.refresh()

    def close(self) -> None:
        """Cancela a inscricao no barramento."""
        self._unsubscribe()
