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


def screen_size(controller):
    from PySide6.QtGui import QGuiApplication

    geometry = QGuiApplication.screens()[0].geometry()
    return geometry.width(), geometry.height()


# --------------------------------------------------------------- basicos


def test_defaults(qt_app) -> None:
    controller = build()

    assert controller.clusterScreen == 0
    assert controller.consoleFraction == pytest.approx(0.3)


def test_screen_index_is_clamped_to_what_exists(qt_app) -> None:
    """Indice alem do que existe cai para o ultimo display, em vez de sumir."""
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


def test_sharing_does_not_create_a_second_window(qt_app) -> None:
    """Dividindo a tela, o cluster vira regiao e nao janela.

    No Wayland a aplicacao nao escolhe onde a propria janela aparece - isso e
    prerrogativa do compositor. Duas janelas lado a lado so funcionam quando
    cada uma tem a sua tela; na mesma tela elas acabam empilhadas.
    """
    assert not build(cluster_screen=0, console_screen=0).dual


def test_shared_console_takes_the_whole_screen(qt_app) -> None:
    """Dividindo a tela existe uma janela so, que hospeda as duas regioes."""
    controller = build(cluster_screen=0, console_screen=0, console_fraction=0.3)
    console = controller.consoleGeometry
    width, height = screen_size(controller)

    assert console["x"] == 0
    assert console["y"] == 0
    assert console["width"] == width
    assert console["height"] == height


def test_cluster_region_uses_the_remaining_fraction(qt_app) -> None:
    controller = build(cluster_screen=0, console_screen=0, console_fraction=0.25)
    width, _ = screen_size(controller)

    assert controller.clusterGeometry["width"] == pytest.approx(width * 0.75, abs=2)


def test_fullscreen_is_always_allowed(qt_app) -> None:
    """Mesmo dividindo, a unica janela deve ocupar o display inteiro."""
    assert build(cluster_screen=0, console_screen=0).fullscreenAllowed
    assert build(cluster_screen=0, console_screen=1).fullscreenAllowed


# ----------------------------------------------------------- telas proprias


def test_dedicated_screens_give_each_window_its_own(qt_app) -> None:
    controller = build(cluster_screen=0, console_screen=1)

    if controller.screenCount > 1:
        assert controller.dual
        assert not controller.shared
        assert controller.clusterScreen != controller.consoleScreen


def test_console_takes_its_fraction_of_a_dedicated_screen(qt_app) -> None:
    """Com tela propria, a multimidia cede o resto para a projecao."""
    controller = build(cluster_screen=0, console_screen=1, console_fraction=0.3)

    if controller.dual:
        width, _ = screen_size(controller)
        assert controller.consoleGeometry["width"] < width


def test_single_screen_gives_the_console_everything(qt_app) -> None:
    controller = build(cluster_screen=0, console_screen=9)

    if not controller.dual and not controller.shared:
        console = controller.consoleGeometry
        assert console["x"] == 0
        assert console["width"] > 0
