"""Testes do modelo dinamico do veiculo."""

import pytest

from picockpit.core.models import SIGNAL_RANGES, Reading, Signal
from picockpit.simulation.model import VehicleModel
from picockpit.simulation.spec import VehicleSpec


def run_for(model: VehicleModel, seconds: float, throttle: float, brake: float = 0.0, dt=0.05):
    """Executa a simulacao por um periodo com entradas constantes."""
    values: dict = {}
    for _ in range(int(seconds / dt)):
        values = model.step(dt, throttle, brake)
    return values


def test_starts_cold_and_full() -> None:
    model = VehicleModel()
    assert model.coolant_temp_c == pytest.approx(model.spec.ambient_temp_c)
    assert model.fuel_l == pytest.approx(model.spec.tank_capacity_l)
    assert model.rpm == pytest.approx(model.spec.idle_rpm)


def test_step_rejects_non_positive_dt() -> None:
    with pytest.raises(ValueError, match="dt deve ser positivo"):
        VehicleModel().step(0.0, 50.0, 0.0)


def test_idle_keeps_vehicle_stopped() -> None:
    model = VehicleModel()
    values = run_for(model, seconds=10.0, throttle=0.0)

    assert values[Signal.SPEED] == pytest.approx(0.0, abs=0.1)
    assert values[Signal.RPM] == pytest.approx(model.spec.idle_rpm, abs=1.0)


def test_throttle_accelerates_the_vehicle() -> None:
    model = VehicleModel()
    values = run_for(model, seconds=12.0, throttle=90.0)

    assert values[Signal.SPEED] > 40.0
    assert values[Signal.RPM] > model.spec.idle_rpm


def test_brake_brings_the_vehicle_back_to_rest() -> None:
    model = VehicleModel()
    run_for(model, seconds=12.0, throttle=90.0)
    values = run_for(model, seconds=20.0, throttle=0.0, brake=100.0)

    assert values[Signal.SPEED] == pytest.approx(0.0, abs=0.5)


def test_gearbox_upshifts_while_accelerating() -> None:
    model = VehicleModel()
    run_for(model, seconds=25.0, throttle=100.0)

    assert model.gear > 1
    assert model.gear <= model.spec.gear_count()


def test_rpm_never_exceeds_redline() -> None:
    model = VehicleModel()
    for _ in range(4000):
        values = model.step(0.05, 100.0, 0.0)
        assert values[Signal.RPM] <= model.spec.redline_rpm
        assert values[Signal.RPM] >= model.spec.idle_rpm


def test_engine_warms_up_towards_operating_temperature() -> None:
    model = VehicleModel()
    cold = model.coolant_temp_c
    values = run_for(model, seconds=600.0, throttle=30.0)

    assert values[Signal.COOLANT_TEMP] > cold
    assert values[Signal.COOLANT_TEMP] == pytest.approx(model.spec.operating_temp_c, abs=6.0)


def test_fuel_decreases_monotonically() -> None:
    model = VehicleModel()
    previous = 100.0
    for _ in range(600):
        values = model.step(0.1, 60.0, 0.0)
        assert values[Signal.FUEL_LEVEL] <= previous
        previous = values[Signal.FUEL_LEVEL]
    assert previous < 100.0


def test_fuel_level_never_goes_negative() -> None:
    spec = VehicleSpec(tank_capacity_l=0.05)
    model = VehicleModel(spec=spec)
    values = run_for(model, seconds=120.0, throttle=100.0)

    assert values[Signal.FUEL_LEVEL] == pytest.approx(0.0)


def test_manifold_pressure_tracks_throttle() -> None:
    model = VehicleModel()
    closed = model.step(0.05, 0.0, 0.0)[Signal.MAP]
    wide_open = model.step(0.05, 100.0, 0.0)[Signal.MAP]

    assert closed < wide_open
    assert wide_open == pytest.approx(101.3, abs=0.1)


def test_airflow_grows_with_rpm_and_throttle() -> None:
    model = VehicleModel()
    idle = model.step(0.05, 0.0, 0.0)[Signal.MAF]
    driving = run_for(model, seconds=15.0, throttle=100.0)[Signal.MAF]

    assert driving > idle > 0.0


def test_voltage_drops_under_load() -> None:
    model = VehicleModel()
    unloaded = model.step(0.05, 0.0, 0.0)[Signal.VOLTAGE]
    loaded = model.step(0.05, 100.0, 0.0)[Signal.VOLTAGE]

    assert loaded < unloaded <= model.spec.charging_voltage


def test_uptime_accumulates_exactly() -> None:
    model = VehicleModel()
    for _ in range(20):
        values = model.step(0.5, 10.0, 0.0)

    assert values[Signal.UPTIME] == pytest.approx(10.0)


@pytest.mark.parametrize("throttle", [0.0, 25.0, 60.0, 100.0])
def test_every_signal_stays_within_physical_range(throttle: float) -> None:
    model = VehicleModel()
    for _ in range(1200):
        values = model.step(0.05, throttle, 0.0)
        for signal, value in values.items():
            low, high = SIGNAL_RANGES[signal]
            assert low <= value <= high, f"{signal.value}={value}"
            assert Reading(signal=signal, value=value, timestamp=0.0).is_plausible()


def test_inputs_are_clamped_to_valid_range() -> None:
    model = VehicleModel()
    values = model.step(0.05, 250.0, -30.0)

    assert values[Signal.THROTTLE] == pytest.approx(100.0)
    assert model.brake == pytest.approx(0.0)


def test_model_is_deterministic() -> None:
    first = VehicleModel()
    second = VehicleModel()
    for _ in range(300):
        assert first.step(0.05, 70.0, 0.0) == second.step(0.05, 70.0, 0.0)
