"""Testes da ponte de temas. Executa apenas no Raspberry Pi."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.ui

pytest.importorskip("PySide6", reason="PySide6 so existe no Raspberry Pi")

from picockpit.core.theme import DEFAULT_THEME, THEMES, ThemeName  # noqa: E402


@pytest.fixture
def controller():
    from picockpit.ui.bridge import ThemeController

    return ThemeController()


def test_starts_on_the_default_theme(controller) -> None:
    assert controller.name == DEFAULT_THEME.value


def test_activating_changes_the_palette(controller) -> None:
    controller.activate(ThemeName.SPORT.value)

    assert controller.name == ThemeName.SPORT.value
    assert controller.colors == THEMES[ThemeName.SPORT].palette.to_dict()
    assert controller.gauge == THEMES[ThemeName.SPORT].gauge.to_dict()


def test_unknown_theme_is_ignored(controller) -> None:
    """Nome invalido nao pode deixar a interface sem paleta."""
    controller.activate("inexistente")

    assert controller.name == DEFAULT_THEME.value


# ------------------------------------------------- consultas para a previa
#
# A tela de ajustes desenha os cinco temas ao mesmo tempo, incluindo os que
# nao estao ativos. Sem estes acessos a previa so poderia mostrar o nome.


@pytest.mark.parametrize("theme", list(ThemeName))
def test_palette_of_any_theme_is_reachable(controller, theme: ThemeName) -> None:
    assert controller.paletteOf(theme.value) == THEMES[theme].palette.to_dict()


@pytest.mark.parametrize("theme", list(ThemeName))
def test_geometry_of_any_theme_is_reachable(controller, theme: ThemeName) -> None:
    assert controller.gaugeOf(theme.value) == THEMES[theme].gauge.to_dict()


@pytest.mark.parametrize("theme", list(ThemeName))
def test_style_of_any_theme_is_reachable(controller, theme: ThemeName) -> None:
    assert controller.styleOf(theme.value) == THEMES[theme].gauge_style.value


def test_preview_queries_do_not_depend_on_the_active_theme(controller) -> None:
    """A previa de Track e a mesma com Night ativo ou com Simple ativo."""
    controller.activate(ThemeName.NIGHT.value)
    with_night = controller.gaugeOf(ThemeName.SPORT.value)
    controller.activate(ThemeName.NORMAL.value)

    assert controller.gaugeOf(ThemeName.SPORT.value) == with_night


def test_preview_queries_fall_back_instead_of_failing(controller) -> None:
    """Nome desconhecido devolve o padrao: a previa nao pode ficar sem dados."""
    assert controller.paletteOf("inexistente") == THEMES[DEFAULT_THEME].palette.to_dict()
    assert controller.gaugeOf("inexistente") == THEMES[DEFAULT_THEME].gauge.to_dict()
    assert controller.styleOf("inexistente") == THEMES[DEFAULT_THEME].gauge_style.value


def test_every_available_name_resolves(controller) -> None:
    """`available` alimenta o Repeater da previa; todo nome dali tem de existir."""
    for name in controller.available:
        assert controller.paletteOf(name)
        assert controller.gaugeOf(name)
        assert controller.styleOf(name)
