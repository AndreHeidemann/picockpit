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
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from picockpit import __version__
from picockpit.core.config import AppConfig, load_config
from picockpit.core.logging_setup import setup_logging
from picockpit.ui.bridge import AppInfo, ThemeController

logger = logging.getLogger(__name__)

QML_ROOT = Path(__file__).resolve().parent.parent / "ui" / "qml"


def build_engine(app_config: AppConfig) -> tuple[QQmlApplicationEngine, list[object]]:
    """Cria o engine QML com a ponte Python ja registrada.

    Args:
        app_config: Configuracao efetiva da aplicacao.

    Returns:
        O engine e a lista de objetos de ponte, que precisam ser mantidos vivos
        pelo chamador para nao serem coletados pelo garbage collector.
    """
    engine = QQmlApplicationEngine()

    theme = ThemeController(app_config.theme)
    info = AppInfo(version=__version__, env=app_config.env)

    context = engine.rootContext()
    context.setContextProperty("Theme", theme)
    context.setContextProperty("AppInfo", info)
    context.setContextProperty("targetFps", app_config.target_fps)

    engine.load(QUrl.fromLocalFile(str(QML_ROOT / "Main.qml")))
    return engine, [theme, info]


def main() -> int:
    """Sobe a aplicacao Qt e entra no loop de eventos.

    Returns:
        Codigo de saida do processo.
    """
    app_config = load_config()
    setup_logging(level=app_config.log_level, log_dir=app_config.log_dir)

    logger.info("PiCockpit OS %s iniciando (env=%s)", __version__, app_config.env)

    app = QGuiApplication(sys.argv)
    app.setApplicationName("PiCockpit OS")
    app.setApplicationVersion(__version__)

    # Estilo Basic: sem dependencia de tema do sistema e sem custo extra de
    # renderizacao. A identidade visual vem inteira da nossa paleta.
    QQuickStyle.setStyle("Basic")

    engine, bridges = build_engine(app_config)
    if not engine.rootObjects():
        logger.error("Falha ao carregar Main.qml")
        return 1

    logger.info("Plataforma Qt em uso: %s", app.platformName())
    exit_code: int = app.exec()
    del bridges
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
