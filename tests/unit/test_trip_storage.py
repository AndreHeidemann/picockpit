"""Testes do banco e do repositorio de viagens."""

from pathlib import Path

import pytest

from picockpit.core.trip import Trip
from picockpit.data.database import MIGRATIONS, connect, migrate
from picockpit.data.trip_repository import TripRepository


@pytest.fixture()
def repository() -> TripRepository:
    return TripRepository(connect(":memory:"))


def make_trip(**overrides) -> Trip:
    base = {
        "started_at": 1000.0,
        "ended_at": 2000.0,
        "duration_s": 1000.0,
        "moving_s": 900.0,
        "distance_km": 12.0,
        "fuel_used_l": 1.0,
        "max_speed_kmh": 88.0,
    }
    base.update(overrides)
    return Trip(**base)


def test_schema_is_created_at_the_latest_version() -> None:
    connection = connect(":memory:")

    assert connection.execute("PRAGMA user_version").fetchone()[0] == len(MIGRATIONS)


def test_migration_is_idempotent() -> None:
    connection = connect(":memory:")
    first = migrate(connection)
    second = migrate(connection)

    assert first == second == len(MIGRATIONS)


def test_database_file_is_created_with_its_directory(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "picockpit.db"
    connect(target)

    assert target.is_file()


def test_saving_assigns_an_identifier(repository: TripRepository) -> None:
    saved = repository.save(make_trip())

    assert saved.trip_id is not None
    assert repository.count() == 1


def test_round_trip_preserves_every_field(repository: TripRepository) -> None:
    original = make_trip(fuel="ethanol", fault_codes=("P0301", "P0171"))
    repository.save(original)

    restored = repository.recent()[0]

    assert restored.distance_km == pytest.approx(original.distance_km)
    assert restored.fuel == "ethanol"
    assert restored.fault_codes == ("P0301", "P0171")


def test_trip_without_faults_round_trips_as_empty(repository: TripRepository) -> None:
    repository.save(make_trip())

    assert repository.recent()[0].fault_codes == ()


def test_recent_returns_newest_first(repository: TripRepository) -> None:
    repository.save(make_trip(started_at=100.0))
    repository.save(make_trip(started_at=300.0))
    repository.save(make_trip(started_at=200.0))

    order = [trip.started_at for trip in repository.recent()]

    assert order == [300.0, 200.0, 100.0]


def test_recent_respects_the_limit(repository: TripRepository) -> None:
    for index in range(5):
        repository.save(make_trip(started_at=float(index)))

    assert len(repository.recent(limit=2)) == 2


def test_totals_accumulate(repository: TripRepository) -> None:
    repository.save(make_trip(distance_km=10.0, fuel_used_l=1.0))
    repository.save(make_trip(distance_km=20.0, fuel_used_l=1.0))

    totals = repository.totals()

    assert totals["distance_km"] == pytest.approx(30.0)
    assert totals["average_consumption_km_l"] == pytest.approx(15.0)


def test_totals_on_empty_database(repository: TripRepository) -> None:
    totals = repository.totals()

    assert totals["distance_km"] == 0.0
    assert totals["average_consumption_km_l"] == 0.0


def test_delete_all_clears_history(repository: TripRepository) -> None:
    repository.save(make_trip())
    repository.delete_all()

    assert repository.count() == 0


def test_average_consumption_is_zero_without_fuel() -> None:
    assert make_trip(fuel_used_l=0.0).average_consumption_km_l == 0.0


def test_average_speed_uses_moving_time_only() -> None:
    """Semaforo nao pode derrubar a media da viagem."""
    trip = make_trip(distance_km=30.0, moving_s=1800.0, duration_s=3600.0)

    assert trip.average_speed_kmh == pytest.approx(60.0)


def test_average_speed_is_zero_when_never_moved() -> None:
    assert make_trip(moving_s=0.0).average_speed_kmh == 0.0
