"""Ponte entre o dominio Python e a camada QML.

Objetos expostos aqui sao a unica superficie que o QML enxerta do Python. Manter
essa fronteira estreita e o que permite trocar a origem dos dados (simulacao,
OBD-II, CAN) sem reescrever a interface.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from picockpit.core.theme import DEFAULT_THEME, ThemeName, get_palette


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
        self._palette = get_palette(initial)
        self._name = initial

    @Property(str, notify=changed)  # type: ignore[operator]
    def name(self) -> str:
        """Nome do tema ativo."""
        return self._name

    @Property("QVariantMap", notify=changed)  # type: ignore[operator]
    def colors(self) -> dict[str, str]:
        """Paleta ativa como mapa consumivel por bindings QML."""
        return self._palette.to_dict()

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
        palette = get_palette(name)
        if palette is self._palette:
            return
        self._name = name
        self._palette = palette
        self.changed.emit()


class AppInfo(QObject):
    """Metadados estaticos da aplicacao, usados na barra superior."""

    def __init__(self, version: str, env: str, parent: QObject | None = None) -> None:
        """Inicializa com versao e ambiente correntes."""
        super().__init__(parent)
        self._version = version
        self._env = env

    @Property(str, constant=True)  # type: ignore[operator]
    def version(self) -> str:
        """Versao do PiCockpit OS."""
        return self._version

    @Property(str, constant=True)  # type: ignore[operator]
    def env(self) -> str:
        """Ambiente logico em execucao."""
        return self._env
