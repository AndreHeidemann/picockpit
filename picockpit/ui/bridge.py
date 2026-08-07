"""Ponte entre o dominio Python e a camada QML.

Objetos expostos aqui sao a unica superficie que o QML enxerta do Python. Manter
essa fronteira estreita e o que permite trocar a origem dos dados (simulacao,
OBD-II, CAN) sem reescrever a interface.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Property, QObject, Signal, Slot

from picockpit.core.theme import DEFAULT_THEME, ThemeName, get_theme

logger = logging.getLogger(__name__)

#: Amostras de FPS agregadas antes de escrever uma linha de log.
FPS_WINDOW = 5


class ThemeController(QObject):
    """Expoe a paleta ativa ao QML e permite troca em tempo de execucao.

    A troca dinamica completa e escopo da Etapa 4; a infraestrutura de
    notificacao ja fica pronta aqui para nao exigir refatoracao da UI depois.
    """

    #: Emitido sempre que o tema ativo muda; QML reavalia os bindings.
    changed = Signal()

    def __init__(self, initial: str = DEFAULT_THEME.value, parent: QObject | None = None) -> None:
        """Inicializa o controlador com o tema informado."""
        super().__init__(parent)
        self._theme = get_theme(initial)
        self._name = initial

    @Property(str, notify=changed)  # type: ignore[operator]
    def name(self) -> str:
        """Nome do tema ativo."""
        return self._name

    @Property("QVariantMap", notify=changed)  # type: ignore[operator]
    def colors(self) -> dict[str, str]:
        """Paleta ativa como mapa consumivel por bindings QML."""
        return self._theme.palette.to_dict()

    @Property(str, notify=changed)  # type: ignore[operator]
    def label(self) -> str:
        """Nome do tema ativo como aparece na interface."""
        return self._theme.label

    @Property(str, notify=changed)  # type: ignore[operator]
    def gaugeStyle(self) -> str:  # noqa: N802 - nome consumido pelo QML
        """Geometria do mostrador principal: ``segment`` ou ``arc``."""
        return self._theme.gauge_style.value

    @Property("QVariantMap", notify=changed)  # type: ignore[operator]
    def gauge(self) -> dict[str, float | int]:
        """Proporcoes e tipografia do mostrador do tema ativo."""
        return self._theme.gauge.to_dict()

    @Slot(str, result=str)
    def labelOf(self, name: str) -> str:  # noqa: N802 - nome consumido pelo QML
        """Nome de exibicao de um tema qualquer.

        Args:
            name: Identificador do tema.

        Returns:
            Rotulo correspondente.
        """
        return get_theme(name).label

    @Property("QStringList", constant=True)  # type: ignore[operator]
    def available(self) -> list[str]:
        """Nomes de todos os temas disponiveis."""
        return [theme.value for theme in ThemeName]

    @Slot(str)
    def activate(self, name: str) -> None:
        """Ativa o tema informado, ignorando nomes desconhecidos.

        Args:
            name: Nome do tema a ativar.
        """
        theme = get_theme(name)
        if theme is self._theme:
            return
        self._name = name
        self._theme = theme
        self.changed.emit()


class AppInfo(QObject):
    """Metadados estaticos da aplicacao, usados na barra superior."""

    def __init__(
        self,
        version: str,
        env: str,
        target_fps: int = 60,
        kiosk: bool = False,
        parent: QObject | None = None,
    ) -> None:
        """Inicializa com versao, ambiente, alvo de FPS e modo de exibicao."""
        super().__init__(parent)
        self._version = version
        self._env = env
        self._target_fps = target_fps
        self._kiosk = kiosk
        self._fps_samples: list[int] = []

    @Property(str, constant=True)  # type: ignore[operator]
    def version(self) -> str:
        """Versao do PiCockpit OS."""
        return self._version

    @Property(str, constant=True)  # type: ignore[operator]
    def env(self) -> str:
        """Ambiente logico em execucao."""
        return self._env

    @Property(int, constant=True)  # type: ignore[operator]
    def targetFps(self) -> int:  # noqa: N802 - nome consumido pelo QML
        """Taxa de quadros alvo, usada como referencia pelo medidor de FPS."""
        return self._target_fps

    @Property(bool, constant=True)  # type: ignore[operator]
    def kiosk(self) -> bool:
        """Indica se a janela deve abrir em tela cheia."""
        return self._kiosk

    @Slot(int)
    def reportFps(self, fps: int) -> None:  # noqa: N802 - nome consumido pelo QML
        """Registra o FPS medido pela interface.

        Medir FPS olhando a tela pelo Raspberry Pi Connect e enganoso: a
        codificacao de video do compartilhamento consome o mesmo hardware que
        se pretende medir. Registrando no log, a medicao continua disponivel
        com a sessao de visualizacao fechada.

        Args:
            fps: Quadros renderizados no ultimo segundo.
        """
        self._fps_samples.append(fps)
        if len(self._fps_samples) < FPS_WINDOW:
            return

        samples = self._fps_samples
        self._fps_samples = []

        # DEBUG de proposito: uma linha a cada 5s daria cerca de 2 MB por dia
        # de escrita continua no cartao SD. Para medir, subir com
        # PICOCKPIT_LOG_LEVEL=DEBUG.
        logger.debug(
            "FPS janela de %ds: min=%d media=%.1f max=%d (alvo=%d)",
            len(samples),
            min(samples),
            sum(samples) / len(samples),
            max(samples),
            self._target_fps,
        )
