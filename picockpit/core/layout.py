"""Composicao da tela: modos de divisao e paginas disponiveis.

Tela dividida e sistema de widgets sao o mesmo problema visto de dois angulos -
blocos independentes ocupando regioes configuraveis. O que muda e a granularidade:
uma pagina inteira de um lado, ou varios cartoes pequenos num painel.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LayoutMode(str, Enum):
    """Como a area de conteudo e dividida."""

    SINGLE = "single"
    SPLIT = "split"


@dataclass(frozen=True, slots=True)
class SplitRatio:
    """Proporcao de uma divisao.

    Attributes:
        value: Fracao ocupada pelo painel principal, de 0 a 1.
        label: Como a proporcao aparece na interface.
    """

    value: float
    label: str


#: Proporcoes oferecidas. Divisoes muito desiguais deixam o painel secundario
#: menor do que o menor widget util, e por isso 80/20 e o limite.
SPLIT_RATIOS: tuple[SplitRatio, ...] = (
    SplitRatio(0.5, "50/50"),
    SplitRatio(0.7, "70/30"),
    SplitRatio(0.8, "80/20"),
)

DEFAULT_RATIO = SPLIT_RATIOS[1]


@dataclass(frozen=True, slots=True)
class PageInfo:
    """Pagina que pode ocupar uma regiao da tela.

    Attributes:
        key: Identificador estavel, usado em configuracao e persistencia.
        label: Nome exibido.
        glyph: Simbolo usado na trilha de navegacao.
        splittable: Se a pagina pode ocupar uma regiao de tela dividida.
            Ajustes fica de fora: e uma tela de formulario, nao de leitura.
    """

    key: str
    label: str
    glyph: str
    splittable: bool = True


#: Paginas registradas, na ordem em que aparecem na trilha de navegacao.
PAGES: tuple[PageInfo, ...] = (
    PageInfo("dashboard", "Painel", "◴"),
    PageInfo("performance", "Tempos", "⏱"),
    PageInfo("charts", "Graficos", "◫"),
    PageInfo("widgets", "Widgets", "▦"),
    PageInfo("trips", "Viagens", "▤"),
    PageInfo("media", "Media", "▶"),
    PageInfo("settings", "Ajustes", "⚙", splittable=False),
)


def page_keys() -> tuple[str, ...]:
    """Identificadores de todas as paginas."""
    return tuple(page.key for page in PAGES)


def splittable_keys() -> tuple[str, ...]:
    """Identificadores das paginas que podem dividir a tela."""
    return tuple(page.key for page in PAGES if page.splittable)


def find_page(key: str) -> PageInfo:
    """Resolve uma pagina pelo identificador.

    Args:
        key: Identificador procurado.

    Returns:
        A pagina correspondente, ou a primeira registrada se o nome nao existir.
    """
    for page in PAGES:
        if page.key == key:
            return page
    return PAGES[0]


def find_ratio(value: float) -> SplitRatio:
    """Resolve a proporcao mais proxima do valor informado.

    Args:
        value: Fracao desejada.

    Returns:
        A proporcao registrada mais proxima.
    """
    return min(SPLIT_RATIOS, key=lambda ratio: abs(ratio.value - value))
