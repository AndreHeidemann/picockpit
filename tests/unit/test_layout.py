"""Testes da composicao de tela."""

import pytest

from picockpit.core.layout import (
    DEFAULT_RATIO,
    PAGES,
    SPLIT_RATIOS,
    LayoutMode,
    find_page,
    find_ratio,
    page_keys,
    splittable_keys,
)


def test_every_page_has_a_unique_key() -> None:
    keys = page_keys()

    assert len(keys) == len(set(keys))


def test_every_page_is_labelled() -> None:
    for page in PAGES:
        assert page.label
        assert page.glyph


def test_settings_cannot_share_the_screen() -> None:
    """Formulario nao e tela de leitura: nao entra em divisao."""
    assert "settings" not in splittable_keys()
    assert "dashboard" in splittable_keys()


def test_find_page_resolves_by_key() -> None:
    assert find_page("charts").label == "Graficos"


def test_unknown_page_falls_back_to_the_first() -> None:
    assert find_page("inexistente") is PAGES[0]


@pytest.mark.parametrize("ratio", SPLIT_RATIOS)
def test_ratios_are_within_bounds(ratio) -> None:
    assert 0.5 <= ratio.value <= 0.8
    assert ratio.label


def test_default_ratio_is_registered() -> None:
    assert DEFAULT_RATIO in SPLIT_RATIOS


def test_find_ratio_snaps_to_the_closest() -> None:
    assert find_ratio(0.52).value == pytest.approx(0.5)
    assert find_ratio(0.68).value == pytest.approx(0.7)
    assert find_ratio(0.95).value == pytest.approx(0.8)


def test_layout_modes_are_stable_strings() -> None:
    assert LayoutMode.SINGLE.value == "single"
    assert LayoutMode.SPLIT.value == "split"
