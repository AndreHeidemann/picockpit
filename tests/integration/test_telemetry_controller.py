"""Testes do controlador de telemetria da UI."""

import pytest

pytest.importorskip("PySide6", reason="PySide6 so existe no Raspberry Pi")

from picockpit.core.events import EventBus
from picockpit.core.models import Reading, Signal
from picockpit.services.telemetry_service import TelemetryService
from picockpit.simulation.provider import SimulationProvider
from picockpit.ui.telemetry_controller import TelemetryController

pytestmark = pytest.mark.ui


def make_stack() -> tuple[TelemetryService, TelemetryController]:
    bus = EventBus()
    service = TelemetryService(SimulationProvider(), bus)
    return service, TelemetryController(bus)


async def test_starts_zeroed() -> None:
    _, controller = make_stack()

    assert controller.rpm == 0.0
    assert controller.gearLabel == "N"


async def test_reflects_published_state() -> None:
    service, controller = make_stack()

    await service.handle(Reading(signal=Signal.RPM, value=3200.0, timestamp=1.0))
    await service.handle(Reading(signal=Signal.SPEED, value=90.0, timestamp=1.0))

    assert controller.rpm == 3200.0
    assert controller.speed == 90.0


async def test_emits_updated_signal() -> None:
    service, controller = make_stack()
    hits: list[int] = []
    controller.updated.connect(lambda: hits.append(1))

    await service.handle(Reading(signal=Signal.SPEED, value=10.0, timestamp=1.0))

    assert hits


async def test_gear_label_uses_neutral_for_zero() -> None:
    service, controller = make_stack()

    await service.handle(Reading(signal=Signal.GEAR, value=0.0, timestamp=1.0))
    assert controller.gearLabel == "N"

    await service.handle(Reading(signal=Signal.GEAR, value=4.0, timestamp=2.0))
    assert controller.gearLabel == "4"


async def test_low_fuel_alert_trips_below_threshold() -> None:
    service, controller = make_stack()

    await service.handle(Reading(signal=Signal.FUEL_LEVEL, value=50.0, timestamp=1.0))
    assert not controller.lowFuel

    await service.handle(Reading(signal=Signal.FUEL_LEVEL, value=8.0, timestamp=2.0))
    assert controller.lowFuel


async def test_overheating_alert_trips_above_threshold() -> None:
    service, controller = make_stack()

    await service.handle(Reading(signal=Signal.COOLANT_TEMP, value=92.0, timestamp=1.0))
    assert not controller.overheating

    await service.handle(Reading(signal=Signal.COOLANT_TEMP, value=110.0, timestamp=2.0))
    assert controller.overheating


async def test_low_voltage_ignores_the_zeroed_initial_state() -> None:
    _, controller = make_stack()

    assert not controller.lowVoltage


async def test_close_stops_receiving_updates() -> None:
    service, controller = make_stack()
    controller.close()

    await service.handle(Reading(signal=Signal.RPM, value=5000.0, timestamp=1.0))

    assert controller.rpm == 0.0
