"""Testes da conversao de unidades na borda. Executa apenas no Raspberry Pi."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.ui

pytest.importorskip("PySide6", reason="PySide6 so existe no Raspberry Pi")

from picockpit.core.events import EventBus  # noqa: E402
from picockpit.core.models import Reading, Signal  # noqa: E402
from picockpit.services.telemetry_service import TelemetryService  # noqa: E402
from picockpit.simulation.provider import SimulationProvider  # noqa: E402
from picockpit.ui.telemetry_controller import TelemetryController  # noqa: E402


def build() -> tuple[TelemetryService, TelemetryController]:
    bus = EventBus()
    return TelemetryService(SimulationProvider(), bus), TelemetryController(bus)


async def test_metric_is_the_default() -> None:
    service, controller = build()
    await service.handle(Reading(signal=Signal.SPEED, value=100.0, timestamp=1.0))

    assert controller.speed == pytest.approx(100.0)
    assert controller.speedUnit == "km/h"


async def test_switching_to_imperial_converts_the_reading() -> None:
    service, controller = build()
    await service.handle(Reading(signal=Signal.SPEED, value=100.0, timestamp=1.0))
    controller.set_units("imperial")

    assert controller.speed == pytest.approx(62.14, abs=0.01)
    assert controller.speedUnit == "mph"


async def test_temperature_alert_uses_celsius_regardless_of_display() -> None:
    """Limiar de superaquecimento e propriedade do motor, nao da unidade."""
    service, controller = build()
    controller.set_units("imperial")
    await service.handle(Reading(signal=Signal.COOLANT_TEMP, value=110.0, timestamp=1.0))

    assert controller.overheating
    assert controller.coolantTemp == pytest.approx(230.0)


async def test_low_fuel_threshold_is_not_converted() -> None:
    service, controller = build()
    controller.set_units("imperial")
    await service.handle(Reading(signal=Signal.FUEL_LEVEL, value=8.0, timestamp=1.0))

    assert controller.lowFuel


async def test_unknown_unit_system_is_ignored() -> None:
    _, controller = build()
    controller.set_units("nautico")

    assert controller.speedUnit == "km/h"


async def test_switching_units_notifies_the_interface() -> None:
    _, controller = build()
    hits: list[int] = []
    controller.updated.connect(lambda: hits.append(1))

    controller.set_units("imperial")

    assert hits


async def test_trip_history_follows_the_unit_system() -> None:
    """O historico converte na leitura; o banco continua metrico."""
    from picockpit.core.trip import Trip
    from picockpit.data.database import connect
    from picockpit.data.trip_repository import TripRepository
    from picockpit.ui.trips_controller import TripsController

    repository = TripRepository(connect(":memory:"))
    repository.save(
        Trip(
            started_at=1000.0,
            ended_at=2000.0,
            duration_s=1000.0,
            moving_s=900.0,
            distance_km=100.0,
            fuel_used_l=10.0,
            max_speed_kmh=100.0,
        )
    )

    controller = TripsController(repository, EventBus())
    assert controller.trips[0]["distance"] == "100.0 km"
    assert controller.trips[0]["maxSpeed"] == "100 km/h"

    controller.set_units("imperial")
    assert controller.trips[0]["distance"] == "62.1 mi"
    assert controller.trips[0]["maxSpeed"] == "62 mph"

    # O que esta gravado nao muda.
    assert repository.recent()[0].distance_km == pytest.approx(100.0)
