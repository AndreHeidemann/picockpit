"""Testes das paletas de tema."""

import re

import pytest

from picockpit.core.theme import DEFAULT_THEME, PALETTES, Palette, ThemeName, get_palette

HEX_COLOR = re.compile(r"^#[0-9A-F]{6}$")


@pytest.mark.parametrize("theme", list(ThemeName))
def test_every_theme_has_a_palette(theme: ThemeName) -> None:
    assert isinstance(PALETTES[theme], Palette)


@pytest.mark.parametrize("theme", list(ThemeName))
def test_all_colors_are_uppercase_hex(theme: ThemeName) -> None:
    for value in PALETTES[theme].to_dict().values():
        assert HEX_COLOR.match(value), value


def test_get_palette_accepts_string_and_enum() -> None:
    assert get_palette("sport") is PALETTES[ThemeName.SPORT]
    assert get_palette(ThemeName.SPORT) is PALETTES[ThemeName.SPORT]


def test_unknown_theme_falls_back_to_default() -> None:
    assert get_palette("inexistente") is PALETTES[DEFAULT_THEME]


def test_palette_serializes_every_field() -> None:
    palette = get_palette(ThemeName.NORMAL)
    assert set(palette.to_dict()) == set(Palette.__dataclass_fields__)
