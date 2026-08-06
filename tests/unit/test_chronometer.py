"""Testes dos cronometros de aceleracao e de volta."""

import pytest

from picockpit.services.chronometer import AccelerationTimer, LapTimer


def feed(timer: AccelerationTimer, samples: list[tuple[float, float]]) -> list[float]:
    """Alimenta o cronometro e devolve os tempos concluidos."""
    return [result for ts, speed in samples if (result := timer.update(ts, speed)) is not None]


def ramp(start_time: float, duration: float, top_speed: float, step: float = 0.05):
    """Gera uma aceleracao linear de zero ate ``top_speed``."""
    samples = []
    ticks = int(duration / step)
    for index in range(ticks + 1):
        elapsed = index * step
        samples.append((start_time + elapsed, top_speed * elapsed / duration))
    return samples


def test_starts_without_history() -> None:
    timer = AccelerationTimer()

    assert timer.last_seconds is None
    assert timer.best_seconds is None
    assert not timer.running


def test_measures_a_full_run() -> None:
    timer = AccelerationTimer(target_kmh=100.0)
    results = feed(timer, [(0.0, 0.0), *ramp(0.0, 20.0, 120.0)])

    assert len(results) == 1
    # Rampa linear ate 120 km/h em 20 s cruza 100 km/h aos 16,67 s.
    assert results[0] == pytest.approx(100.0 / 120.0 * 20.0, abs=0.05)


def test_clock_starts_from_rest_not_from_the_first_movement() -> None:
    """Contar so a partir de 1 km/h daria um tempo artificialmente bom."""
    timer = AccelerationTimer(target_kmh=100.0)
    feed(timer, [(0.0, 0.0), *ramp(0.0, 20.0, 120.0)])

    assert timer.last_seconds is not None
    assert timer.last_seconds > 100.0 / 120.0 * 20.0 - 0.05


def test_interpolates_the_crossing_instead_of_snapping_to_a_sample() -> None:
    """Sem interpolacao o resultado cairia sempre num multiplo do intervalo."""
    timer = AccelerationTimer(target_kmh=100.0)
    timer.update(0.0, 0.0)
    timer.update(0.5, 20.0)
    elapsed = timer.update(1.0, 120.0)

    # Cruza 100 km/h a 80% do intervalo entre 0,5 s e 1,0 s.
    assert elapsed is not None
    assert elapsed == pytest.approx(0.9, abs=0.02)
    assert elapsed != pytest.approx(1.0, abs=0.01)


def test_keeps_the_best_time() -> None:
    timer = AccelerationTimer(target_kmh=100.0)
    feed(timer, [(0.0, 0.0), *ramp(0.0, 14.0, 120.0)])
    rapida = timer.last_seconds

    feed(timer, [(30.0, 0.0), *ramp(30.0, 20.0, 120.0)])
    lenta = timer.last_seconds

    assert rapida is not None
    assert lenta is not None
    assert lenta > rapida
    assert timer.best_seconds == pytest.approx(rapida)


def test_does_not_start_from_a_rolling_speed() -> None:
    """Retomada em movimento nao e arrancada e nao pode contar."""
    timer = AccelerationTimer(target_kmh=100.0)
    results = feed(timer, [(0.0, 40.0), (1.0, 60.0), (2.0, 90.0), (3.0, 110.0)])

    assert results == []
    assert timer.last_seconds is None


def test_aborts_when_the_car_stops_before_the_target() -> None:
    timer = AccelerationTimer(target_kmh=100.0)
    feed(timer, [(0.0, 0.0), (1.0, 30.0), (2.0, 60.0)])
    assert timer.running

    timer.update(3.0, 0.0)

    assert not timer.running
    assert timer.last_seconds is None


def test_rearms_after_stopping() -> None:
    timer = AccelerationTimer(target_kmh=100.0)
    feed(timer, [(0.0, 0.0), (1.0, 30.0), (2.0, 0.0)])
    results = feed(timer, [(3.0, 0.0), *ramp(3.0, 16.0, 120.0)])

    assert len(results) == 1


def test_elapsed_reports_the_run_in_progress() -> None:
    timer = AccelerationTimer()
    feed(timer, [(0.0, 0.0), (1.0, 20.0), (2.0, 40.0)])

    assert timer.running
    assert timer.elapsed == pytest.approx(2.0, abs=0.1)


def test_reset_clears_everything() -> None:
    timer = AccelerationTimer(target_kmh=100.0)
    feed(timer, [(0.0, 0.0), *ramp(0.0, 20.0, 120.0)])
    timer.reset()

    assert timer.last_seconds is None
    assert timer.best_seconds is None
    assert not timer.running


def test_lower_target_finishes_sooner() -> None:
    fast = AccelerationTimer(target_kmh=60.0)
    slow = AccelerationTimer(target_kmh=100.0)
    samples = [(0.0, 0.0), *ramp(0.0, 20.0, 120.0)]
    feed(fast, samples)
    feed(slow, samples)

    assert fast.last_seconds is not None
    assert slow.last_seconds is not None
    assert fast.last_seconds < slow.last_seconds


# --------------------------------------------------------------- cronometro de volta


def test_lap_timer_starts_empty() -> None:
    lap = LapTimer()

    assert not lap.running
    assert lap.count == 0
    assert lap.best is None
    assert lap.current == 0.0


def test_lap_current_advances_with_the_clock() -> None:
    lap = LapTimer()
    lap.start(10.0)
    lap.tick(13.5)

    assert lap.current == pytest.approx(3.5)


def test_split_closes_a_lap_and_opens_the_next() -> None:
    lap = LapTimer()
    lap.start(0.0)
    closed = lap.split(42.0)

    assert closed == pytest.approx(42.0)
    assert lap.count == 1
    assert lap.running
    assert lap.current == 0.0


def test_best_lap_is_the_fastest() -> None:
    lap = LapTimer()
    lap.start(0.0)
    lap.split(40.0)
    lap.split(75.0)
    lap.split(120.0)

    assert lap.count == 3
    assert lap.best == pytest.approx(35.0)
    assert lap.last == pytest.approx(45.0)


def test_split_without_start_begins_the_session() -> None:
    lap = LapTimer()

    assert lap.split(5.0) is None
    assert lap.running


def test_stop_records_the_lap_in_progress() -> None:
    lap = LapTimer()
    lap.start(0.0)
    closed = lap.stop(30.0)

    assert closed == pytest.approx(30.0)
    assert not lap.running
    assert lap.count == 1


def test_stop_without_start_is_safe() -> None:
    lap = LapTimer()

    assert lap.stop(10.0) is None
    assert lap.count == 0


def test_reset_clears_the_session() -> None:
    lap = LapTimer()
    lap.start(0.0)
    lap.split(40.0)
    lap.reset()

    assert lap.count == 0
    assert not lap.running
    assert lap.current == 0.0


def test_run_is_abandoned_after_the_timeout() -> None:
    """Arrancada que nunca alcanca o alvo nao pode contar para sempre."""
    timer = AccelerationTimer(target_kmh=100.0, timeout_s=10.0)
    feed(timer, [(0.0, 0.0), (1.0, 40.0)])
    assert timer.running

    timer.update(12.0, 60.0)

    assert not timer.running
    assert timer.last_seconds is None


def test_timeout_requires_a_new_stop_to_rearm() -> None:
    timer = AccelerationTimer(target_kmh=100.0, timeout_s=5.0)
    feed(timer, [(0.0, 0.0), (1.0, 40.0), (7.0, 60.0)])

    assert not timer.running
    assert feed(timer, [(8.0, 120.0)]) == []

    # Rampa curta de proposito: com timeout de 5 s, uma arrancada de 12 s
    # seria abandonada antes de cruzar o alvo.
    results = feed(timer, [(9.0, 0.0), *ramp(9.0, 4.0, 120.0)])
    assert len(results) == 1
