"""Testes do injetor de falhas."""

import pytest

from picockpit.core.models import Signal
from picockpit.services.providers import TelemetryProvider
from picockpit.simulation.faults import KNOWN_CODES, FaultInjector
from picockpit.simulation.provider import SimulationProvider


def test_starts_without_faults() -> None:
    injector = FaultInjector()

    assert injector.active == ()
    assert not injector.mil_on


def test_injecting_a_known_code_uses_the_catalog() -> None:
    injector = FaultInjector()
    fault = injector.inject("P0301")

    assert fault is KNOWN_CODES["P0301"]
    assert injector.codes == ("P0301",)
    assert injector.mil_on


def test_unknown_codes_are_accepted() -> None:
    injector = FaultInjector()
    fault = injector.inject("P1234")

    assert fault.code == "P1234"
    assert injector.mil_on


def test_code_that_does_not_light_the_lamp() -> None:
    injector = FaultInjector()
    injector.inject("P0442")

    assert injector.codes == ("P0442",)
    assert not injector.mil_on


def test_injecting_twice_does_not_duplicate() -> None:
    injector = FaultInjector()
    injector.inject("P0171")
    injector.inject("P0171")

    assert injector.codes == ("P0171",)


def test_clearing_a_single_code() -> None:
    injector = FaultInjector()
    injector.inject("P0300")
    injector.inject("P0442")
    injector.clear("P0300")

    assert injector.codes == ("P0442",)
    assert not injector.mil_on


def test_clearing_everything() -> None:
    injector = FaultInjector()
    injector.inject("P0300")
    injector.clear()

    assert injector.codes == ()


def test_base_provider_reports_no_faults() -> None:
    assert TelemetryProvider.fault_codes(object()) == ()  # type: ignore[arg-type]


async def test_simulation_provider_publishes_the_lamp_state() -> None:
    provider = SimulationProvider()
    await provider.connect()

    lamp = {reading.signal: reading.value for reading in provider.sample()}[Signal.MIL]
    assert lamp == pytest.approx(0.0)

    provider.faults.inject("P0301")
    lamp = {reading.signal: reading.value for reading in provider.sample()}[Signal.MIL]

    assert lamp == pytest.approx(1.0)
    assert provider.fault_codes() == ("P0301",)
