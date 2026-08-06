"""Testes do provider de simulacao."""

import pytest

from picockpit.core.models import ProviderKind, Signal
from picockpit.services.providers import ProviderError
from picockpit.simulation.provider import SimulationProvider


def test_rejects_invalid_sample_interval() -> None:
    with pytest.raises(ValueError, match="sample_interval_s"):
        SimulationProvider(sample_interval_s=0.0)


def test_rejects_invalid_time_scale() -> None:
    with pytest.raises(ValueError, match="time_scale"):
        SimulationProvider(time_scale=-1.0)


def test_sample_before_connect_fails() -> None:
    with pytest.raises(ProviderError):
        SimulationProvider().sample()


def test_model_before_connect_fails() -> None:
    with pytest.raises(ProviderError):
        _ = SimulationProvider().model


async def test_connect_and_disconnect_toggle_state() -> None:
    provider = SimulationProvider()
    assert not provider.is_connected

    await provider.connect()
    assert provider.is_connected

    await provider.disconnect()
    assert not provider.is_connected


async def test_sample_returns_every_signal_once() -> None:
    provider = SimulationProvider()
    await provider.connect()

    readings = provider.sample()

    assert {reading.signal for reading in readings} == set(Signal)
    assert all(reading.source is ProviderKind.SIMULATION for reading in readings)
    assert len({reading.timestamp for reading in readings}) == 1


async def test_readings_are_always_plausible() -> None:
    provider = SimulationProvider(time_scale=10.0)
    await provider.connect()

    for _ in range(400):
        for reading in provider.sample():
            assert reading.is_plausible(), f"{reading.signal.value}={reading.value}"


async def test_timestamp_advances_by_the_scaled_interval() -> None:
    provider = SimulationProvider(sample_interval_s=0.1, time_scale=2.0)
    await provider.connect()

    first = provider.sample()[0].timestamp
    second = provider.sample()[0].timestamp

    assert second - first == pytest.approx(0.2)


async def test_stream_yields_readings() -> None:
    provider = SimulationProvider(sample_interval_s=0.001)
    await provider.connect()

    collected = []
    async for reading in provider.stream():
        collected.append(reading)
        if len(collected) >= len(Signal) * 2:
            break

    await provider.disconnect()
    assert len(collected) == len(Signal) * 2


async def test_stream_without_connection_fails() -> None:
    provider = SimulationProvider()
    with pytest.raises(ProviderError):
        async for _ in provider.stream():
            break


async def test_context_manager_connects_and_disconnects() -> None:
    provider = SimulationProvider()
    async with provider:
        assert provider.is_connected
    assert not provider.is_connected


async def test_vehicle_actually_moves_over_a_full_cycle() -> None:
    provider = SimulationProvider(sample_interval_s=0.05, time_scale=4.0)
    await provider.connect()

    top_speed = 0.0
    for _ in range(600):
        for reading in provider.sample():
            if reading.signal is Signal.SPEED:
                top_speed = max(top_speed, reading.value)

    assert top_speed > 20.0
