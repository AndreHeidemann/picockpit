"""Testes dos comandos de simulacao expostos pelo provider."""

import pytest

from picockpit.core.models import Signal
from picockpit.services.providers import ProviderError, TelemetryProvider
from picockpit.simulation.provider import SimulationProvider
from picockpit.simulation.spec import FuelKind


class BareProvider(TelemetryProvider):
    """Provider minimo que nao suporta comando nenhum."""

    async def connect(self) -> None: ...

    async def disconnect(self) -> None: ...

    def stream(self):
        raise NotImplementedError

    @property
    def is_connected(self) -> bool:
        return False


def test_base_provider_declares_no_simulation_controls() -> None:
    assert not BareProvider().supports_simulation_controls


def test_base_provider_rejects_fuel_change() -> None:
    with pytest.raises(NotImplementedError):
        BareProvider().set_fuel("ethanol")


def test_base_provider_rejects_fault_injection() -> None:
    with pytest.raises(NotImplementedError):
        BareProvider().inject_fault("P0301")


def test_base_provider_rejects_clearing_faults() -> None:
    with pytest.raises(NotImplementedError):
        BareProvider().clear_faults()


async def test_simulation_declares_the_controls() -> None:
    provider = SimulationProvider()
    await provider.connect()

    assert provider.supports_simulation_controls
    assert provider.fuel() == FuelKind.GASOLINE.value


async def test_fuel_change_preserves_the_vehicle_state() -> None:
    """Trocar combustivel nao pode zerar tanque, hodometro nem temperatura."""
    provider = SimulationProvider(time_scale=6.0)
    await provider.connect()
    for _ in range(200):
        provider.sample()

    before = provider.model
    tank, odometer, coolant = before.fuel_l, before.odometer_km, before.coolant_temp_c
    provider.set_fuel("ethanol")
    after = provider.model

    assert provider.fuel() == "ethanol"
    assert after.fuel_l == pytest.approx(tank)
    assert after.odometer_km == pytest.approx(odometer)
    assert after.coolant_temp_c == pytest.approx(coolant)


async def test_fuel_change_updates_the_chemistry() -> None:
    provider = SimulationProvider()
    await provider.connect()
    provider.set_fuel("ethanol")

    assert provider.model.spec.fuel_properties.afr == pytest.approx(9.0)


async def test_unknown_fuel_is_rejected() -> None:
    provider = SimulationProvider()
    await provider.connect()

    with pytest.raises(ProviderError, match="desconhecido"):
        provider.set_fuel("diesel")


async def test_injecting_and_clearing_faults_moves_the_lamp() -> None:
    provider = SimulationProvider()
    await provider.connect()

    provider.inject_fault("P0301")
    lit = {reading.signal: reading.value for reading in provider.sample()}[Signal.MIL]
    assert lit == pytest.approx(1.0)

    provider.clear_faults()
    off = {reading.signal: reading.value for reading in provider.sample()}[Signal.MIL]
    assert off == pytest.approx(0.0)
    assert provider.fault_codes() == ()


def test_commands_before_connecting_fail_loudly() -> None:
    provider = SimulationProvider()

    with pytest.raises(ProviderError):
        provider.inject_fault("P0301")
    with pytest.raises(ProviderError):
        provider.clear_faults()
