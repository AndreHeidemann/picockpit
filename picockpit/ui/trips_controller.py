"""Controlador do historico de viagens."""

from __future__ import annotations

import time
from typing import Any

from PySide6.QtCore import Property, QObject, Slot
from PySide6.QtCore import Signal as QtSignal

from picockpit.core.events import EventBus
from picockpit.core.models import Signal
from picockpit.core.trip import Trip
from picockpit.core.units import UnitSystem, convert
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


def _to_map(trip: Trip, units: UnitSystem) -> dict[str, Any]:
    """Converte uma viagem no mapa consumido pelo QML.

    O banco guarda sempre em unidade canonica; a conversao acontece aqui, na
    leitura, para que o historico continue comparavel depois de o usuario
    trocar de sistema.

    Args:
        trip: Viagem gravada.
        units: Sistema de unidades de exibicao.

    Returns:
        Mapa com os valores ja formatados.
    """
    distance = convert(Signal.ODOMETER, trip.distance_km, units)
    consumption = convert(Signal.CONSUMPTION, trip.average_consumption_km_l, units)
    average = convert(Signal.SPEED, trip.average_speed_kmh, units)
    top = convert(Signal.SPEED, trip.max_speed_kmh, units)
    fuel = convert(Signal.FUEL_RATE, trip.fuel_used_l, units)

    return {
        "id": trip.trip_id or 0,
        "date": time.strftime("%d/%m %H:%M", time.localtime(trip.started_at)),
        "distance": f"{distance.value:.1f} {distance.unit}",
        "consumption": f"{consumption.value:.1f} {consumption.unit}",
        "duration": _duration(trip.duration_s),
        "averageSpeed": f"{average.value:.0f} {average.unit}",
        "maxSpeed": f"{top.value:.0f} {top.unit}",
        "fuelUsed": f"{fuel.value:.2f} {'gal' if units is UnitSystem.IMPERIAL else 'L'}",
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
        self._units = UnitSystem.METRIC
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

    def set_units(self, units: str | UnitSystem) -> None:
        """Troca o sistema de unidades do historico.

        Args:
            units: Sistema de unidades desejado.
        """
        try:
            system = UnitSystem(units)
        except ValueError:
            return
        if system is self._units:
            return
        self._units = system
        self.refresh()

    @Slot()
    def refresh(self) -> None:
        """Recarrega historico e somatorios do banco."""
        self._trips = [
            _to_map(trip, self._units) for trip in self._repository.recent(HISTORY_LIMIT)
        ]
        totals = self._repository.totals()
        distance = convert(Signal.ODOMETER, totals["distance_km"], self._units)
        consumption = convert(Signal.CONSUMPTION, totals["average_consumption_km_l"], self._units)
        fuel = convert(Signal.FUEL_RATE, totals["fuel_used_l"], self._units)
        self._totals = {
            "distance": f"{distance.value:.1f} {distance.unit}",
            "fuel": f"{fuel.value:.1f} {'gal' if self._units is UnitSystem.IMPERIAL else 'L'}",
            "consumption": f"{consumption.value:.1f} {consumption.unit}",
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
