"""Distribuicao das janelas entre os displays do veiculo.

A instalacao final tem duas telas com papeis distintos: a do motorista mostra
instrumentos e nao recebe toque, a da multimidia concentra navegacao, ajustes e
a projecao.

Este controlador calcula a geometria de cada janela e cobre tres arranjos:

- **duas telas**: cada janela ocupa a sua, em tela cheia
- **uma tela, dois papeis**: `cluster_screen` e `console_screen` apontando para
  o mesmo indice; a tela e dividida entre as duas janelas. E o arranjo de
  desenvolvimento, porque o compartilhamento do Raspberry Pi Connect exibe uma
  saida so e nao permite escolher qual - com as janelas separadas em saidas
  diferentes, metade do sistema fica invisivel remotamente
- **uma tela, uma janela**: sem display suficiente, so a multimidia aparece, com
  o painel como primeira pagina
"""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import Property, QObject
from PySide6.QtCore import Signal as QtSignal
from PySide6.QtGui import QGuiApplication

logger = logging.getLogger(__name__)


class DisplayController(QObject):
    """Expoe a configuracao e a geometria das janelas ao QML."""

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
            console_screen: Indice do display da multimidia. Igual ao do
                cluster significa dividir a mesma tela entre os dois.
            console_fraction: Fracao reservada a barra lateral da multimidia.
            parent: Pai Qt opcional.
        """
        super().__init__(parent)
        self._cluster = max(0, cluster_screen)
        self._console = max(0, console_screen)
        self._fraction = min(0.9, max(0.1, console_fraction))

        count = self.screenCount
        if self.shared:
            logger.info(
                "Cluster e multimidia dividindo o display %d: %d%% e %d%%",
                self.clusterScreen,
                round((1 - self._fraction) * 100),
                round(self._fraction * 100),
            )
        elif not self.dual:
            logger.info(
                "Displays configurados (%d e %d) alem dos %d disponiveis; "
                "apenas a multimidia sera exibida",
                self._cluster,
                self._console,
                count,
            )

    # ------------------------------------------------------------- arranjo

    @Property(int, constant=True)  # type: ignore[operator]
    def screenCount(self) -> int:  # noqa: N802 - nome consumido pelo QML
        """Quantidade de displays conectados."""
        application = QGuiApplication.instance()
        return len(application.screens()) if application else 1

    @Property(bool, notify=changed)  # type: ignore[operator]
    def shared(self) -> bool:
        """Indica que as duas janelas dividem o mesmo display."""
        return self._cluster == self._console and self.screenCount > self._cluster

    @Property(bool, notify=changed)  # type: ignore[operator]
    def dual(self) -> bool:
        """Indica se o cluster deve existir como janela propria.

        Dividindo a tela o cluster existe, mas como regiao da janela da
        multimidia - nao como janela.
        """
        return not self.shared and self.screenCount > max(self._cluster, self._console)

    @Property(int, notify=changed)  # type: ignore[operator]
    def clusterScreen(self) -> int:  # noqa: N802 - nome consumido pelo QML
        """Indice do display do cluster, limitado ao que existe."""
        return min(self._cluster, self.screenCount - 1)

    @Property(int, notify=changed)  # type: ignore[operator]
    def consoleScreen(self) -> int:  # noqa: N802 - nome consumido pelo QML
        """Indice do display da multimidia, limitado ao que existe."""
        return min(self._console, self.screenCount - 1)

    @Property(float, notify=changed)  # type: ignore[operator]
    def consoleFraction(self) -> float:  # noqa: N802 - nome consumido pelo QML
        """Fracao reservada a multimidia quando ela divide a tela."""
        return self._fraction

    # ----------------------------------------------------------- geometria

    def _screen_size(self, index: int) -> tuple[int, int]:
        """Tamanho do display informado, com valor de reserva."""
        application = QGuiApplication.instance()
        screens = application.screens() if application else []
        if not screens:
            return 1920, 1080
        geometry = screens[min(index, len(screens) - 1)].geometry()
        return geometry.width(), geometry.height()

    @Property("QVariantMap", notify=changed)  # type: ignore[operator]
    def clusterGeometry(self) -> dict[str, Any]:  # noqa: N802 - nome consumido pelo QML
        """Posicao e tamanho da janela do cluster, na tela dele."""
        width, height = self._screen_size(self.clusterScreen)
        if self.shared:
            return {"x": 0, "y": 0, "width": round(width * (1 - self._fraction)), "height": height}
        return {"x": 0, "y": 0, "width": width, "height": height}

    @Property("QVariantMap", notify=changed)  # type: ignore[operator]
    def consoleGeometry(self) -> dict[str, Any]:  # noqa: N802 - nome consumido pelo QML
        """Posicao e tamanho da janela da multimidia, na tela dela.

        Dividindo a tela, a janela da multimidia ocupa o display inteiro e
        hospeda as duas regioes. No Wayland a aplicacao nao escolhe onde cada
        janela aparece - posicionamento e prerrogativa do compositor -, entao
        duas janelas lado a lado so acontecem quando cada uma tem a sua tela.
        """
        width, height = self._screen_size(self.consoleScreen)
        if self.shared:
            return {"x": 0, "y": 0, "width": width, "height": height}
        if not self.dual:
            return {"x": 0, "y": 0, "width": width, "height": height}
        # Com tela propria a projecao fica encostada a esquerda (regra do
        # labwc, ver deployment/labwc-rc.xml) - a multimidia precisa ceder
        # essa faixa em vez de tomar o display inteiro, senao as duas janelas
        # disputam o mesmo canto.
        console_width = round(width * self._fraction)
        return {"x": width - console_width, "y": 0, "width": console_width, "height": height}

    @Property(bool, notify=changed)  # type: ignore[operator]
    def clusterFullscreenAllowed(self) -> bool:  # noqa: N802 - nome consumido pelo QML
        """Indica se a janela do cluster pode ir a tela cheia.

        Sempre pode: quando ela existe como janela propria (`dual`), tem uma
        saida HDMI so para si - a projecao nunca disputa essa tela.
        """
        return True

    @Property(bool, notify=changed)  # type: ignore[operator]
    def consoleFullscreenAllowed(self) -> bool:  # noqa: N802 - nome consumido pelo QML
        """Indica se a janela da multimidia pode ir a tela cheia.

        So quando ela e a unica coisa no display: dividindo a tela (`shared`,
        onde a janela compoe as duas regioes por dentro) ou sem tela dedicada
        ao cluster. Com tela propria e a projecao ao lado (`dual`), tela cheia
        via `Window.FullScreen` faz o Wayland ignorar `consoleGeometry` e
        cobrir a saida inteira - foi assim que a faixa reservada ao LIVI
        sumiu na pratica, mesmo com a geometria calculada certa.
        """
        return not self.dual
