"""Testes das definicoes de tema: paleta e geometria."""

import re

import pytest

from picockpit.core.theme import (
    DEFAULT_THEME,
    PALETTES,
    THEMES,
    GaugeStyle,
    Palette,
    ThemeName,
    get_palette,
    get_theme,
)

HEX_COLOR = re.compile(r"^#[0-9A-F]{6}$")


@pytest.mark.parametrize("theme", list(ThemeName))
def test_every_theme_is_registered(theme: ThemeName) -> None:
    definition = THEMES[theme]

    assert definition.name is theme
    assert definition.label
    assert isinstance(definition.palette, Palette)
    assert isinstance(definition.gauge_style, GaugeStyle)


@pytest.mark.parametrize("theme", list(ThemeName))
def test_all_colors_are_uppercase_hex(theme: ThemeName) -> None:
    for value in THEMES[theme].palette.to_dict().values():
        assert HEX_COLOR.match(value), value


@pytest.mark.parametrize("theme", list(ThemeName))
def test_gradient_ends_are_distinct(theme: ThemeName) -> None:
    """Gradiente com as duas pontas iguais seria cor chapada disfarcada."""
    palette = THEMES[theme].palette

    assert palette.primary != palette.primary_dim


@pytest.mark.parametrize("theme", list(ThemeName))
def test_text_contrasts_with_the_background(theme: ThemeName) -> None:
    """Texto principal precisa ser claramente mais luminoso que o fundo."""
    palette = THEMES[theme].palette

    def luminance(color: str) -> float:
        red, green, blue = (int(color[index : index + 2], 16) for index in (1, 3, 5))
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    assert luminance(palette.text) - luminance(palette.background) > 120


def test_labels_are_unique() -> None:
    labels = [definition.label for definition in THEMES.values()]

    assert len(labels) == len(set(labels))


def test_night_theme_is_the_dimmest() -> None:
    """O modo noturno nao pode ofuscar: fundo mais escuro de todos."""
    night = THEMES[ThemeName.NIGHT].palette

    assert night.background == "#000000"


def test_get_theme_accepts_string_and_enum() -> None:
    assert get_theme("sport") is THEMES[ThemeName.SPORT]
    assert get_theme(ThemeName.SPORT) is THEMES[ThemeName.SPORT]


def test_unknown_theme_falls_back_to_default() -> None:
    assert get_theme("inexistente") is THEMES[DEFAULT_THEME]


def test_palette_shortcut_matches_the_definition() -> None:
    assert get_palette("dark") is PALETTES[ThemeName.DARK]
    assert PALETTES[ThemeName.DARK] is THEMES[ThemeName.DARK].palette


def test_both_gauge_styles_are_in_use() -> None:
    """Se todos os temas usassem a mesma geometria, o estilo seria inutil."""
    styles = {definition.gauge_style for definition in THEMES.values()}

    assert styles == set(GaugeStyle)


def test_palette_serializes_every_field() -> None:
    palette = get_palette(ThemeName.NORMAL)

    assert set(palette.to_dict()) == set(Palette.__dataclass_fields__)
