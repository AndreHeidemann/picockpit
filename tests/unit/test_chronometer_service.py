"""Testes do servico de cronometragem ligado ao barramento."""

import pytest

from picockpit.core.events import EventBus
from picockpit.core.models import Reading, Signal
from picockpit.services.chronometer import TOPIC_CHRONOMETER, ChronometerService


def speed(value: float, timestamp: float) -> Reading:
    return Reading(signal=Signal.SPEED, value=value, timestamp=timestamp)


async def test_publishes_a_snapshot_on_every_sample() -> None:
    bus = EventBus()
    ChronometerService(bus)
    seen: list = []
    bus.subscribe(TOPIC_CHRONOMETER, seen.append)

    await bus.publish("vehicle.signal.speed", speed(0.0, 0.0))
    await bus.publish("vehicle.signal.speed", speed(30.0, 1.0))

    assert len(seen) == 2
    assert seen[-1].acceleration_running


async def test_measures_an_acceleration_run_from_the_bus() -> None:
    bus = EventBus()
    service = ChronometerService(bus, target_kmh=100.0)

    await bus.publish("vehicle.signal.speed", speed(0.0, 0.0))
    for step in range(1, 41):
        await bus.publish("vehicle.signal.speed", speed(step * 3.0, step * 0.5))

    assert service.acceleration.last_seconds is not None
    assert service.acceleration.last_seconds == pytest.approx(100.0 / 3.0 * 0.5, abs=0.2)


async def test_lap_commands_use_the_telemetry_clock() -> None:
    bus = EventBus()
    service = ChronometerService(bus)

    await bus.publish("vehicle.signal.speed", speed(50.0, 10.0))
    await service.start_lap()
    await bus.publish("vehicle.signal.speed", speed(50.0, 40.0))
    await service.split_lap()

    assert service.lap.count == 1
    assert service.lap.last == pytest.approx(30.0)


async def test_reset_clears_both_chronometers() -> None:
    bus = EventBus()
    service = ChronometerService(bus, target_kmh=50.0)

    await bus.publish("vehicle.signal.speed", speed(0.0, 0.0))
    await bus.publish("vehicle.signal.speed", speed(80.0, 4.0))
    await service.start_lap()
    await service.reset()

    assert service.acceleration.best_seconds is None
    assert service.lap.count == 0
    assert not service.lap.running


async def test_snapshot_reflects_the_current_state() -> None:
    bus = EventBus()
    service = ChronometerService(bus)

    await bus.publish("vehicle.signal.speed", speed(0.0, 0.0))
    await bus.publish("vehicle.signal.speed", speed(40.0, 2.0))

    snapshot = service.snapshot()
    assert snapshot.acceleration_running
    assert snapshot.acceleration_elapsed == pytest.approx(2.0, abs=0.1)
    assert snapshot.lap_count == 0


async def test_close_stops_receiving_samples() -> None:
    bus = EventBus()
    service = ChronometerService(bus)
    service.close()

    await bus.publish("vehicle.signal.speed", speed(50.0, 1.0))

    assert service.now == 0.0
