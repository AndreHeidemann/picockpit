"""Testes do motorista sintetico."""

import pytest

from picockpit.simulation.driver import PHASE_ORDER, DriverProfile, Phase


def test_starts_idle_with_pedals_released() -> None:
    driver = DriverProfile()
    assert driver.phase is Phase.IDLE
    assert driver.throttle == pytest.approx(0.0)
    assert driver.brake == pytest.approx(0.0)


def test_cycles_through_every_phase() -> None:
    driver = DriverProfile()
    seen = set()
    for _ in range(2000):
        driver.step(0.1)
        seen.add(driver.phase)

    assert seen == set(PHASE_ORDER)


def test_pedals_stay_within_bounds() -> None:
    driver = DriverProfile()
    for _ in range(3000):
        throttle, brake = driver.step(0.05)
        assert 0.0 <= throttle <= 100.0
        assert 0.0 <= brake <= 100.0


def test_throttle_moves_smoothly() -> None:
    driver = DriverProfile()
    previous = 0.0
    for _ in range(1000):
        throttle, _ = driver.step(0.05)
        assert abs(throttle - previous) < 25.0
        previous = throttle


def test_same_seed_gives_same_sequence() -> None:
    first = DriverProfile(seed=7)
    second = DriverProfile(seed=7)
    for _ in range(500):
        assert first.step(0.05) == second.step(0.05)


def test_different_seeds_diverge() -> None:
    first = DriverProfile(seed=1)
    second = DriverProfile(seed=2)
    outputs = [(first.step(0.05), second.step(0.05)) for _ in range(500)]

    assert any(a != b for a, b in outputs)


def test_braking_phase_releases_the_throttle() -> None:
    driver = DriverProfile()
    for _ in range(4000):
        throttle, brake = driver.step(0.05)
        if driver.phase is Phase.BRAKE and brake > 30.0:
            assert throttle < 15.0
            return
    pytest.fail("fase de frenagem nao foi alcancada")
