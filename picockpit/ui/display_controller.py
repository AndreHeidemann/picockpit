"""Distribuicao das janelas entre os displays do veiculo.

A instalacao final tem duas telas com papeis distintos: a do motorista mostra
instrumentos e nao recebe toque, a da multimidia concentra navegacao, ajustes e
a projecao. Este controlador diz a camada QML onde cada janela vai parar - e o
que fazer quando so existe um monitor, que e o caso da bancada.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Property, QObject
from PySide6.QtCore import Signal as QtSignal
from PySide6.QtGui import QGuiApplication

logger = logging.getLogger(__name__)


class DisplayController(QObject):
    """Expoe a configuracao de displays ao QML."""

    changed = QtSignal()

    def __init__(
        self,
        cluster_screen: int = 0,
        console_screen: int = 1,
        console_fraction: float = 0.3,
        parent: QObject | None = None,
    ) -> None:
        """Inicializa o controlador.

        Args:
            cluster_screen: Indice do display do motorista.
            console_screen: Indice do display da multimidia.
            console_fraction: Fracao do display da multimidia reservada a barra
                lateral do PiCockpit.
            parent: Pai Qt opcional.
        """
        super().__init__(parent)
        self._cluster = max(0, cluster_screen)
        self._console = max(0, console_screen)
        self._fraction = min(0.9, max(0.1, console_fraction))

        count = self.screenCount
        if self._cluster >= count or self._console >= count:
            logger.info(
                "Displays configurados (%d e %d) alem dos %d disponiveis; "
                "as duas janelas dividem a mesma tela",
                self._cluster,
                self._console,
                count,
            )

    @Property(int, constant=True)  # type: ignore[operator]
    def screenCount(self) -> int:  # noqa: N802 - nome consumido pelo QML
        """Quantidade de displays conectados."""
        application = QGuiApplication.instance()
        return len(application.screens()) if application else 1

    @Property(bool, notify=changed)  # type: ignore[operator]
    def dual(self) -> bool:
        """Indica se ha display suficiente para separar cluster e multimidia."""
        return self.screenCount > max(self._cluster, self._console)

    @Property(int, notify=changed)  # type: ignore[operator]
    def clusterScreen(self) -> int:  # noqa: N802 - nome consumido pelo QML
        """Indice do display do motorista, limitado ao que existe."""
        return min(self._cluster, self.screenCount - 1)

    @Property(int, notify=changed)  # type: ignore[operator]
    def consoleScreen(self) -> int:  # noqa: N802 - nome consumido pelo QML
        """Indice do display da multimidia, limitado ao que existe."""
        return min(self._console, self.screenCount - 1)

    @Property(float, notify=changed)  # type: ignore[operator]
    def consoleFraction(self) -> float:  # noqa: N802 - nome consumido pelo QML
        """Fracao do display da multimidia ocupada pela barra lateral."""
        return self._fraction
