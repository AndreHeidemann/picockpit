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
    """Com um monitor so, as duas janelas caem na mesma tela em vez de sumir."""
    controller = build(cluster_screen=0, console_screen=9)

    assert controller.consoleScreen <= controller.screenCount - 1
    assert controller.consoleScreen >= 0


def test_dual_reports_whether_the_split_is_possible(qt_app) -> None:
    controller = build(cluster_screen=0, console_screen=9)

    assert controller.dual == (controller.screenCount > 9)


def test_fraction_is_bounded(qt_app) -> None:
    """Fracao fora de faixa deixaria a barra invisivel ou tomaria a tela toda."""
    assert build(console_fraction=0.001).consoleFraction == pytest.approx(0.1)
    assert build(console_fraction=5.0).consoleFraction == pytest.approx(0.9)


def test_negative_index_is_rejected(qt_app) -> None:
    assert build(cluster_screen=-3).clusterScreen == 0
