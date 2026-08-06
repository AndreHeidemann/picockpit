"""Testes do controlador de configuracoes. Executa apenas no Raspberry Pi."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.ui

pytest.importorskip("PySide6", reason="PySide6 so existe no Raspberry Pi")

from picockpit.core.events import EventBus  # noqa: E402
from picockpit.data.database import connect  # noqa: E402
from picockpit.data.preferences import PreferenceStore  # noqa: E402
from picockpit.simulation.provider import SimulationProvider  # noqa: E402
from picockpit.ui.settings_controller import SettingsController  # noqa: E402


def build(preferences: PreferenceStore | None = None) -> SettingsController:
    return SettingsController(SimulationProvider(), EventBus(), preferences=preferences)


def test_defaults_when_nothing_was_saved() -> None:
    controller = build(PreferenceStore(connect(":memory:")))

    assert controller.units == "metric"
    assert controller.uiScale == pytest.approx(1.0)
    assert controller.targetFps == 60


def test_units_are_remembered() -> None:
    store = PreferenceStore(connect(":memory:"))
    build(store).setUnits("imperial")

    assert build(store).units == "imperial"


def test_theme_is_remembered() -> None:
    store = PreferenceStore(connect(":memory:"))
    build(store).setTheme("sport")

    assert build(store).theme == "sport"


def test_fuel_choice_is_reapplied_on_startup() -> None:
    """O combustivel escolhido precisa valer no proximo boot."""
    store = PreferenceStore(connect(":memory:"))
    provider = SimulationProvider()
    SettingsController(provider, EventBus(), preferences=store).setFuel("ethanol")

    other = SimulationProvider()
    SettingsController(other, EventBus(), preferences=store)

    assert other.fuel() == "ethanol"


def test_invalid_values_are_ignored() -> None:
    controller = build(PreferenceStore(connect(":memory:")))
    controller.setUnits("nautico")
    controller.setUiScale(4.0)
    controller.setTargetFps(144)

    assert controller.units == "metric"
    assert controller.uiScale == pytest.approx(1.0)
    assert controller.targetFps == 60


def test_restore_defaults_clears_everything() -> None:
    store = PreferenceStore(connect(":memory:"))
    controller = build(store)
    controller.setUnits("imperial")
    controller.setUiScale(1.3)
    controller.restoreDefaults()

    assert controller.units == "metric"
    assert controller.uiScale == pytest.approx(1.0)
    assert store.all() == {}


def test_works_without_a_store() -> None:
    """Sem repositorio a tela continua funcional, so nao lembra de nada."""
    controller = build(None)
    controller.setUnits("imperial")

    assert controller.units == "metric"


def test_factory_defaults_come_from_the_config_file() -> None:
    controller = SettingsController(
        SimulationProvider(),
        EventBus(),
        preferences=PreferenceStore(connect(":memory:")),
        defaults={"theme": "night", "target_fps": "30"},
    )

    assert controller.theme == "night"
    assert controller.targetFps == 60
