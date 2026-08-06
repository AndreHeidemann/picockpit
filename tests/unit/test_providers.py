"""Testes do contrato de providers."""

from collections.abc import AsyncIterator

import pytest

from picockpit.core.models import ProviderKind, Reading, Signal
from picockpit.services.providers import TelemetryProvider


class FakeProvider(TelemetryProvider):
    """Provider minimo usado para validar o contrato da classe base."""

    kind = ProviderKind.SIMULATION

    def __init__(self) -> None:
        self._connected = False
        self.disconnect_calls = 0

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False
        self.disconnect_calls += 1

    async def stream(self) -> AsyncIterator[Reading]:
        yield Reading(signal=Signal.RPM, value=800.0, timestamp=0.0, source=self.kind)

    @property
    def is_connected(self) -> bool:
        return self._connected


async def test_async_context_manager_connects_and_disconnects() -> None:
    provider = FakeProvider()

    async with provider as active:
        assert active.is_connected

    assert not provider.is_connected
    assert provider.disconnect_calls == 1


async def test_stream_yields_readings_tagged_with_provider_kind() -> None:
    provider = FakeProvider()
    readings = [reading async for reading in provider.stream()]

    assert readings[0].source is ProviderKind.SIMULATION
    assert readings[0].signal is Signal.RPM


def test_base_class_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        TelemetryProvider()  # type: ignore[abstract]
