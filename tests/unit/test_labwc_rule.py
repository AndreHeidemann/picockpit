"""Testes da regra de compositor para a projecao e a multimidia.

``labwc-rc.xml`` e um recorte de configuracao sem qualquer verificacao do
compositor: XML invalido so aparece quando alguem tenta fundir o arquivo na
maquina, e um numero de geometria dessincronizado nao da erro nenhum - a
janela so aparece sobreposta ou deixa uma faixa preta. Estes testes travam as
duas classes de problema antes do arquivo sair do repositorio.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

RULE_FILE = Path(__file__).resolve().parents[2] / "deployment" / "labwc-rc.xml"

#: Titulo definido em ConsoleWindow.qml - a regra da nossa janela casa por
#: aqui, e nao por app_id, porque cluster e multimidia compartilham o mesmo
#: app_id no Wayland.
CONSOLE_TITLE = "PiCockpit OS - Multimidia"

#: Largura padrao assumida pelas duas regras, com PICOCKPIT_CONSOLE_FRACTION
#: no valor default (0.3) e um display de 1920px de largura.
DISPLAY_WIDTH = 1920


def _rules() -> dict[str, ET.Element]:
    root = ET.parse(RULE_FILE).getroot()
    rules = {}
    for rule in root.iter("windowRule"):
        key = rule.get("identifier") or rule.get("title")
        assert key, f"windowRule sem identifier nem title: {ET.tostring(rule)!r}"
        rules[key] = rule
    return rules


def _resize_width(rule: ET.Element) -> int:
    for action in rule.iter("action"):
        if action.get("name") == "ResizeTo":
            return int(action.get("width"))
    raise AssertionError("windowRule sem action ResizeTo")


def _move_x(rule: ET.Element) -> int:
    for action in rule.iter("action"):
        if action.get("name") == "MoveTo":
            return int(action.get("x"))
    raise AssertionError("windowRule sem action MoveTo")


def test_the_file_is_well_formed_xml() -> None:
    """Regressao: um comentario com `--` ja quebrou este arquivo antes."""
    ET.parse(RULE_FILE)


def test_both_rules_exist() -> None:
    rules = _rules()

    assert "livi" in rules
    assert CONSOLE_TITLE in rules


def test_console_rule_matches_by_title_not_identifier() -> None:
    """Cluster e multimidia compartilham app_id; so o title distingue."""
    console = _rules()[CONSOLE_TITLE]

    assert console.get("title") == CONSOLE_TITLE
    assert console.get("identifier") is None


def test_the_two_widths_fill_the_display_with_no_gap_or_overlap() -> None:
    rules = _rules()
    livi_width = _resize_width(rules["livi"])
    console_width = _resize_width(rules[CONSOLE_TITLE])

    assert livi_width + console_width == DISPLAY_WIDTH


def test_console_sits_flush_right_of_the_projection() -> None:
    rules = _rules()
    livi_width = _resize_width(rules["livi"])
    console_x = _move_x(rules[CONSOLE_TITLE])

    assert _move_x(rules["livi"]) == 0
    assert console_x == livi_width
