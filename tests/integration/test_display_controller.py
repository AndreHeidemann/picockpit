"""Testes da distribuicao de janelas. Executa apenas no Raspberry Pi."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.ui

pytest.importorskip("PySide6", reason="PySide6 so existe no Raspberry Pi")


@pytest.fixture(scope="module")
def qt_app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtGui import QGuiApplication

    yield QGuiApplication.instance() or QGuiApplication([])


def build(**kwargs):
    from picockpit.ui.display_controller import DisplayController

    return DisplayController(**kwargs)


def test_defaults(qt_app) -> None:
    controller = build()

    assert controller.clusterScreen == 0
    assert controller.consoleFraction == pytest.approx(0.3)


def test_screen_index_is_clamped_to_what_exists(qt_app) -> None:
    """Com um monitor so, o indice cai para o que existe em vez de sumir."""
    controller = build(cluster_screen=0, console_screen=9)

    assert 0 <= controller.consoleScreen <= controller.screenCount - 1


def test_fraction_is_bounded(qt_app) -> None:
    """Fracao fora de faixa deixaria a barra invisivel ou tomaria a tela toda."""
    assert build(console_fraction=0.001).consoleFraction == pytest.approx(0.1)
    assert build(console_fraction=5.0).consoleFraction == pytest.approx(0.9)


def test_negative_index_is_rejected(qt_app) -> None:
    assert build(cluster_screen=-3).clusterScreen == 0


# ------------------------------------------------------ tela compartilhada


def test_same_index_means_sharing_one_screen(qt_app) -> None:
    """Apontar os dois papeis para a mesma tela divide aquela tela."""
    controller = build(cluster_screen=0, console_screen=0)

    assert controller.shared
    assert controller.dual


def test_shared_geometry_covers_the_screen_without_overlap(qt_app) -> None:
    controller = build(cluster_screen=0, console_screen=0, console_fraction=0.3)
    cluster = controller.clusterGeometry
    console = controller.consoleGeometry

    assert cluster["x"] == 0
    assert console["x"] == cluster["width"]
    assert cluster["width"] + console["width"] == cluster["width"] + console["width"]
    assert console["x"] + console["width"] >= cluster["width"]
    assert cluster["height"] == console["height"]


def test_console_gets_the_configured_fraction(qt_app) -> None:
    controller = build(cluster_screen=0, console_screen=0, console_fraction=0.25)
    total = controller.clusterGeometry["width"] + controller.consoleGeometry["width"]
    share = controller.consoleGeometry["width"] / total

    assert share == pytest.approx(0.25, abs=0.01)


def test_fullscreen_is_refused_while_sharing(qt_app) -> None:
    """Tela cheia numa tela dividida faria uma janela cobrir a outra."""
    assert not build(cluster_screen=0, console_screen=0).fullscreenAllowed


def test_fullscreen_is_allowed_on_dedicated_screens(qt_app) -> None:
    assert build(cluster_screen=0, console_screen=1).fullscreenAllowed


def test_single_screen_gives_the_console_everything(qt_app) -> None:
    controller = build(cluster_screen=0, console_screen=9)

    if not controller.dual:
        console = controller.consoleGeometry
        assert console["x"] == 0
        assert console["width"] > 0
