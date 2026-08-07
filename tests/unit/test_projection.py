"""Testes do comando da projecao."""

from __future__ import annotations

import pytest

from picockpit.services.projection import ProjectionService, ProjectionState


class FakeSystemd:
    """systemd de mentira, com estado controlavel."""

    def __init__(self, load: str = "loaded", active: str = "inactive", code: int = 0) -> None:
        self.load = load
        self.active = active
        self.code = code
        self.commands: list[list[str]] = []

    def __call__(self, command: list[str]) -> tuple[int, str]:
        self.commands.append(list(command))
        if "show" in command:
            return 0, f"LoadState={self.load}\nActiveState={self.active}"
        return self.code, ""


def build(**kwargs) -> tuple[ProjectionService, FakeSystemd]:
    systemd = FakeSystemd(**kwargs)
    service = ProjectionService(runner=systemd)
    service.available = lambda: True  # type: ignore[method-assign]
    return service, systemd


# ------------------------------------------------------------------- estado


@pytest.mark.parametrize(
    ("active", "expected"),
    [
        ("active", ProjectionState.RUNNING),
        ("activating", ProjectionState.STARTING),
        ("inactive", ProjectionState.STOPPED),
        ("deactivating", ProjectionState.STOPPED),
        ("failed", ProjectionState.FAILED),
    ],
)
def test_systemd_states_are_translated(active: str, expected: ProjectionState) -> None:
    service, _ = build(active=active)

    assert service.state() is expected


def test_unknown_state_is_treated_as_stopped() -> None:
    """Estado que nao conhecemos nao pode virar 'rodando' por otimismo."""
    service, _ = build(active="alguma-coisa-nova")

    assert service.state() is ProjectionState.STOPPED


def test_unit_not_installed_is_absent_not_error() -> None:
    """Nao ter LIVI instalado e configuracao valida do produto, nao falha."""
    service, _ = build(load="not-found")

    assert service.state() is ProjectionState.ABSENT


def test_without_systemctl_everything_is_absent() -> None:
    """Na bancada e no container nao ha systemd; a interface precisa saber."""
    service = ProjectionService(runner=lambda command: (0, ""))
    service.available = lambda: False  # type: ignore[method-assign]

    assert service.state() is ProjectionState.ABSENT


# ------------------------------------------------------------------ comando


def test_start_sends_the_command() -> None:
    service, systemd = build(active="inactive")

    assert service.start()
    assert ["systemctl", "--user", "start", "livi.service"] in systemd.commands


def test_stop_sends_the_command() -> None:
    service, systemd = build(active="active")

    assert service.stop()
    assert ["systemctl", "--user", "stop", "livi.service"] in systemd.commands


def test_commands_are_refused_when_nothing_is_installed() -> None:
    """Sem unidade, o comando nem sai - erro do systemd nao explica nada."""
    service, systemd = build(load="not-found")

    assert not service.start()
    assert not any("start" in command for command in systemd.commands)


def test_failure_is_reported_not_raised() -> None:
    """Falhar ao subir a projecao nao pode derrubar o painel junto."""
    service, _ = build(active="inactive", code=1)

    assert not service.start()


def test_a_broken_runner_does_not_escape() -> None:
    """Se o systemd sumir no meio, o painel segue - sem projecao, mas segue.

    Quem chama isto e a thread da interface. Uma excecao vazando daqui levaria
    junto o painel do motorista, que e a parte do sistema que nao pode parar.
    """

    def explode(command: list[str]) -> tuple[int, str]:
        raise OSError("systemd sumiu")

    service = ProjectionService(runner=explode)
    service.available = lambda: True  # type: ignore[method-assign]

    assert service.state() is ProjectionState.ABSENT
    assert not service.start()
