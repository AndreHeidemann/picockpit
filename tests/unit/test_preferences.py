"""Testes da persistencia de preferencias."""

import pytest

from picockpit.data.database import MIGRATIONS, connect
from picockpit.data.preferences import PreferenceStore


@pytest.fixture()
def store() -> PreferenceStore:
    return PreferenceStore(connect(":memory:"))


def test_migration_added_the_preferences_table() -> None:
    connection = connect(":memory:")

    assert connection.execute("PRAGMA user_version").fetchone()[0] == len(MIGRATIONS)
    connection.execute("SELECT key, value FROM preferences")


def test_missing_key_returns_the_default(store: PreferenceStore) -> None:
    assert store.get("tema", "normal") == "normal"


def test_value_survives_a_round_trip(store: PreferenceStore) -> None:
    store.set("tema", "sport")

    assert store.get("tema") == "sport"


def test_setting_twice_overwrites(store: PreferenceStore) -> None:
    store.set("tema", "sport")
    store.set("tema", "night")

    assert store.get("tema") == "night"
    assert len(store.all()) == 1


def test_numeric_helpers_parse(store: PreferenceStore) -> None:
    store.set("fps", "30")
    store.set("escala", "1.25")

    assert store.get_int("fps", 60) == 30
    assert store.get_float("escala", 1.0) == pytest.approx(1.25)


def test_corrupted_numeric_value_falls_back(store: PreferenceStore) -> None:
    """Valor invalido no banco nao pode impedir a aplicacao de subir."""
    store.set("fps", "sessenta")

    assert store.get_int("fps", 60) == 60


def test_all_returns_every_pair(store: PreferenceStore) -> None:
    store.set("a", "1")
    store.set("b", "2")

    assert store.all() == {"a": "1", "b": "2"}


def test_clear_restores_factory_values(store: PreferenceStore) -> None:
    store.set("tema", "sport")
    store.clear()

    assert store.all() == {}
    assert store.get("tema", "normal") == "normal"


def test_preferences_persist_across_connections(tmp_path) -> None:
    """A preferencia precisa sobreviver ao reinicio da aplicacao."""
    path = tmp_path / "picockpit.db"
    PreferenceStore(connect(path)).set("tema", "sport")

    assert PreferenceStore(connect(path)).get("tema") == "sport"
