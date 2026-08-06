"""Testes do servico de telemetria."""

import asyncio

from picockpit.core.events import EventBus
from picockpit.core.models import ProviderKind, Reading, Signal
from picockpit.services.telemetry_service import (
    TOPIC_STATE,
    TelemetryService,
    topic_for,
)
from picockpit.simulation.provider import SimulationProvider


def make_service() -> tuple[TelemetryService, EventBus]:
    bus = EventBus()
    provider = SimulationProvider(sample_interval_s=0.001, time_scale=5.0)
    return TelemetryService(provider, bus), bus


def test_topic_naming_is_stable() -> None:
    assert topic_for(Signal.RPM) == "vehicle.signal.rpm"


async def test_handle_updates_state_and_publishes() -> None:
    service, bus = make_service()
    per_signal: list[Reading] = []
    states: list[object] = []
    bus.subscribe(topic_for(Signal.RPM), per_signal.append)
    bus.subscribe(TOPIC_STATE, states.append)

    await service.handle(Reading(signal=Signal.RPM, value=2500.0, timestamp=1.0))

    assert service.state.get(Signal.RPM) == 2500.0
    assert per_signal[0].value == 2500.0
    assert len(states) == 1


async def test_implausible_reading_is_dropped() -> None:
    service, bus = make_service()
    received: list[Reading] = []
    bus.subscribe(topic_for(Signal.RPM), received.append)

    await service.handle(Reading(signal=Signal.RPM, value=99_000.0, timestamp=1.0))

    assert received == []
    assert service.dropped_readings == 1
    assert service.state.get(Signal.RPM) == 0.0


async def test_state_keeps_previous_signals() -> None:
    service, _ = make_service()
    await service.handle(Reading(signal=Signal.RPM, value=1500.0, timestamp=1.0))
    await service.handle(Reading(signal=Signal.SPEED, value=60.0, timestamp=2.0))

    assert service.state.get(Signal.RPM) == 1500.0
    assert service.state.get(Signal.SPEED) == 60.0


async def test_state_records_the_provider_source() -> None:
    service, _ = make_service()
    await service.handle(
        Reading(signal=Signal.SPEED, value=10.0, timestamp=1.0, source=ProviderKind.OBD)
    )

    assert service.state.source is ProviderKind.OBD


async def test_start_consumes_the_provider_and_stop_cancels() -> None:
    service, bus = make_service()
    seen: list[Reading] = []
    bus.subscribe(topic_for(Signal.SPEED), seen.append)

    await service.start()
    assert service.is_running
    await asyncio.sleep(0.05)
    await service.stop()

    assert not service.is_running
    assert seen, "nenhuma leitura de velocidade chegou ao barramento"


async def test_start_is_idempotent() -> None:
    service, _ = make_service()
    await service.start()
    first = service._task
    await service.start()

    assert service._task is first
    await service.stop()


async def test_stop_without_start_is_safe() -> None:
    service, _ = make_service()
    await service.stop()
    assert not service.is_running
