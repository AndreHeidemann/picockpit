"""Testes da composicao de tela. Executa apenas no Raspberry Pi."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.ui

pytest.importorskip("PySide6", reason="PySide6 so existe no Raspberry Pi")

from picockpit.core.layout import DEFAULT_RATIO  # noqa: E402
from picockpit.data.database import connect  # noqa: E402
from picockpit.data.preferences import PreferenceStore  # noqa: E402
from picockpit.ui.layout_controller import DEFAULT_WIDGETS, LayoutController  # noqa: E402


def build(store: PreferenceStore | None = None) -> LayoutController:
    return LayoutController(store)


def test_starts_undivided() -> None:
    controller = build(PreferenceStore(connect(":memory:")))

    assert not controller.split
    assert controller.ratio == pytest.approx(DEFAULT_RATIO.value)


def test_split_is_remembered() -> None:
    store = PreferenceStore(connect(":memory:"))
    build(store).setSplit(True)

    assert build(store).split


def test_ratio_snaps_to_a_registered_option() -> None:
    store = PreferenceStore(connect(":memory:"))
    controller = build(store)
    controller.setRatio(0.62)

    assert controller.ratio in {option["value"] for option in controller.ratioOptions}


def test_secondary_page_must_be_splittable() -> None:
    """Ajustes e formulario: nao pode ocupar meia tela."""
    controller = build(PreferenceStore(connect(":memory:")))
    controller.setSecondary("settings")

    assert controller.secondary != "settings"


def test_secondary_page_is_remembered() -> None:
    store = PreferenceStore(connect(":memory:"))
    build(store).setSecondary("widgets")

    assert build(store).secondary == "widgets"


def test_default_widgets_are_active() -> None:
    controller = build(PreferenceStore(connect(":memory:")))

    assert controller.widgets == list(DEFAULT_WIDGETS)


def test_toggling_a_widget_persists() -> None:
    store = PreferenceStore(connect(":memory:"))
    build(store).toggleWidget("clock")

    assert "clock" in build(store).widgets


def test_toggling_twice_returns_to_the_original() -> None:
    controller = build(PreferenceStore(connect(":memory:")))
    before = controller.widgets
    controller.toggleWidget("voltage")
    controller.toggleWidget("voltage")

    assert controller.widgets == before


def test_widget_order_follows_the_catalog_not_the_clicks() -> None:
    controller = build(PreferenceStore(connect(":memory:")))
    for key in list(controller.widgets):
        controller.toggleWidget(key)
    controller.toggleWidget("odometer")
    controller.toggleWidget("speed")

    assert controller.widgets == ["speed", "odometer"]


def test_unknown_widget_is_ignored() -> None:
    controller = build(PreferenceStore(connect(":memory:")))
    before = controller.widgets
    controller.toggleWidget("inexistente")

    assert controller.widgets == before


def test_stale_preference_is_filtered_out() -> None:
    """Preferencia antiga apontando para widget que sumiu nao pode quebrar."""
    store = PreferenceStore(connect(":memory:"))
    store.set("widgets", "speed,widget_que_nao_existe,fuel")

    assert build(store).widgets == ["speed", "fuel"]


def test_works_without_a_store() -> None:
    controller = build(None)
    controller.setSplit(True)

    assert not controller.split
