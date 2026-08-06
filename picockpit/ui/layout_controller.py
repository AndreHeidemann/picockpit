"""Controlador da composicao de tela e dos widgets ativos."""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import Property, QObject, Slot
from PySide6.QtCore import Signal as QtSignal

from picockpit.core.layout import (
    DEFAULT_RATIO,
    PAGES,
    SPLIT_RATIOS,
    LayoutMode,
    find_page,
    find_ratio,
    splittable_keys,
)
from picockpit.data.preferences import PreferenceStore

logger = logging.getLogger(__name__)

KEY_MODE = "layout_mode"
KEY_RATIO = "layout_ratio"
KEY_SECONDARY = "layout_secondary"
KEY_WIDGETS = "widgets"

#: Widgets disponiveis, na ordem de exibicao. Cada um le apenas dos singletons
#: ja expostos - nenhum conhece o outro, que e o que permite ligar e desligar
#: qualquer combinacao sem quebrar o resto.
AVAILABLE_WIDGETS: tuple[tuple[str, str], ...] = (
    ("speed", "Velocidade"),
    ("rpm", "Rotacao"),
    ("consumption", "Consumo"),
    ("range", "Autonomia"),
    ("fuel", "Combustivel"),
    ("temperature", "Temperatura"),
    ("voltage", "Bateria"),
    ("odometer", "Hodometro"),
    ("clock", "Relogio"),
    ("gps", "GPS"),
)

#: Widgets ligados de fabrica.
DEFAULT_WIDGETS: tuple[str, ...] = ("speed", "rpm", "consumption", "range", "fuel", "temperature")


class LayoutController(QObject):
    """Expoe modo de tela, proporcao e widgets ativos ao QML."""

    changed = QtSignal()

    def __init__(
        self,
        preferences: PreferenceStore | None = None,
        parent: QObject | None = None,
    ) -> None:
        """Inicializa o controlador.

        Args:
            preferences: Repositorio das preferencias. Sem ele nada e lembrado.
            parent: Pai Qt opcional.
        """
        super().__init__(parent)
        self._preferences = preferences

    def _stored(self, key: str, default: str) -> str:
        """Le uma preferencia."""
        if self._preferences is None:
            return default
        return self._preferences.get(key, default)

    def _remember(self, key: str, value: str) -> None:
        """Grava uma preferencia, se houver onde gravar."""
        if self._preferences is not None:
            self._preferences.set(key, value)

    # ----------------------------------------------------------------- telas

    @Property("QVariantList", constant=True)  # type: ignore[operator]
    def pages(self) -> list[dict[str, Any]]:
        """Paginas registradas, prontas para a trilha de navegacao."""
        return [
            {
                "key": page.key,
                "label": page.label,
                "glyph": page.glyph,
                "splittable": page.splittable,
            }
            for page in PAGES
        ]

    @Property("QStringList", constant=True)  # type: ignore[operator]
    def splittablePages(self) -> list[str]:  # noqa: N802 - nome consumido pelo QML
        """Paginas que podem ocupar a regiao secundaria."""
        return list(splittable_keys())

    @Slot(str, result=str)
    def labelOf(self, key: str) -> str:  # noqa: N802 - nome consumido pelo QML
        """Nome de exibicao de uma pagina."""
        return find_page(key).label

    # --------------------------------------------------------------- divisao

    @Property(bool, notify=changed)  # type: ignore[operator]
    def split(self) -> bool:
        """Indica se a tela esta dividida."""
        return self._stored(KEY_MODE, LayoutMode.SINGLE.value) == LayoutMode.SPLIT.value

    @Slot(bool)
    def setSplit(self, enabled: bool) -> None:  # noqa: N802 - nome consumido pelo QML
        """Liga ou desliga a divisao de tela."""
        mode = LayoutMode.SPLIT if enabled else LayoutMode.SINGLE
        self._remember(KEY_MODE, mode.value)
        self.changed.emit()

    @Property(float, notify=changed)  # type: ignore[operator]
    def ratio(self) -> float:
        """Fracao ocupada pelo painel principal."""
        if self._preferences is None:
            return DEFAULT_RATIO.value
        return find_ratio(self._preferences.get_float(KEY_RATIO, DEFAULT_RATIO.value)).value

    @Property("QVariantList", constant=True)  # type: ignore[operator]
    def ratioOptions(self) -> list[dict[str, Any]]:  # noqa: N802 - nome consumido pelo QML
        """Proporcoes oferecidas."""
        return [{"value": ratio.value, "label": ratio.label} for ratio in SPLIT_RATIOS]

    @Slot(float)
    def setRatio(self, value: float) -> None:  # noqa: N802 - nome consumido pelo QML
        """Troca a proporcao da divisao."""
        self._remember(KEY_RATIO, str(find_ratio(value).value))
        self.changed.emit()

    @Property(str, notify=changed)  # type: ignore[operator]
    def secondary(self) -> str:
        """Pagina exibida na regiao secundaria."""
        stored = self._stored(KEY_SECONDARY, "charts")
        return stored if stored in splittable_keys() else "charts"

    @Slot(str)
    def setSecondary(self, key: str) -> None:  # noqa: N802 - nome consumido pelo QML
        """Troca a pagina da regiao secundaria."""
        if key not in splittable_keys():
            return
        self._remember(KEY_SECONDARY, key)
        self.changed.emit()

    # --------------------------------------------------------------- widgets

    @Property("QVariantList", constant=True)  # type: ignore[operator]
    def availableWidgets(self) -> list[dict[str, str]]:  # noqa: N802 - nome consumido pelo QML
        """Widgets que podem ser ligados."""
        return [{"key": key, "label": label} for key, label in AVAILABLE_WIDGETS]

    @Property("QStringList", notify=changed)  # type: ignore[operator]
    def widgets(self) -> list[str]:
        """Widgets ativos, na ordem de exibicao."""
        stored = self._stored(KEY_WIDGETS, ",".join(DEFAULT_WIDGETS))
        known = {key for key, _ in AVAILABLE_WIDGETS}
        # Filtrar contra o catalogo protege de preferencia antiga apontando
        # para widget que deixou de existir.
        return [key for key in stored.split(",") if key in known]

    @Slot(str)
    def toggleWidget(self, key: str) -> None:  # noqa: N802 - nome consumido pelo QML
        """Liga ou desliga um widget, preservando a ordem do catalogo."""
        if key not in {available for available, _ in AVAILABLE_WIDGETS}:
            return

        active = set(self.widgets)
        if key in active:
            active.remove(key)
        else:
            active.add(key)

        ordered = [available for available, _ in AVAILABLE_WIDGETS if available in active]
        self._remember(KEY_WIDGETS, ",".join(ordered))
        self.changed.emit()
