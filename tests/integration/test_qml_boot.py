"""Teste de fumaca da camada QML. Executa apenas no Raspberry Pi.

Existe por causa de duas falhas reais da Etapa 1: context properties com nome
capitalizado resolvendo como ``null`` dentro de componentes carregados de
arquivo, e singletons registrados depois do engine. Ambas passavam despercebidas
porque o QML degrada silenciosamente - a tela abre, so que com estado errado.
Este teste transforma qualquer aviso do QML em falha.
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

    app = QGuiApplication.instance() or QGuiApplication([])
    yield app


def test_main_qml_loads_without_warnings(qt_app) -> None:
    """A arvore QML inteira compila e nao emite um unico aviso."""
    from PySide6.QtCore import QtMsgType, qInstallMessageHandler

    from picockpit.app.main import build_engine
    from picockpit.core.config import AppConfig

    problems: list[str] = []

    def handler(mode, _context, message: str) -> None:
        if mode in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            problems.append(message)

    previous = qInstallMessageHandler(handler)
    try:
        engine, bridges = build_engine(AppConfig())
    finally:
        qInstallMessageHandler(previous)

    assert engine.rootObjects(), "Main.qml nao carregou"
    assert not problems, "QML emitiu avisos:\n" + "\n".join(problems)
    assert bridges


def test_dashboard_reflects_telemetry(qt_app) -> None:
    """O painel recebe os valores publicados no barramento."""
    from picockpit.app.main import build_engine
    from picockpit.core.config import AppConfig
    from picockpit.core.events import EventBus
    from picockpit.core.models import Reading, Signal
    from picockpit.services.telemetry_service import TelemetryService
    from picockpit.simulation.provider import SimulationProvider

    bus = EventBus()
    engine, bridges = build_engine(AppConfig(), bus)
    assert engine.rootObjects()

    service = TelemetryService(SimulationProvider(), bus)
    asyncio.run(service.handle(Reading(signal=Signal.SPEED, value=88.0, timestamp=1.0)))

    telemetry = bridges[2]
    assert telemetry.speed == 88.0


def test_theme_singleton_is_visible_from_qml(qt_app) -> None:
    """O singleton ``Theme`` resolve dentro de um componente e expoe a paleta."""
    from PySide6.QtQml import QQmlApplicationEngine

    from picockpit.app.main import build_engine
    from picockpit.core.config import AppConfig
    from picockpit.core.theme import get_palette

    engine, bridges = build_engine(AppConfig(theme="sport"))
    assert isinstance(engine, QQmlApplicationEngine)

    theme = bridges[0]
    assert theme.name == "sport"
    assert theme.colors["primary"] == get_palette("sport").primary
