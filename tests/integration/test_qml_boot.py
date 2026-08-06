"""Teste de fumaca da camada QML. Executa apenas no Raspberry Pi.

Existe por causa de tres falhas reais das Etapas 1 e 3: context properties com
nome capitalizado resolvendo como ``null``, singletons registrados depois do
engine, e ``opacity`` atribuido a um ShapePath. As tres degradavam em silencio
ou apontavam para a linha errada. Aqui, qualquer aviso do QML e falha.

O engine e construido uma unica vez por processo: objetos registrados com
``qmlRegisterSingletonInstance`` pertencem a um unico engine, e um segundo
engine receberia os singletons como ``null``.
"""

from __future__ import annotations

import asyncio
import os

import pytest

pytestmark = pytest.mark.ui

PySide6 = pytest.importorskip("PySide6", reason="PySide6 so existe no Raspberry Pi")


@pytest.fixture(scope="module")
def qt_app():
    """Fornece uma QGuiApplication offscreen para o modulo de testes."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtGui import QGuiApplication

    yield QGuiApplication.instance() or QGuiApplication([])


@pytest.fixture(scope="module")
def stack(qt_app):
    """Constroi a arvore QML uma unica vez, capturando avisos do Qt."""
    from PySide6.QtCore import QtMsgType, qInstallMessageHandler

    from picockpit.app.main import build_engine
    from picockpit.core.config import AppConfig
    from picockpit.core.events import EventBus

    problems: list[str] = []

    def handler(mode, _context, message: str) -> None:
        if mode in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            problems.append(message)

    bus = EventBus()
    previous = qInstallMessageHandler(handler)
    try:
        engine, bridges = build_engine(AppConfig(), bus)
    finally:
        qInstallMessageHandler(previous)

    theme, _info, telemetry = bridges
    yield {
        "engine": engine,
        "bus": bus,
        "theme": theme,
        "telemetry": telemetry,
        "problems": problems,
    }


def test_main_qml_loads(stack: dict) -> None:
    """A arvore QML inteira compila e produz um objeto raiz."""
    assert stack["engine"].rootObjects(), "Main.qml nao carregou"


def test_qml_emits_no_warnings(stack: dict) -> None:
    """Nenhum aviso do QML durante a construcao da interface."""
    assert not stack["problems"], "QML emitiu avisos:\n" + "\n".join(stack["problems"])


def test_dashboard_receives_telemetry(stack: dict) -> None:
    """Valores publicados no barramento chegam ao controlador da UI."""
    from picockpit.core.models import Reading, Signal
    from picockpit.services.telemetry_service import TelemetryService
    from picockpit.simulation.provider import SimulationProvider

    service = TelemetryService(SimulationProvider(), stack["bus"])
    asyncio.run(service.handle(Reading(signal=Signal.SPEED, value=88.0, timestamp=1.0)))
    asyncio.run(service.handle(Reading(signal=Signal.GEAR, value=3.0, timestamp=1.0)))

    assert stack["telemetry"].speed == 88.0
    assert stack["telemetry"].gearLabel == "3"


def test_theme_switching_updates_the_palette(stack: dict) -> None:
    """O singleton de tema troca a paleta em tempo de execucao."""
    from picockpit.core.theme import get_palette

    theme = stack["theme"]
    theme.activate("sport")

    assert theme.name == "sport"
    assert theme.colors["primary"] == get_palette("sport").primary

    theme.activate("normal")


def test_second_engine_is_rejected(stack: dict) -> None:
    """Construir um segundo engine falha alto em vez de degradar em silencio."""
    from picockpit.app.main import build_engine
    from picockpit.core.config import AppConfig

    with pytest.raises(RuntimeError, match="um unico engine"):
        build_engine(AppConfig())
