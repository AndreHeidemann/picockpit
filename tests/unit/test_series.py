"""Testes da serie temporal usada nos graficos."""

import pytest

from picockpit.core.series import TimeSeries


def test_starts_empty() -> None:
    series = TimeSeries()

    assert len(series) == 0
    assert series.latest == 0.0
    assert series.normalized() == []


def test_keeps_samples_in_order() -> None:
    series = TimeSeries()
    series.append(1.0, 10.0)
    series.append(2.0, 20.0)

    assert series.samples == ((1.0, 10.0), (2.0, 20.0))
    assert series.latest == 20.0


def test_drops_samples_older_than_the_window() -> None:
    series = TimeSeries(window_s=10.0)
    for second in range(30):
        series.append(float(second), float(second))

    oldest = series.samples[0][0]
    assert oldest >= 29.0 - 10.0


def test_capacity_limits_memory() -> None:
    series = TimeSeries(window_s=10_000.0, capacity=50)
    for step in range(500):
        series.append(float(step), 1.0)

    assert len(series) == 50


def test_fixed_bounds_are_respected() -> None:
    series = TimeSeries(minimum=0.0, maximum=100.0)
    series.append(0.0, 10.0)

    assert series.bounds() == (0.0, 100.0)


def test_automatic_bounds_follow_the_peak() -> None:
    series = TimeSeries(maximum=None)
    series.append(0.0, 10.0)
    series.append(1.0, 40.0)

    assert series.bounds() == (0.0, 40.0)


def test_bounds_never_collapse() -> None:
    series = TimeSeries(maximum=None)
    series.append(0.0, 0.0)

    low, high = series.bounds()
    assert high > low


def test_normalized_stays_inside_the_unit_square() -> None:
    series = TimeSeries(window_s=10.0, minimum=0.0, maximum=100.0)
    for step in range(200):
        series.append(step * 0.05, step * 0.5)

    for x, y in series.normalized():
        assert 0.0 <= x <= 1.0
        assert 0.0 <= y <= 1.0


def test_normalized_is_downsampled_to_the_requested_resolution() -> None:
    series = TimeSeries(window_s=60.0, capacity=2000)
    for step in range(1200):
        series.append(step * 0.05, float(step))

    points = series.normalized(resolution=100)

    assert 90 <= len(points) <= 110


def test_newest_sample_is_the_last_point() -> None:
    series = TimeSeries(window_s=10.0, minimum=0.0, maximum=100.0)
    for step in range(100):
        series.append(step * 0.1, 50.0)
    series.append(10.0, 100.0)

    assert series.normalized()[-1][1] == pytest.approx(1.0)


def test_partial_history_does_not_stretch_across_the_axis() -> None:
    """Com pouca historia o grafico cresce da direita, nao estica na tela."""
    series = TimeSeries(window_s=60.0, minimum=0.0, maximum=10.0)
    series.append(0.0, 1.0)
    series.append(1.0, 2.0)
    series.append(2.0, 3.0)

    first_x = series.normalized()[0][0]
    assert first_x > 0.9


def test_clear_empties_the_series() -> None:
    series = TimeSeries()
    series.append(0.0, 1.0)
    series.clear()

    assert len(series) == 0
