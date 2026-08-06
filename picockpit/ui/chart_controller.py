"""Controlador dos graficos em tempo real.

Mantem uma serie por sinal e entrega ao QML pontos ja no sistema de coordenadas
do desenho. A reducao de pontos acontece aqui, do lado Python, porque atravessar
a fronteira com o QML custa mais caro do que a conta em si.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Property, QObject, QPointF, Slot
from PySide6.QtCore import Signal as QtSignal

from picockpit.core.events import EventBus
from picockpit.core.models import SIGNAL_RANGES, Signal, VehicleState
from picockpit.core.series import TimeSeries
from picockpit.services.telemetry_service import TOPIC_STATE

logger = logging.getLogger(__name__)

#: Sinais acompanhados pelos graficos, na ordem de exibicao.
CHARTED_SIGNALS: tuple[Signal, ...] = (
    Signal.SPEED,
    Signal.RPM,
    Signal.CONSUMPTION,
    Signal.ENGINE_LOAD,
)

#: Escalas verticais fixas. Sinal ausente daqui usa escala automatica.
FIXED_SCALES: dict[Signal, tuple[float, float]] = {
    Signal.SPEED: (0.0, 140.0),
    Signal.RPM: (0.0, 7000.0),
    Signal.ENGINE_LOAD: (0.0, 100.0),
}

#: Intervalo minimo entre redesenhos, em segundos de telemetria.
#:
#: A telemetria chega a 20 Hz, mas redesenhar um grafico 20 vezes por segundo
#: nao acrescenta informacao visivel e gasta GPU que o painel precisa. 10 Hz ja
#: parece continuo.
REDRAW_INTERVAL_S = 0.1


class ChartController(QObject):
    """Expoe series temporais ao QML como polilinhas prontas para desenho."""

    updated = QtSignal()

    def __init__(
        self, bus: EventBus, window_s: float = 60.0, parent: QObject | None = None
    ) -> None:
        """Inscreve o controlador no barramento.

        Args:
            bus: Barramento de eventos.
            window_s: Janela visivel dos graficos, em segundos.
            parent: Pai Qt opcional.
        """
        super().__init__(parent)
        self._series: dict[str, TimeSeries] = {}
        for signal in CHARTED_SIGNALS:
            low, high = FIXED_SCALES.get(signal, (SIGNAL_RANGES[signal][0], None))
            self._series[signal.value] = TimeSeries(window_s=window_s, minimum=low, maximum=high)
        self._last_redraw = 0.0
        self._revision = 0
        self._unsubscribe = bus.subscribe(TOPIC_STATE, self._on_state)

    def _on_state(self, state: VehicleState) -> None:
        """Acrescenta uma amostra a cada serie acompanhada."""
        for signal in CHARTED_SIGNALS:
            if signal in state.values:
                self._series[signal.value].append(state.timestamp, state.values[signal])

        if state.timestamp - self._last_redraw < REDRAW_INTERVAL_S:
            return
        self._last_redraw = state.timestamp
        self._revision += 1
        self.updated.emit()

    @Property(int, notify=updated)  # type: ignore[operator]
    def revision(self) -> int:
        """Contador de atualizacoes.

        Existe porque binding QML so reavalia quando depende de uma
        *propriedade*. Referenciar o sinal ``updated`` dentro da expressao nao
        cria dependencia nenhuma - o grafico ficaria congelado no primeiro
        desenho. Lendo ``revision``, o binding passa a acompanhar de verdade.
        """
        return self._revision

    @Property("QStringList", constant=True)  # type: ignore[operator]
    def chartedSignals(self) -> list[str]:  # noqa: N802 - nome consumido pelo QML
        """Nomes dos sinais com grafico disponivel."""
        return [signal.value for signal in CHARTED_SIGNALS]

    @Slot(str, float, float, result="QVariantList")
    def polyline(self, signal: str, width: float, height: float) -> list[QPointF]:
        """Pontos da serie no sistema de coordenadas do item que vai desenhar.

        Args:
            signal: Nome do sinal, como em ``Signal.value``.
            width: Largura disponivel em pixels.
            height: Altura disponivel em pixels.

        Returns:
            Pontos prontos para um ``PathPolyline``. Lista vazia quando ainda
            nao ha historico suficiente.
        """
        series = self._series.get(signal)
        if series is None or width <= 0 or height <= 0:
            return []

        resolution = max(2, min(200, int(width)))
        return [QPointF(x * width, height - y * height) for x, y in series.normalized(resolution)]

    @Slot(str, result=float)
    def latest(self, signal: str) -> float:
        """Ultimo valor recebido do sinal informado."""
        series = self._series.get(signal)
        return series.latest if series else 0.0

    @Slot(str, result=float)
    def peak(self, signal: str) -> float:
        """Limite superior corrente da escala vertical do sinal."""
        series = self._series.get(signal)
        return series.bounds()[1] if series else 0.0

    @Slot()
    def clear(self) -> None:
        """Descarta o historico de todas as series."""
        for series in self._series.values():
            series.clear()
        self._revision += 1
        self.updated.emit()

    def close(self) -> None:
        """Cancela a inscricao no barramento."""
        self._unsubscribe()
