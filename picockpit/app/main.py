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
from picockpit.data.database import connect
from picockpit.data.preferences import PreferenceStore
from picockpit.data.trip_repository import TripRepository
from picockpit.services.chronometer import ChronometerService
from picockpit.services.providers import TelemetryProvider
from picockpit.services.trip_recorder import TripRecorder
from picockpit.simulation.provider import SimulationProvider
from picockpit.ui.bridge import AppInfo, ThemeController
from picockpit.ui.chart_controller import ChartController
from picockpit.ui.chrono_controller import ChronoController
from picockpit.ui.display_controller import DisplayController
from picockpit.ui.layout_controller import LayoutController
from picockpit.ui.settings_controller import SettingsController
from picockpit.ui.telemetry_controller import TelemetryController
from picockpit.ui.trips_controller import TripsController

logger = logging.getLogger(__name__)

QML_ROOT = Path(__file__).resolve().parent.parent / "ui" / "qml"

#: Namespace QML dos objetos expostos pelo Python.
QML_URI = "PiCockpit"

#: Guarda de engine unico. Ver ``build_engine``.
_engine_built = False


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
    provider: TelemetryProvider | None = None,
) -> tuple[QQmlApplicationEngine, list[object]]:
    """Cria o engine QML com a ponte Python ja registrada.

    Args:
        app_config: Configuracao efetiva da aplicacao.
        bus: Barramento de eventos. Um novo e criado quando omitido.
        provider: Fonte de telemetria. Uma nova e criada quando omitida.

    Returns:
        O engine e a lista de objetos de ponte, que precisam ser mantidos vivos
        pelo chamador para nao serem coletados pelo garbage collector.

    Raises:
        RuntimeError: Se chamado mais de uma vez no mesmo processo.
    """
    global _engine_built

    # Objetos registrados com qmlRegisterSingletonInstance pertencem a um unico
    # engine. Um segundo engine no mesmo processo recebe os singletons como
    # `null`, e a arvore QML falha com mensagens que apontam para o lugar
    # errado. Falhar alto aqui e melhor do que caçar o sintoma depois.
    if _engine_built:
        raise RuntimeError(
            "build_engine ja foi chamado neste processo; singletons QML "
            "pertencem a um unico engine"
        )
    _engine_built = True

    # Uma unica conexao serve viagens e preferencias: mesmo banco, mesmo
    # backup, uma so migracao.
    connection = connect(app_config.database_path)
    preferences = PreferenceStore(connection)

    # Preferencia guardada tem precedencia sobre o arquivo de fabrica.
    theme = ThemeController(preferences.get("theme", app_config.theme))
    info = AppInfo(
        version=__version__,
        env=app_config.env,
        target_fps=preferences.get_int("target_fps", app_config.target_fps),
        kiosk=app_config.kiosk,
    )
    event_bus = bus or EventBus()
    telemetry = TelemetryController(event_bus)
    chronometer = ChronometerService(event_bus)
    chrono = ChronoController(event_bus, chronometer)
    charts = ChartController(event_bus)
    layout = LayoutController(preferences)
    displays = DisplayController(
        cluster_screen=app_config.cluster_screen,
        console_screen=app_config.console_screen,
        console_fraction=app_config.console_fraction,
    )
    settings = SettingsController(
        provider or create_provider(app_config),
        event_bus,
        preferences=preferences,
        defaults={
            "theme": app_config.theme,
            "target_fps": str(app_config.target_fps),
        },
    )

    repository = TripRepository(connection)
    recorder = TripRecorder(event_bus, repository)
    trips = TripsController(repository, event_bus)
    # O gravador precisa saber o combustivel para registrar na viagem; a
    # tela de ajustes e quem sabe quando ele muda.
    settings.changed.connect(lambda: recorder.set_fuel(settings.fuel))
    recorder.set_fuel(settings.fuel)

    # A troca de unidades acontece na tela de ajustes e precisa alcancar quem
    # formata os valores.
    settings.changed.connect(lambda: telemetry.set_units(settings.units))
    settings.changed.connect(lambda: trips.set_units(settings.units))
    telemetry.set_units(settings.units)
    trips.set_units(settings.units)

    # Tema tambem e preferencia persistida: a tela grava, o controlador aplica.
    settings.changed.connect(lambda: theme.activate(settings.theme))

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
    qmlRegisterSingletonInstance(ChronoController, QML_URI, 1, 0, "Chrono", chrono)
    qmlRegisterSingletonInstance(ChartController, QML_URI, 1, 0, "Chart", charts)
    qmlRegisterSingletonInstance(LayoutController, QML_URI, 1, 0, "Layout", layout)
    qmlRegisterSingletonInstance(DisplayController, QML_URI, 1, 0, "Display", displays)
    qmlRegisterSingletonInstance(SettingsController, QML_URI, 1, 0, "Settings", settings)
    qmlRegisterSingletonInstance(TripsController, QML_URI, 1, 0, "Trips", trips)

    engine = QQmlApplicationEngine()
    engine.load(QUrl.fromLocalFile(str(QML_ROOT / "Main.qml")))
    return engine, [
        theme,
        info,
        telemetry,
        chrono,
        chronometer,
        charts,
        settings,
        recorder,
        trips,
        layout,
        displays,
    ]


def main() -> int:
    """Sobe a aplicacao Qt, o laco asyncio e a telemetria.

    Returns:
        Codigo de saida do processo.
    """
    import asyncio
    import signal

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
    provider = create_provider(app_config)
    engine, bridges = build_engine(app_config, bus, provider)
    if not engine.rootObjects():
        logger.error("Falha ao carregar Main.qml")
        return 1

    service = TelemetryService(provider, bus)

    logger.info(
        "Plataforma Qt: %s | provider: %s | amostragem: %dms",
        app.platformName(),
        app_config.provider,
        app_config.sample_interval_ms,
    )

    recorder = bridges[7]

    with loop:
        task = loop.create_task(service.run())
        app.aboutToQuit.connect(task.cancel)

        # Sem tratar SIGTERM, `systemctl stop` mataria o processo direto e a
        # viagem em andamento nunca seria gravada - justamente a viagem que
        # acabou de acontecer. Encaminhando para o quit do Qt, o encerramento
        # segue o mesmo caminho de fechar a janela.
        for signal_number in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(signal_number, app.quit)

        loop.run_forever()

        # Encerra a viagem em andamento antes de fechar o laco: sem isso, um
        # trecho rodado ate o desligamento simplesmente nao existiria no
        # historico.
        loop.run_until_complete(recorder.finish())

    del bridges
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
