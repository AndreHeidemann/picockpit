"""Controlador dos cronometros para a camada QML."""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Slot
from PySide6.QtCore import Signal as QtSignal

from picockpit.core.events import EventBus
from picockpit.services.chronometer import (
    TOPIC_CHRONOMETER,
    ChronometerService,
    ChronometerSnapshot,
)


def _format(seconds: float | None) -> str:
    """Formata um tempo em ``m:ss,cc``, ou traco quando nao ha medicao.

    Args:
        seconds: Tempo em segundos.

    Returns:
        Texto pronto para exibicao.
    """
    if seconds is None:
        return "--"
    minutes, rest = divmod(seconds, 60.0)
    if minutes >= 1:
        return f"{int(minutes)}:{rest:05.2f}"
    return f"{rest:.2f}"


class ChronoController(QObject):
    """Expoe os cronometros ao QML e encaminha os comandos de volta."""

    updated = QtSignal()

    def __init__(
        self,
        bus: EventBus,
        service: ChronometerService | None = None,
        parent: QObject | None = None,
    ) -> None:
        """Inscreve o controlador no barramento.

        Args:
            bus: Barramento de eventos.
            service: Servico de cronometragem. Os comandos de volta ficam
                indisponiveis quando omitido, o que e o caso em testes que so
                observam.
            parent: Pai Qt opcional.
        """
        super().__init__(parent)
        self._snapshot = ChronometerSnapshot()
        self._service = service
        self._unsubscribe = bus.subscribe(TOPIC_CHRONOMETER, self._on_snapshot)

    def _on_snapshot(self, snapshot: ChronometerSnapshot) -> None:
        """Recebe o estado dos cronometros."""
        self._snapshot = snapshot
        self.updated.emit()

    @Property(bool, notify=updated)  # type: ignore[operator]
    def accelRunning(self) -> bool:  # noqa: N802 - nome consumido pelo QML
        """Indica medicao de arrancada em andamento."""
        return self._snapshot.acceleration_running

    @Property(str, notify=updated)  # type: ignore[operator]
    def accelElapsed(self) -> str:  # noqa: N802 - nome consumido pelo QML
        """Tempo corrente da arrancada."""
        return _format(self._snapshot.acceleration_elapsed)

    @Property(str, notify=updated)  # type: ignore[operator]
    def accelLast(self) -> str:  # noqa: N802 - nome consumido pelo QML
        """Tempo da ultima arrancada concluida."""
        return _format(self._snapshot.acceleration_last)

    @Property(str, notify=updated)  # type: ignore[operator]
    def accelBest(self) -> str:  # noqa: N802 - nome consumido pelo QML
        """Melhor arrancada da sessao."""
        return _format(self._snapshot.acceleration_best)

    @Property(bool, notify=updated)  # type: ignore[operator]
    def lapRunning(self) -> bool:  # noqa: N802 - nome consumido pelo QML
        """Indica sessao de voltas em andamento."""
        return self._snapshot.lap_running

    @Property(str, notify=updated)  # type: ignore[operator]
    def lapCurrent(self) -> str:  # noqa: N802 - nome consumido pelo QML
        """Tempo da volta em andamento."""
        return _format(self._snapshot.lap_current)

    @Property(str, notify=updated)  # type: ignore[operator]
    def lapLast(self) -> str:  # noqa: N802 - nome consumido pelo QML
        """Tempo da ultima volta fechada."""
        return _format(self._snapshot.lap_last)

    @Property(str, notify=updated)  # type: ignore[operator]
    def lapBest(self) -> str:  # noqa: N802 - nome consumido pelo QML
        """Melhor volta da sessao."""
        return _format(self._snapshot.lap_best)

    @Property(int, notify=updated)  # type: ignore[operator]
    def lapCount(self) -> int:  # noqa: N802 - nome consumido pelo QML
        """Quantidade de voltas fechadas."""
        return self._snapshot.lap_count

    @Slot()
    def toggleLap(self) -> None:  # noqa: N802 - nome consumido pelo QML
        """Inicia a sessao de voltas, ou fecha uma volta se ja estiver em curso."""
        if self._service is None:
            return
        coroutine = (
            self._service.split_lap() if self._snapshot.lap_running else self._service.start_lap()
        )
        self._schedule(coroutine)

    @Slot()
    def stopLap(self) -> None:  # noqa: N802 - nome consumido pelo QML
        """Encerra a sessao de voltas."""
        if self._service is not None:
            self._schedule(self._service.stop_lap())

    @Slot()
    def resetAll(self) -> None:  # noqa: N802 - nome consumido pelo QML
        """Zera arrancadas e voltas."""
        if self._service is not None:
            self._schedule(self._service.reset())

    def _schedule(self, coroutine) -> None:
        """Agenda uma corrotina no laco em execucao.

        O QML chama estes slots de dentro do laco de eventos do Qt, que com o
        qasync e o mesmo do asyncio - por isso ``create_task`` e seguro aqui.
        """
        import asyncio

        try:
            asyncio.get_running_loop().create_task(coroutine)
        except RuntimeError:
            coroutine.close()

    def close(self) -> None:
        """Cancela a inscricao no barramento."""
        self._unsubscribe()
