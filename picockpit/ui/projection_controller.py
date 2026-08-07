"""Ponte da projecao com a camada QML."""

from __future__ import annotations

import logging

from PySide6.QtCore import Property, QObject, QTimer, Slot
from PySide6.QtCore import Signal as QtSignal

from picockpit.services.projection import ProjectionService, ProjectionState

logger = logging.getLogger(__name__)

#: Intervalo de consulta ao systemd, em milissegundos.
#:
#: Dois segundos, e nao 200 ms: cada consulta e um processo novo, e o estado da
#: projecao muda na escala do humano plugando um cabo. Consultar rapido gastaria
#: CPU que o painel usa para manter 60 quadros.
POLL_MS = 2000


class ProjectionController(QObject):
    """Expoe estado e comando da projecao ao QML."""

    changed = QtSignal()

    def __init__(self, service: ProjectionService | None = None, parent: QObject | None = None):
        """Inicializa o controlador e comeca a acompanhar o estado.

        Args:
            service: Servico de projecao; util injetar nos testes.
            parent: Pai Qt opcional.
        """
        super().__init__(parent)
        self._service = service or ProjectionService()
        self._state = self._service.state()

        self._timer = QTimer(self)
        self._timer.setInterval(POLL_MS)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()

    @Slot()
    def refresh(self) -> None:
        """Reconsulta o estado e avisa a interface se algo mudou."""
        state = self._service.state()
        if state is self._state:
            return
        self._state = state
        self.changed.emit()

    @Property(str, notify=changed)  # type: ignore[operator]
    def state(self) -> str:
        """Estado corrente, como em ``ProjectionState``."""
        return self._state.value

    @Property(bool, notify=changed)  # type: ignore[operator]
    def installed(self) -> bool:
        """Indica se ha projecao instalada nesta maquina."""
        return self._state is not ProjectionState.ABSENT

    @Property(bool, notify=changed)  # type: ignore[operator]
    def running(self) -> bool:
        """Indica se a projecao esta ocupando a tela."""
        return self._state is ProjectionState.RUNNING

    @Property(bool, notify=changed)  # type: ignore[operator]
    def busy(self) -> bool:
        """Indica transicao em andamento, para a interface nao piscar botao."""
        return self._state in (ProjectionState.STARTING, ProjectionState.RETRYING)

    @Property(bool, notify=changed)  # type: ignore[operator]
    def stoppable(self) -> bool:
        """Indica se ha o que interromper.

        Inclui a retentativa: sem isso, a unica saida de um laco de reinicio -
        cabo solto, adaptador ausente - seria o terminal, que ninguem tem no
        carro.
        """
        return self._state in (
            ProjectionState.RUNNING,
            ProjectionState.STARTING,
            ProjectionState.RETRYING,
            ProjectionState.FAILED,
        )

    @Property(str, notify=changed)  # type: ignore[operator]
    def summary(self) -> str:
        """Frase curta descrevendo o estado, ja em portugues."""
        return {
            ProjectionState.ABSENT: "Projecao nao instalada neste sistema",
            ProjectionState.STOPPED: "Pronta - conecte o telefone ou o adaptador",
            ProjectionState.STARTING: "Iniciando...",
            ProjectionState.RETRYING: "Falhou e esta tentando de novo - confira cabo e adaptador",
            ProjectionState.RUNNING: "Projetando na regiao reservada",
            ProjectionState.FAILED: "Falhou ao iniciar - confira cabo, adaptador e log",
        }[self._state]

    @Slot()
    def start(self) -> None:
        """Sobe a projecao e reconsulta o estado logo em seguida."""
        self._service.start()
        self.refresh()

    @Slot()
    def stop(self) -> None:
        """Derruba a projecao e reconsulta o estado logo em seguida."""
        self._service.stop()
        self.refresh()

    def close(self) -> None:
        """Interrompe a consulta periodica."""
        self._timer.stop()
