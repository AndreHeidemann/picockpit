"""Testes das conversoes de unidade."""

import pytest

from picockpit.core.models import SIGNAL_UNITS, Signal
from picockpit.core.units import (
    UnitSystem,
    celsius_to_fahrenheit,
    convert,
    km_per_litre_to_mpg,
    km_to_miles,
)


def test_metric_is_the_identity() -> None:
    result = convert(Signal.SPEED, 100.0, UnitSystem.METRIC)

    assert result.value == pytest.approx(100.0)
    assert result.unit == "km/h"


def test_speed_converts_to_miles_per_hour() -> None:
    assert convert(Signal.SPEED, 100.0, UnitSystem.IMPERIAL).value == pytest.approx(62.14, abs=0.01)


def test_temperature_converts_to_fahrenheit() -> None:
    result = convert(Signal.COOLANT_TEMP, 100.0, UnitSystem.IMPERIAL)

    assert result.value == pytest.approx(212.0)
    assert result.unit == "F"


def test_freezing_point_is_thirty_two() -> None:
    assert celsius_to_fahrenheit(0.0) == pytest.approx(32.0)


def test_consumption_converts_to_miles_per_gallon() -> None:
    """13 km/L equivalem a cerca de 30,6 mpg."""
    assert km_per_litre_to_mpg(13.0) == pytest.approx(30.57, abs=0.05)


def test_a_marathon_is_about_twenty_six_miles() -> None:
    assert km_to_miles(42.195) == pytest.approx(26.219, abs=0.001)


@pytest.mark.parametrize("signal", [Signal.RPM, Signal.THROTTLE, Signal.VOLTAGE, Signal.MAP])
def test_signals_without_imperial_equivalent_stay_untouched(signal: Signal) -> None:
    """Rotacao, porcentagem e tensao sao iguais nos dois sistemas."""
    result = convert(signal, 42.0, UnitSystem.IMPERIAL)

    assert result.value == pytest.approx(42.0)
    assert result.unit == SIGNAL_UNITS[signal]


@pytest.mark.parametrize("system", list(UnitSystem))
@pytest.mark.parametrize("signal", list(Signal))
def test_every_signal_converts_without_error(signal: Signal, system: UnitSystem) -> None:
    result = convert(signal, 10.0, system)

    assert result.unit is not None
    assert isinstance(result.value, float)


def test_conversion_is_reversible_within_tolerance() -> None:
    from picockpit.core.units import KM_PER_MILE

    original = 88.0
    converted = convert(Signal.SPEED, original, UnitSystem.IMPERIAL).value

    assert converted * KM_PER_MILE == pytest.approx(original)
