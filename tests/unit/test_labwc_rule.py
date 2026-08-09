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

#: app_id assumido para o LIVI: o StartupWMClass que o instalador oficial
#: (scripts/install/desktop/install.sh) grava nos atalhos que cria. Palpite,
#: nao garantia - so `lswt -v` na maquina real confirma.
LIVI_IDENTIFIER = "dev.f-io.livi"

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


def _edge_directions(rule: ET.Element) -> set[str]:
    """Direcoes dos `MoveToEdge` da regra.

    Nao usamos mais `MoveTo` com coordenada absoluta: `wlr-randr` mostra as
    saidas lado a lado num unico espaco de coordenadas logico (na maquina
    real, HDMI-A-2 em 1024,0), entao x=0/x=1344 nao encostavam em borda
    nenhuma - mandavam a janela para o desktop virtual inteiro, nao para a
    saida onde ela estava. `MoveToEdge` e relativo a saida atual, imune a
    isso.
    """
    return {
        action.get("direction")
        for action in rule.iter("action")
        if action.get("name") == "MoveToEdge"
    }


def test_the_file_is_well_formed_xml() -> None:
    """Regressao: um comentario com `--` ja quebrou este arquivo antes."""
    ET.parse(RULE_FILE)


def test_both_rules_exist() -> None:
    rules = _rules()

    assert LIVI_IDENTIFIER in rules
    assert CONSOLE_TITLE in rules


def test_console_rule_matches_by_title_not_identifier() -> None:
    """Cluster e multimidia compartilham app_id; so o title distingue."""
    console = _rules()[CONSOLE_TITLE]

    assert console.get("title") == CONSOLE_TITLE
    assert console.get("identifier") is None


def test_the_two_widths_fill_the_display_with_no_gap_or_overlap() -> None:
    rules = _rules()
    livi_width = _resize_width(rules[LIVI_IDENTIFIER])
    console_width = _resize_width(rules[CONSOLE_TITLE])

    assert livi_width + console_width == DISPLAY_WIDTH


def test_livi_hugs_the_left_edge_of_its_own_output() -> None:
    """`MoveToEdge`, nao `MoveTo`: ver comentario de `_edge_directions`."""
    livi = _rules()[LIVI_IDENTIFIER]

    assert "left" in _edge_directions(livi)
    assert "up" in _edge_directions(livi)


def test_console_hugs_the_right_edge_of_its_own_output() -> None:
    """A multimidia encosta a direita - a faixa da esquerda e do LIVI."""
    console = _rules()[CONSOLE_TITLE]

    assert "right" in _edge_directions(console)
    assert "up" in _edge_directions(console)


def test_edge_actions_do_not_snap_to_the_other_window() -> None:
    """snapWindows="no": a ordem de mapeamento entre as duas nao pode importar.

    Com o padrao (`yes`), quem mapear por ultimo poderia parar encostado na
    janela da outra em vez de na borda da tela, se elas already se
    sobrepoem no instante em que a regra roda.
    """
    rules = _rules()
    for rule in (rules[LIVI_IDENTIFIER], rules[CONSOLE_TITLE]):
        for action in rule.iter("action"):
            if action.get("name") == "MoveToEdge":
                assert action.get("snapWindows") == "no"
