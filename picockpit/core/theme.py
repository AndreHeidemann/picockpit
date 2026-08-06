"""Definicao dos temas visuais como dados puros, sem dependencia de Qt.

Um tema aqui nao e so paleta: carrega tambem a geometria do mostrador. Essa
distincao existe porque modo esportivo de painel automotivo nao e o modo
conforto pintado de vermelho - muda o desenho do instrumento, nao so a cor.

Mantido no nucleo de proposito: temas sao configuracao de dominio, precisam ser
testaveis no container e serao persistidos junto das preferencias do usuario
(Etapa 12). A camada Qt apenas consome estes valores.

A linguagem visual se inspira em clusters digitais contemporaneos - gradiente
saturado, segmentacao angular, escala ao longo do arco. Geometria, proporcoes e
paleta sao proprias.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class ThemeName(str, Enum):
    """Temas disponiveis."""

    NORMAL = "normal"
    SPORT = "sport"
    NIGHT = "night"
    DARK = "dark"
    MINIMAL = "minimal"


class GaugeStyle(str, Enum):
    """Geometria do mostrador principal.

    ``SEGMENT`` preenche setores com gradiente e separadores angulares.
    ``ARC`` desenha apenas um traco fino de contorno, mais discreto.
    """

    SEGMENT = "segment"
    ARC = "arc"


@dataclass(frozen=True, slots=True)
class Palette:
    """Cores de um tema, em notacao hexadecimal ``#RRGGBB``.

    Attributes:
        background: Fundo da janela.
        surface: Fundo de paineis e cartoes.
        surface_alt: Variante de superficie para realce sutil.
        primary: Extremidade clara do acento, usada no fim do gradiente.
        primary_dim: Extremidade escura do acento, usada no inicio do gradiente.
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
    primary_dim: str
    secondary: str
    text: str
    text_muted: str
    warning: str
    danger: str
    success: str

    def to_dict(self) -> dict[str, str]:
        """Serializa a paleta para consumo pela camada QML."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ThemeDefinition:
    """Tema completo: identidade, paleta e geometria do mostrador.

    Attributes:
        name: Identificador estavel, usado em configuracao e persistencia.
        label: Nome exibido na interface.
        palette: Cores do tema.
        gauge_style: Geometria do mostrador principal.
    """

    name: ThemeName
    label: str
    palette: Palette
    gauge_style: GaugeStyle


#: Temas registrados. `normal` e o padrao de fabrica.
THEMES: dict[ThemeName, ThemeDefinition] = {
    ThemeName.NORMAL: ThemeDefinition(
        name=ThemeName.NORMAL,
        label="Simple",
        gauge_style=GaugeStyle.SEGMENT,
        palette=Palette(
            background="#05070C",
            surface="#0B111A",
            surface_alt="#16202E",
            primary="#5FD0FF",
            primary_dim="#1B4FD8",
            secondary="#6B8098",
            text="#FFFFFF",
            text_muted="#7C8CA0",
            warning="#F5A623",
            danger="#E5484D",
            success="#31C48D",
        ),
    ),
    ThemeName.SPORT: ThemeDefinition(
        name=ThemeName.SPORT,
        label="Track",
        gauge_style=GaugeStyle.SEGMENT,
        palette=Palette(
            background="#0A0603",
            surface="#150C05",
            surface_alt="#24160B",
            primary="#FFC24A",
            primary_dim="#E05A00",
            secondary="#A8763C",
            text="#FFFFFF",
            text_muted="#A98C6B",
            warning="#FFC24A",
            danger="#FF3B30",
            success="#3DDC84",
        ),
    ),
    ThemeName.DARK: ThemeDefinition(
        name=ThemeName.DARK,
        label="Technology",
        gauge_style=GaugeStyle.SEGMENT,
        palette=Palette(
            background="#08060A",
            surface="#120A14",
            surface_alt="#22111F",
            primary="#FF7A45",
            primary_dim="#C7166B",
            secondary="#8C5A72",
            text="#FFFFFF",
            text_muted="#9A7F8C",
            warning="#FFB020",
            danger="#FF2D55",
            success="#2FD07A",
        ),
    ),
    ThemeName.MINIMAL: ThemeDefinition(
        name=ThemeName.MINIMAL,
        label="Comfort",
        gauge_style=GaugeStyle.ARC,
        palette=Palette(
            background="#06080B",
            surface="#0C1116",
            surface_alt="#1A2129",
            primary="#EDF1F6",
            primary_dim="#8C99A8",
            secondary="#5B6774",
            text="#FFFFFF",
            text_muted="#7E8B99",
            warning="#E2B457",
            danger="#E06C6C",
            success="#7FC9A4",
        ),
    ),
    ThemeName.NIGHT: ThemeDefinition(
        name=ThemeName.NIGHT,
        label="Night",
        gauge_style=GaugeStyle.ARC,
        palette=Palette(
            # Luminancia baixa de proposito: o painel nao pode ofuscar o
            # motorista a noite, e vermelho e ambar preservam a visao escura.
            background="#000000",
            surface="#080604",
            surface_alt="#14100B",
            primary="#FF8A3D",
            primary_dim="#8A3B12",
            secondary="#6B4A2E",
            text="#E8D5C4",
            text_muted="#7A6656",
            warning="#C98A2B",
            danger="#B23A3A",
            success="#4A8C6A",
        ),
    ),
}

#: Compatibilidade: acesso direto as paletas por nome de tema.
PALETTES: dict[ThemeName, Palette] = {
    name: definition.palette for name, definition in THEMES.items()
}

DEFAULT_THEME = ThemeName.NORMAL


def get_theme(name: str | ThemeName) -> ThemeDefinition:
    """Resolve um tema pelo nome, caindo no padrao se desconhecido.

    Args:
        name: Nome do tema.

    Returns:
        Definicao correspondente, ou a do tema padrao.
    """
    try:
        theme = ThemeName(name)
    except ValueError:
        theme = DEFAULT_THEME
    return THEMES[theme]


def get_palette(name: str | ThemeName) -> Palette:
    """Resolve a paleta de um tema pelo nome.

    Args:
        name: Nome do tema.

    Returns:
        Paleta correspondente, ou a do tema padrao se o nome nao existir.
    """
    return get_theme(name).palette
