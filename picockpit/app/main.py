"""Ponto de entrada da aplicacao grafica.

Executa exclusivamente no Raspberry Pi: importa PySide6, que nao existe no
container de backend.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonInstance
from PySide6.QtQuickControls2 import QQuickStyle

from picockpit import __version__
from picockpit.core.config import AppConfig, load_config
from picockpit.core.events import EventBus
from picockpit.core.logging_setup import setup_logging
from picockpit.services.providers import TelemetryProvider
from picockpit.simulation.provider import SimulationProvider
from picockpit.ui.bridge import AppInfo, ThemeController
from picockpit.ui.telemetry_controller import TelemetryController

logger = logging.getLogger(__name__)

QML_ROOT = Path(__file__).resolve().parent.parent / "ui" / "qml"

#: Namespace QML dos objetos expostos pelo Python.
QML_URI = "PiCockpit"


def create_provider(app_config: AppConfig) -> TelemetryProvider:
    """Instancia o provider de telemetria configurado.

    E o unico ponto do sistema que decide a origem dos dados. Trocar simulacao
    por OBD-II ou CAN na Etapa 8 e acrescentar um ramo aqui - nada acima desta
    funcao precisa mudar.

    Args:
        app_config: Configuracao efetiva.

    Returns:
        Provider pronto para uso.

    Raises:
        NotImplementedError: Para providers ainda nao implementados.
    """
    interval_s = app_config.sample_interval_ms / 1000.0

    if app_config.provider == "simulation":
        return SimulationProvider(sample_interval_s=interval_s)
    if app_config.provider in {"obd", "can"}:
        raise NotImplementedError(f"Provider '{app_config.provider}' chega na Etapa 8")
    raise NotImplementedError(f"Provider desconhecido: {app_config.provider}")


def build_engine(
    app_config: AppConfig,
    bus: EventBus | None = None,
) -> tuple[QQmlApplicationEngine, list[object]]:
    """Cria o engine QML com a ponte Python ja registrada.

    Args:
        app_config: Configuracao efetiva da aplicacao.
        bus: Barramento de eventos. Um novo e criado quando omitido.

    Returns:
        O engine e a lista de objetos de ponte, que precisam ser mantidos vivos
        pelo chamador para nao serem coletados pelo garbage collector.
    """
    theme = ThemeController(app_config.theme)
    info = AppInfo(
        version=__version__,
        env=app_config.env,
        target_fps=app_config.target_fps,
    )
    telemetry = TelemetryController(bus or EventBus())

    # Singletons registrados, e nao context properties: nomes capitalizados em
    # context property nao resolvem de forma confiavel dentro de componentes
    # carregados de arquivo, e falham silenciosamente como `null`. O singleton
    # e explicito, resolvido em tempo de compilacao do QML e verificavel.
    #
    # A ORDEM IMPORTA: o registro precisa acontecer ANTES de instanciar o
    # QQmlApplicationEngine. Registrar depois deixa o modulo num estado
    # meio-resolvido e o erro reportado e enganoso ("Cannot assign object to
    # list property data", apontando para um Text qualquer).
    qmlRegisterSingletonInstance(ThemeController, QML_URI, 1, 0, "Theme", theme)
    qmlRegisterSingletonInstance(AppInfo, QML_URI, 1, 0, "AppInfo", info)
    qmlRegisterSingletonInstance(TelemetryController, QML_URI, 1, 0, "Telemetry", telemetry)

    engine = QQmlApplicationEngine()
    engine.load(QUrl.fromLocalFile(str(QML_ROOT / "Main.qml")))
    return engine, [theme, info, telemetry]


def main() -> int:
    """Sobe a aplicacao Qt, o laco asyncio e a telemetria.

    Returns:
        Codigo de saida do processo.
    """
    import asyncio

    import qasync

    from picockpit.services.telemetry_service import TelemetryService

    app_config = load_config()
    setup_logging(level=app_config.log_level, log_dir=app_config.log_dir)

    logger.info("PiCockpit OS %s iniciando (env=%s)", __version__, app_config.env)

    app = QGuiApplication(sys.argv)
    app.setApplicationName("PiCockpit OS")
    app.setApplicationVersion(__version__)

    # Estilo Basic: sem dependencia de tema do sistema e sem custo extra de
    # renderizacao. A identidade visual vem inteira da nossa paleta.
    QQuickStyle.setStyle("Basic")

    # qasync coloca o laco do asyncio para rodar dentro do laco do Qt. A
    # alternativa seria uma thread separada com invokeMethod para cada
    # atualizacao - mais codigo, e uma fronteira de concorrencia a mais para
    # errar. Com um unico laco, provider, servico e UI vivem na mesma thread.
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    bus = EventBus()
    engine, bridges = build_engine(app_config, bus)
    if not engine.rootObjects():
        logger.error("Falha ao carregar Main.qml")
        return 1

    service = TelemetryService(create_provider(app_config), bus)

    logger.info(
        "Plataforma Qt: %s | provider: %s | amostragem: %dms",
        app.platformName(),
        app_config.provider,
        app_config.sample_interval_ms,
    )

    with loop:
        task = loop.create_task(service.run())
        app.aboutToQuit.connect(task.cancel)
        loop.run_forever()

    del bridges
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
