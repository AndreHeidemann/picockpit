"""Testes do controlador de graficos. Executa apenas no Raspberry Pi."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.ui

pytest.importorskip("PySide6", reason="PySide6 so existe no Raspberry Pi")

from picockpit.core.events import EventBus  # noqa: E402
from picockpit.core.models import Reading, Signal  # noqa: E402
from picockpit.services.telemetry_service import TelemetryService  # noqa: E402
from picockpit.simulation.provider import SimulationProvider  # noqa: E402
from picockpit.ui.chart_controller import ChartController  # noqa: E402


def make_stack() -> tuple[TelemetryService, ChartController]:
    bus = EventBus()
    return TelemetryService(SimulationProvider(), bus), ChartController(bus)


async def feed(service: TelemetryService, samples: int, step: float = 0.1) -> None:
    for index in range(samples):
        await service.handle(
            Reading(signal=Signal.SPEED, value=index * 2.0, timestamp=index * step)
        )


async def test_polyline_is_empty_before_any_data() -> None:
    _, charts = make_stack()

    assert charts.polyline("speed", 200.0, 100.0) == []


async def test_polyline_grows_with_telemetry() -> None:
    service, charts = make_stack()
    await feed(service, 60)

    points = charts.polyline("speed", 200.0, 100.0)

    assert len(points) > 1
    assert all(0.0 <= point.x() <= 200.0 for point in points)
    assert all(0.0 <= point.y() <= 100.0 for point in points)


async def test_y_axis_is_inverted_for_screen_coordinates() -> None:
    """Valor maior tem de ficar mais perto do topo, ou seja, y menor."""
    service, charts = make_stack()
    await feed(service, 60)

    points = charts.polyline("speed", 200.0, 100.0)

    assert points[-1].y() < points[0].y()


async def test_revision_advances_so_bindings_reevaluate() -> None:
    service, charts = make_stack()
    before = charts.revision
    await feed(service, 40)

    assert charts.revision > before


async def test_redraw_is_throttled_below_the_sample_rate() -> None:
    """20 Hz de telemetria nao pode virar 20 Hz de redesenho."""
    service, charts = make_stack()
    before = charts.revision
    for index in range(40):
        await service.handle(Reading(signal=Signal.SPEED, value=50.0, timestamp=index * 0.05))

    assert charts.revision - before <= 22


async def test_latest_reports_the_last_value() -> None:
    service, charts = make_stack()
    await service.handle(Reading(signal=Signal.SPEED, value=77.0, timestamp=1.0))

    assert charts.latest("speed") == pytest.approx(77.0)


async def test_unknown_signal_is_handled_gracefully() -> None:
    _, charts = make_stack()

    assert charts.polyline("inexistente", 100.0, 50.0) == []
    assert charts.latest("inexistente") == 0.0


async def test_clear_discards_history() -> None:
    service, charts = make_stack()
    await feed(service, 60)
    charts.clear()

    assert charts.polyline("speed", 200.0, 100.0) == []
