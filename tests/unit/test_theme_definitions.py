"""Testes das definicoes de tema: paleta e geometria."""

import re

import pytest

from picockpit.core.theme import (
    DEFAULT_THEME,
    PALETTES,
    THEMES,
    GaugeGeometry,
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


# ------------------------------------------------------ geometria do mostrador


@pytest.mark.parametrize("theme", list(ThemeName))
def test_every_theme_carries_a_geometry(theme: ThemeName) -> None:
    assert isinstance(THEMES[theme].gauge, GaugeGeometry)


@pytest.mark.parametrize("theme", list(ThemeName))
def test_the_arc_never_closes_on_itself(theme: ThemeName) -> None:
    """O vao de baixo e o que da forma de mostrador ao anel.

    Passando de 360 graus o desenho vira uma rosca fechada; abaixo de 90 nao
    sobra arco util para a escala.
    """
    sweep = THEMES[theme].gauge.sweep_degrees

    assert 90.0 <= sweep <= 340.0


@pytest.mark.parametrize("theme", list(ThemeName))
def test_the_ring_fits_inside_its_own_radius(theme: ThemeName) -> None:
    """Espessura maior que o raio comeria o numeral central."""
    assert 0.0 < THEMES[theme].gauge.thickness_ratio < 0.5


@pytest.mark.parametrize("theme", list(ThemeName))
def test_the_central_numeral_stays_readable(theme: ThemeName) -> None:
    geometry = THEMES[theme].gauge

    assert 0.25 <= geometry.value_ratio <= 0.6
    assert 1 <= geometry.value_weight <= 99


@pytest.mark.parametrize("theme", list(ThemeName))
def test_separator_count_is_not_negative(theme: ThemeName) -> None:
    """Zero e valido - anel liso; negativo desenharia separadores ao contrario."""
    assert THEMES[theme].gauge.separator_count >= 0
    assert THEMES[theme].gauge.tick_width >= 1


@pytest.mark.parametrize("theme", list(ThemeName))
def test_scale_factor_never_multiplies_the_marks(theme: ThemeName) -> None:
    """A pagina pede as marcas; o tema so pode rarefazer, nunca inventar."""
    assert 0.0 <= THEMES[theme].gauge.scale_steps_factor <= 1.0


def test_arc_themes_are_thinner_than_segment_themes() -> None:
    """Sem isto o estilo de arco viraria uma faixa grossa, nao um traco."""
    arcs = [t.gauge.thickness_ratio for t in THEMES.values() if t.gauge_style is GaugeStyle.ARC]
    segments = [
        t.gauge.thickness_ratio for t in THEMES.values() if t.gauge_style is GaugeStyle.SEGMENT
    ]

    assert max(arcs) < min(segments)


def test_no_two_themes_share_the_same_drawing() -> None:
    """O ponto do trabalho: cinco modos, cinco instrumentos distintos.

    Ate aqui tres temas eram o mesmo desenho com outra cor. Este teste e o que
    impede a regressao silenciosa de volta para isso.
    """
    drawings = {theme.gauge for theme in THEMES.values()}

    assert len(drawings) == len(THEMES)


def test_night_shows_the_least_lit_area() -> None:
    """Coerencia com a paleta: o modo noturno acende o minimo em tudo."""
    night = THEMES[ThemeName.NIGHT].gauge
    others = [t.gauge for name, t in THEMES.items() if name is not ThemeName.NIGHT]

    assert night.thickness_ratio == min(g.thickness_ratio for g in [night, *others])
    assert night.sweep_degrees == min(g.sweep_degrees for g in [night, *others])


def test_track_is_the_boldest() -> None:
    track = THEMES[ThemeName.SPORT].gauge

    assert track.sweep_degrees == max(t.gauge.sweep_degrees for t in THEMES.values())
    assert track.thickness_ratio == max(t.gauge.thickness_ratio for t in THEMES.values())
    assert track.value_weight == max(t.gauge.value_weight for t in THEMES.values())


def test_geometry_serializes_every_field() -> None:
    geometry = get_theme(ThemeName.NORMAL).gauge

    assert set(geometry.to_dict()) == set(GaugeGeometry.__dataclass_fields__)


def test_the_picker_order_starts_sober_and_ends_at_night() -> None:
    """A ordem do enum e a ordem do seletor; Night fecha por ser modo de uso."""
    order = [theme.value for theme in ThemeName]

    assert order[0] == ThemeName.NORMAL.value
    assert order[-1] == ThemeName.NIGHT.value


def test_every_stored_name_still_resolves() -> None:
    """Reordenar o enum nao pode invalidar preferencia ja gravada."""
    for stored in ("normal", "sport", "night", "dark", "minimal"):
        assert get_theme(stored).name.value == stored
