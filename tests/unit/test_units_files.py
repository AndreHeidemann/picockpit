"""Testes dos arquivos de unidade do systemd.

Arquivo de unidade e configuracao sem compilador: chave escrita na secao errada
nao gera erro, nao aparece no log, e o comportamento que ela deveria produzir
simplesmente nao acontece. Foi o que houve com o limitador de reinicio - ele
estava em ``[Service]``, onde o systemd nao le, e a unidade da projecao
acumulou 52 reinicios com o limite aparentemente configurado.
"""

from __future__ import annotations

import configparser
from pathlib import Path

import pytest

DEPLOYMENT = Path(__file__).resolve().parents[2] / "deployment"

#: Chaves que so tem efeito na secao ``[Unit]``.
UNIT_ONLY = ("StartLimitIntervalSec", "StartLimitBurst")


def unit_files() -> list[Path]:
    return sorted(DEPLOYMENT.glob("*.service"))


def parse(path: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(strict=False)
    # Chaves de unidade sao sensiveis a caixa; o padrao do configparser as
    # rebaixaria para minusculas e o teste deixaria de enxergar o problema.
    parser.optionxform = str  # type: ignore[method-assign]
    parser.read(path, encoding="utf-8")
    return parser


def test_there_are_unit_files_to_check() -> None:
    """Guarda contra o teste passar por nao ter encontrado nada."""
    assert unit_files()


@pytest.mark.parametrize("path", unit_files(), ids=lambda path: path.name)
def test_restart_limit_lives_in_the_unit_section(path: Path) -> None:
    parser = parse(path)

    for key in UNIT_ONLY:
        assert not parser.has_option("Service", key), (
            f"{path.name}: '{key}' em [Service] e ignorado pelo systemd; "
            "vale o padrao de 10 s e o limite nao segura nada"
        )


@pytest.mark.parametrize("path", unit_files(), ids=lambda path: path.name)
def test_a_service_that_restarts_declares_its_limit(path: Path) -> None:
    """Reinicio automatico sem limite e laco infinito em falha permanente."""
    parser = parse(path)
    if parser.get("Service", "Restart", fallback="no") == "no":
        return

    for key in UNIT_ONLY:
        assert parser.has_option("Unit", key), f"{path.name}: falta '{key}' em [Unit]"


@pytest.mark.parametrize("path", unit_files(), ids=lambda path: path.name)
def test_the_window_is_wider_than_the_restart_delay(path: Path) -> None:
    """Janela menor que o intervalo entre tentativas nunca acumula nada.

    Com o padrao de 10 s e ``RestartSec=5``, cabem duas tentativas por janela e
    o limite de tres nunca e atingido - o servico reinicia para sempre.
    """
    parser = parse(path)
    if parser.get("Service", "Restart", fallback="no") == "no":
        return

    window = int(parser.get("Unit", "StartLimitIntervalSec"))
    burst = int(parser.get("Unit", "StartLimitBurst"))
    delay = int(parser.get("Service", "RestartSec", fallback="0"))

    assert window > delay * burst, (
        f"{path.name}: {burst} tentativas a cada {delay}s nao cabem "
        f"em {window}s; o limite nunca dispara"
    )
