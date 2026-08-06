"""Testes de consumo, autonomia e combustivel do Ka simulado."""

import pytest

from picockpit.core.models import Signal
from picockpit.simulation.model import VehicleModel
from picockpit.simulation.spec import FUEL_PROPERTIES, FuelKind, VehicleSpec


def drive(model: VehicleModel, seconds: float, throttle: float, dt: float = 0.05) -> dict:
    values: dict = {}
    for _ in range(int(seconds / dt)):
        values = model.step(dt, throttle, 0.0)
    return values


def test_ethanol_burns_more_fuel_than_gasoline() -> None:
    gasoline = drive(VehicleModel(spec=VehicleSpec(fuel=FuelKind.GASOLINE)), 60.0, 45.0)
    ethanol = drive(VehicleModel(spec=VehicleSpec(fuel=FuelKind.ETHANOL)), 60.0, 45.0)

    assert ethanol[Signal.FUEL_RATE] > gasoline[Signal.FUEL_RATE]
    assert ethanol[Signal.CONSUMPTION] < gasoline[Signal.CONSUMPTION]


def test_ethanol_penalty_is_in_the_expected_range() -> None:
    gasoline = drive(VehicleModel(spec=VehicleSpec(fuel=FuelKind.GASOLINE)), 90.0, 40.0)
    ethanol = drive(VehicleModel(spec=VehicleSpec(fuel=FuelKind.ETHANOL)), 90.0, 40.0)

    ratio = ethanol[Signal.CONSUMPTION] / gasoline[Signal.CONSUMPTION]
    assert 0.6 <= ratio <= 0.8, f"penalidade do etanol fora do esperado: {ratio:.2f}"


def test_consumption_is_zero_while_stopped() -> None:
    values = drive(VehicleModel(), 10.0, 0.0)

    assert values[Signal.SPEED] < VehicleSpec().consumption_floor_kmh
    assert values[Signal.CONSUMPTION] == pytest.approx(0.0)


def test_hourly_rate_is_positive_while_idling() -> None:
    values = drive(VehicleModel(), 10.0, 0.0)

    assert values[Signal.FUEL_RATE] > 0.0


def test_idle_hourly_rate_is_plausible_for_a_small_engine() -> None:
    values = drive(VehicleModel(), 20.0, 0.0)

    assert 0.4 <= values[Signal.FUEL_RATE] <= 1.5


def test_cruising_consumption_is_plausible_for_a_ka() -> None:
    values = drive(VehicleModel(), 200.0, 22.0)

    assert values[Signal.SPEED] > 30.0
    assert 10.0 <= values[Signal.CONSUMPTION] <= 30.0


def test_range_starts_from_the_nominal_figure() -> None:
    spec = VehicleSpec()
    model = VehicleModel(spec=spec)
    values = model.step(0.05, 0.0, 0.0)

    expected = spec.tank_capacity_l * spec.fuel_properties.nominal_km_per_l
    assert values[Signal.RANGE] == pytest.approx(expected, rel=0.02)


def test_range_is_proportional_to_the_fuel_left() -> None:
    model = VehicleModel()
    drive(model, 60.0, 30.0)

    full = model.step(0.05, 30.0, 0.0)[Signal.RANGE]
    model.fuel_l /= 2.0
    half = model.step(0.05, 30.0, 0.0)[Signal.RANGE]

    assert half == pytest.approx(full / 2.0, rel=0.05)


def test_range_grows_when_driving_more_efficiently() -> None:
    """Comportamento esperado: rodar economico estica a autonomia.

    Vale registrar porque contraria a intuicao de que autonomia so cai - com
    tanque quase cheio, a media de consumo melhorando pesa mais do que o
    combustivel gasto no periodo.
    """
    model = VehicleModel()
    thirsty = drive(model, 120.0, 90.0)[Signal.RANGE]
    economical = drive(model, 240.0, 18.0)[Signal.RANGE]

    assert economical > thirsty


def test_range_is_smoother_than_instant_consumption() -> None:
    """Autonomia usa media movel: nao pode saltar como o consumo instantaneo."""
    model = VehicleModel()
    drive(model, 120.0, 25.0)

    ranges = []
    consumptions = []
    for throttle in (25.0, 95.0, 25.0, 95.0):
        values = drive(model, 4.0, throttle)
        ranges.append(values[Signal.RANGE])
        consumptions.append(values[Signal.CONSUMPTION])

    range_swing = (max(ranges) - min(ranges)) / max(ranges)
    consumption_swing = (max(consumptions) - min(consumptions)) / max(consumptions)
    assert range_swing < consumption_swing


def test_intake_temperature_starts_at_ambient() -> None:
    spec = VehicleSpec()
    model = VehicleModel(spec=spec)

    assert model.step(0.05, 0.0, 0.0)[Signal.INTAKE_TEMP] == pytest.approx(
        spec.ambient_temp_c, abs=0.5
    )


def test_intake_temperature_rises_above_ambient_under_load() -> None:
    spec = VehicleSpec()
    values = drive(VehicleModel(spec=spec), 60.0, 80.0)

    assert values[Signal.INTAKE_TEMP] > spec.ambient_temp_c


def test_zero_to_hundred_matches_a_ka_ballpark() -> None:
    """Aceleracao dentro da ordem de grandeza de catalogo do Ka 1.0."""
    model = VehicleModel()
    elapsed = 0.0
    speed = 0.0
    while elapsed < 60.0 and speed < 100.0:
        speed = model.step(0.02, 100.0, 0.0)[Signal.SPEED]
        elapsed += 0.02

    assert 11.0 <= elapsed <= 19.0, f"0-100 em {elapsed:.1f}s"


@pytest.mark.parametrize("fuel", list(FuelKind))
def test_every_fuel_declares_complete_properties(fuel: FuelKind) -> None:
    properties = FUEL_PROPERTIES[fuel]

    assert properties.afr > 0
    assert properties.density_g_per_l > 0
    assert properties.nominal_km_per_l > 0
    assert properties.label
