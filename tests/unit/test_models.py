"""Testes dos modelos de dominio."""

import pytest

from picockpit.core.models import ProviderKind, Reading, Signal, VehicleState


def test_reading_exposes_canonical_unit() -> None:
    reading = Reading(signal=Signal.SPEED, value=80.0, timestamp=1.0)
    assert reading.unit == "km/h"


@pytest.mark.parametrize(
    ("signal", "value", "expected"),
    [
        (Signal.RPM, 3000.0, True),
        (Signal.RPM, -1.0, False),
        (Signal.RPM, 9000.0, False),
        (Signal.FUEL_LEVEL, 100.0, True),
        (Signal.VOLTAGE, 13.8, True),
        (Signal.VOLTAGE, 42.0, False),
    ],
)
def test_plausibility_follows_physical_ranges(signal: Signal, value: float, expected: bool) -> None:
    assert Reading(signal=signal, value=value, timestamp=0.0).is_plausible() is expected


def test_with_reading_does_not_mutate_original_state() -> None:
    original = VehicleState()
    updated = original.with_reading(
        Reading(signal=Signal.RPM, value=2500.0, timestamp=12.5, source=ProviderKind.OBD)
    )

    assert original.values == {}
    assert updated.get(Signal.RPM) == 2500.0
    assert updated.timestamp == 12.5
    assert updated.source is ProviderKind.OBD


def test_get_returns_default_for_unknown_signal() -> None:
    assert VehicleState().get(Signal.MAF, default=-1.0) == -1.0


def test_to_dict_uses_primitive_types() -> None:
    state = VehicleState().with_reading(Reading(signal=Signal.SPEED, value=60.0, timestamp=3.0))
    payload = state.to_dict()

    assert payload == {"timestamp": 3.0, "source": "simulation", "values": {"speed": 60.0}}


def test_every_signal_declares_unit_and_range() -> None:
    from picockpit.core.models import SIGNAL_RANGES, SIGNAL_UNITS

    for signal in Signal:
        assert signal in SIGNAL_UNITS
        assert signal in SIGNAL_RANGES
