"""Comando e estado da projecao de CarPlay e Android Auto.

A projecao roda em outro processo - o LIVI - e nao dentro da nossa cena. Duas
razoes independentes levam a isso:

*Tecnica*: nenhuma solucao de projecao entrega o video como item Qt que a gente
possa ancorar. O LIVI decodifica no hardware do SoC e mantem o quadro na GPU
por um pipeline GStreamer sem copia; passar isso para dentro do nosso QML
significaria justamente a copia que ele evita.

*Licenca*: o LIVI e GPL-3.0-or-later e o PiCockpit e proprietario. Processos
separados que se falam por systemd e socket ficam em lados corretos dessa
fronteira. Linkar ou embutir codigo dele, nao.

Por isso este modulo nao importa nada do LIVI: ele so liga, desliga e pergunta
o estado de uma unidade de usuario do systemd.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from collections.abc import Sequence
from enum import Enum

logger = logging.getLogger(__name__)

#: Unidade de usuario que roda o LIVI. Nossa, e nao a entrada de autostart que
#: o instalador dele cria: com autostart a projecao subiria por fora do nosso
#: controle e apareceria por cima do painel no boot.
UNIT = "livi.service"

#: Tempo maximo de espera por um comando do systemd, em segundos. Curto de
#: proposito: isto e chamado da thread da interface, e travar aqui seria
#: travar o painel.
TIMEOUT_S = 5.0


class ProjectionState(str, Enum):
    """Estado da projecao do ponto de vista de quem opera o carro."""

    #: A unidade nao existe: o LIVI nao foi instalado nesta maquina.
    ABSENT = "absent"
    #: Instalado e parado.
    STOPPED = "stopped"
    #: Subindo pela primeira vez.
    STARTING = "starting"
    #: Rodando.
    RUNNING = "running"
    #: Caiu e o systemd esta tentando de novo.
    RETRYING = "retrying"
    #: Terminou em erro - cabo, dongle ou o proprio LIVI.
    FAILED = "failed"


def _run(command: Sequence[str]) -> tuple[int, str]:
    """Executa um comando e devolve codigo e saida combinada.

    Sem shell de proposito: os argumentos sao fixos no modulo, nada aqui vem da
    interface, e um `shell=True` transformaria qualquer descuido futuro em
    injecao de comando dentro do carro.
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        logger.warning("Comando de projecao falhou: %s", error)
        return 1, str(error)
    return result.returncode, (result.stdout + result.stderr).strip()


class ProjectionService:
    """Liga, desliga e observa a unidade da projecao.

    O executor e injetavel para que o comportamento seja verificavel sem um
    systemd por perto - inclusive os casos que so aparecem no carro, como a
    unidade ausente ou o comando estourando o tempo.
    """

    def __init__(self, unit: str = UNIT, runner=_run) -> None:
        """Inicializa o servico.

        Args:
            unit: Nome da unidade de usuario do systemd.
            runner: Funcao que executa um comando e devolve ``(codigo, saida)``.
        """
        self._unit = unit
        self._runner = runner

    def _run(self, command: Sequence[str]) -> tuple[int, str]:
        """Executa um comando sem deixar excecao escapar.

        A blindagem fica aqui, e nao so no executor padrao, porque quem chama e
        a thread da interface: uma falha ao consultar a projecao nao pode
        derrubar o painel do motorista junto.
        """
        try:
            return self._runner(command)
        except Exception as error:
            logger.warning("Consulta a projecao falhou: %s", error)
            return 1, ""

    @property
    def unit(self) -> str:
        """Nome da unidade controlada."""
        return self._unit

    def available(self) -> bool:
        """Indica se ha systemd de usuario para conversar.

        Fora do Pi - no container ou na bancada - nao ha, e a interface precisa
        dizer isso em vez de oferecer um botao que nunca funciona.
        """
        return shutil.which("systemctl") is not None

    def state(self) -> ProjectionState:
        """Le o estado corrente da unidade.

        Returns:
            Estado da projecao. Unidade desconhecida vira ``ABSENT``, e nao
            erro: nao ter LIVI instalado e uma configuracao valida do produto.
        """
        if not self.available():
            return ProjectionState.ABSENT

        code, output = self._run(
            [
                "systemctl",
                "--user",
                "show",
                self._unit,
                "--property=LoadState,ActiveState,Result,NRestarts",
            ]
        )
        if code != 0 and not output:
            return ProjectionState.ABSENT

        fields = dict(line.split("=", 1) for line in output.splitlines() if "=" in line)
        if fields.get("LoadState") != "loaded":
            return ProjectionState.ABSENT

        active = fields.get("ActiveState", "")
        if active == "activating":
            # `activating` sozinho nao distingue a primeira subida de uma
            # retentativa. Com o AppImage ausente, o systemd fica horas neste
            # estado por causa do Restart=on-failure, e a interface anunciava
            # "Iniciando..." o tempo todo, com o botao travado. Quem esta no
            # carro precisa saber que ja falhou uma vez.
            failed_before = fields.get("Result", "success") != "success"
            restarted = fields.get("NRestarts", "0") not in {"0", ""}
            if failed_before or restarted:
                return ProjectionState.RETRYING
            return ProjectionState.STARTING

        return {
            "active": ProjectionState.RUNNING,
            "reloading": ProjectionState.RUNNING,
            "deactivating": ProjectionState.STOPPED,
            "failed": ProjectionState.FAILED,
        }.get(active, ProjectionState.STOPPED)

    def start(self) -> bool:
        """Sobe a projecao.

        Returns:
            ``True`` se o comando foi aceito.
        """
        return self._command("start")

    def stop(self) -> bool:
        """Derruba a projecao.

        Returns:
            ``True`` se o comando foi aceito.
        """
        return self._command("stop")

    def _command(self, verb: str) -> bool:
        """Envia um verbo do systemd para a unidade."""
        if self.state() is ProjectionState.ABSENT:
            logger.info("Projecao indisponivel: unidade %s nao instalada", self._unit)
            return False
        code, output = self._run(["systemctl", "--user", verb, self._unit])
        if code != 0:
            logger.warning("systemctl --user %s %s falhou: %s", verb, self._unit, output)
        return code == 0
