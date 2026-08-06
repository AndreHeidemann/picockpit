"""Definicao de temas visuais como dados puros, sem dependencia de Qt.

Mantido no nucleo de proposito: paletas sao configuracao de dominio, precisam
ser testaveis no container headless e serao persistidas junto das preferencias
do usuario (Etapa 12). A camada Qt apenas consome estes valores.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class ThemeName(str, Enum):
    """Temas previstos pelo produto. A troca dinamica e escopo da Etapa 4."""

    NORMAL = "normal"
    SPORT = "sport"
    NIGHT = "night"
    DARK = "dark"
    MINIMAL = "minimal"


@dataclass(frozen=True, slots=True)
class Palette:
    """Cores de um tema, em notacao hexadecimal ``#RRGGBB``.

    Attributes:
        background: Fundo da janela.
        surface: Fundo de paineis e cartoes.
        surface_alt: Variante de superficie para realce sutil.
        primary: Cor de acento principal (ponteiros, selecao).
        secondary: Cor de acento secundaria.
        text: Texto de alta enfase.
        text_muted: Texto de baixa enfase.
        warning: Estado de atencao.
        danger: Estado critico.
        success: Estado normal ou confirmacao.
    """

    background: str
    surface: str
    surface_alt: str
    primary: str
    secondary: str
    text: str
    text_muted: str
    warning: str
    danger: str
    success: str

    def to_dict(self) -> dict[str, str]:
        """Serializa a paleta para consumo pela camada QML."""
        return asdict(self)


#: Paletas registradas. `normal` e o padrao de fabrica.
PALETTES: dict[ThemeName, Palette] = {
    ThemeName.NORMAL: Palette(
        background="#0B0E14",
        surface="#141922",
        surface_alt="#1D2430",
        primary="#3DA9FC",
        secondary="#7C89A0",
        text="#F2F5FA",
        text_muted="#8A94A6",
        warning="#F5A623",
        danger="#E5484D",
        success="#31C48D",
    ),
    ThemeName.SPORT: Palette(
        background="#0A0000",
        surface="#180505",
        surface_alt="#241010",
        primary="#FF2E2E",
        secondary="#FF8A3D",
        text="#FFFFFF",
        text_muted="#B08A8A",
        warning="#FFB020",
        danger="#FF2E2E",
        success="#3DDC84",
    ),
    ThemeName.NIGHT: Palette(
        background="#000000",
        surface="#0A0A0A",
        surface_alt="#141414",
        primary="#FF6B2C",
        secondary="#8C4A24",
        text="#E8D5C4",
        text_muted="#7A6656",
        warning="#C98A2B",
        danger="#B23A3A",
        success="#4A8C6A",
    ),
    ThemeName.DARK: Palette(
        background="#101012",
        surface="#18181B",
        surface_alt="#232327",
        primary="#A1A1AA",
        secondary="#52525B",
        text="#FAFAFA",
        text_muted="#71717A",
        warning="#EAB308",
        danger="#DC2626",
        success="#16A34A",
    ),
    ThemeName.MINIMAL: Palette(
        background="#000000",
        surface="#000000",
        surface_alt="#0D0D0D",
        primary="#FFFFFF",
        secondary="#4D4D4D",
        text="#FFFFFF",
        text_muted="#6B6B6B",
        warning="#FFFFFF",
        danger="#FFFFFF",
        success="#FFFFFF",
    ),
}

DEFAULT_THEME = ThemeName.NORMAL


def get_palette(name: str | ThemeName) -> Palette:
    """Resolve uma paleta pelo nome, caindo no tema padrao se desconhecido.

    Args:
        name: Nome do tema.

    Returns:
        Paleta correspondente, ou a paleta padrao se o nome nao existir.
    """
    try:
        theme = ThemeName(name)
    except ValueError:
        theme = DEFAULT_THEME
    return PALETTES[theme]
