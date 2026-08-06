"""Cronometros de aceleracao e de volta.

Ambos trabalham sobre o carimbo de tempo das leituras, nunca sobre o relogio do
sistema. Isso mantem a medicao coerente com a fonte de dados - inclusive
quando o simulador roda em escala de tempo acelerada - e torna os testes
deterministicos.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from picockpit.core.events import EventBus
from picockpit.core.models import Reading, Signal
from picockpit.services.telemetry_service import topic_for

#: Publicado a cada atualizacao dos cronometros.
TOPIC_CHRONOMETER = "vehicle.chronometer"

#: Velocidade abaixo da qual o veiculo e considerado parado, em km/h.
#: Baixo de proposito: se a arrancada so comecasse a contar a 1 km/h, o
#: trecho mais lento da largada ficaria de fora e o 0-100 sairia melhor do
#: que o real. Ruido de leitura em torno de zero apenas rearma a medicao,
#: que e inofensivo.
STOPPED_KMH = 0.2


def _crossing_time(
    previous_time: float,
    previous_value: float,
    current_time: float,
    current_value: float,
    threshold: float,
) -> float:
    """Estima por interpolacao linear o instante em que um limiar foi cruzado.

    A 20 Hz, arredondar para a amostra mais proxima erraria ate 50 ms - erro
    grande demais para um 0-100 que se compara com numero de revista.

    Args:
        previous_time: Instante da amostra anterior.
        previous_value: Valor na amostra anterior.
        current_time: Instante da amostra atual.
        current_value: Valor na amostra atual.
        threshold: Limiar cruzado entre as duas amostras.

    Returns:
        Instante estimado do cruzamento.
    """
    span = current_value - previous_value
    if span <= 0.0:
        return current_time
    ratio = (threshold - previous_value) / span
    ratio = max(0.0, min(1.0, ratio))
    return previous_time + (current_time - previous_time) * ratio


@dataclass(slots=True)
class AccelerationTimer:
    """Mede o tempo de arrancada de parado ate uma velocidade alvo.

    A medicao so arma com o veiculo parado, e aborta se ele parar antes de
    alcancar o alvo. Sem isso, qualquer retomada em movimento contaria como
    arrancada e o melhor tempo viraria ficcao.

    Attributes:
        target_kmh: Velocidade alvo da medicao.
    """

    target_kmh: float = 100.0

    last_seconds: float | None = None
    best_seconds: float | None = None
    running: bool = False

    _armed: bool = False
    _start_time: float = 0.0
    _previous_time: float | None = None
    _previous_speed: float = 0.0

    @property
    def elapsed(self) -> float:
        """Tempo decorrido da medicao em andamento, em segundos."""
        if not self.running or self._previous_time is None:
            return 0.0
        return max(0.0, self._previous_time - self._start_time)

    def reset(self) -> None:
        """Descarta a medicao em andamento e o historico."""
        self.last_seconds = None
        self.best_seconds = None
        self.running = False
        self._armed = False
        self._previous_time = None
        self._previous_speed = 0.0

    def update(self, timestamp: float, speed_kmh: float) -> float | None:
        """Processa uma amostra de velocidade.

        Args:
            timestamp: Instante da amostra, em segundos.
            speed_kmh: Velocidade medida.

        Returns:
            O tempo da arrancada quando ela termina nesta amostra, senao
            ``None``.
        """
        previous_time = self._previous_time
        previous_speed = self._previous_speed
        self._previous_time = timestamp
        self._previous_speed = speed_kmh

        if speed_kmh <= STOPPED_KMH:
            # Parou: arma para a proxima arrancada e cancela a que estava em
            # andamento.
            self._armed = True
            self.running = False
            return None

        if previous_time is None:
            return None

        if not self.running:
            if self._armed and previous_speed <= STOPPED_KMH:
                # Limiar zero, e nao STOPPED_KMH: a arrancada e cronometrada a
                # partir do repouso, como manda a convencao de 0-100. Comecar a
                # contar so a 1 km/h descontaria a parte mais lenta da largada
                # e daria um tempo artificialmente bom.
                self._start_time = _crossing_time(
                    previous_time, previous_speed, timestamp, speed_kmh, 0.0
                )
                self.running = True
                self._armed = False
            return None

        if speed_kmh < self.target_kmh:
            return None

        finish = _crossing_time(
            previous_time, previous_speed, timestamp, speed_kmh, self.target_kmh
        )
        elapsed = max(0.0, finish - self._start_time)
        self.running = False
        self.last_seconds = elapsed
        if self.best_seconds is None or elapsed < self.best_seconds:
            self.best_seconds = elapsed
        return elapsed


@dataclass(slots=True)
class LapTimer:
    """Cronometro de voltas com marcacao manual.

    Marcacao manual e uma escolha consciente: sem GPS a bordo nao ha como
    detectar a linha de chegada. A interface ja fica pronta para o GPS assumir
    o disparo quando ele existir, sem mudar nada aqui.
    """

    running: bool = False
    laps: list[float] = field(default_factory=list)

    _start_time: float = 0.0
    _now: float = 0.0

    @property
    def current(self) -> float:
        """Tempo da volta em andamento, em segundos."""
        if not self.running:
            return 0.0
        return max(0.0, self._now - self._start_time)

    @property
    def last(self) -> float | None:
        """Tempo da ultima volta completada."""
        return self.laps[-1] if self.laps else None

    @property
    def best(self) -> float | None:
        """Melhor volta da sessao."""
        return min(self.laps) if self.laps else None

    @property
    def count(self) -> int:
        """Quantidade de voltas completadas."""
        return len(self.laps)

    def tick(self, timestamp: float) -> None:
        """Avanca o relogio interno com o carimbo de tempo das leituras."""
        self._now = timestamp

    def start(self, timestamp: float) -> None:
        """Inicia a primeira volta."""
        self._now = timestamp
        self._start_time = timestamp
        self.running = True

    def split(self, timestamp: float) -> float | None:
        """Fecha a volta atual e inicia a proxima.

        Args:
            timestamp: Instante do corte.

        Returns:
            O tempo da volta fechada, ou ``None`` se nao havia volta em curso.
        """
        if not self.running:
            self.start(timestamp)
            return None

        lap = max(0.0, timestamp - self._start_time)
        self.laps.append(lap)
        self._start_time = timestamp
        self._now = timestamp
        return lap

    def stop(self, timestamp: float) -> float | None:
        """Encerra a sessao, contabilizando a volta em curso.

        Args:
            timestamp: Instante do encerramento.

        Returns:
            O tempo da ultima volta, ou ``None`` se nao havia volta em curso.
        """
        if not self.running:
            return None
        lap = self.split(timestamp)
        self.running = False
        return lap

    def reset(self) -> None:
        """Zera voltas e para o cronometro."""
        self.running = False
        self.laps.clear()
        self._start_time = 0.0
        self._now = 0.0


@dataclass(frozen=True, slots=True)
class ChronometerSnapshot:
    """Estado dos cronometros num instante, pronto para a interface."""

    acceleration_running: bool = False
    acceleration_elapsed: float = 0.0
    acceleration_last: float | None = None
    acceleration_best: float | None = None
    lap_running: bool = False
    lap_current: float = 0.0
    lap_last: float | None = None
    lap_best: float | None = None
    lap_count: int = 0


class ChronometerService:
    """Liga os cronometros ao fluxo de telemetria.

    Observa apenas a velocidade: e o unico sinal de que os dois cronometros
    precisam. O carimbo de tempo vem das proprias leituras, entao a medicao
    acompanha a fonte mesmo quando o simulador roda acelerado.
    """

    def __init__(self, bus: EventBus, target_kmh: float = 100.0) -> None:
        """Inscreve o servico no barramento.

        Args:
            bus: Barramento de eventos.
            target_kmh: Velocidade alvo do cronometro de aceleracao.
        """
        self._bus = bus
        self.acceleration = AccelerationTimer(target_kmh=target_kmh)
        self.lap = LapTimer()
        self._now = 0.0
        self._unsubscribe = bus.subscribe(topic_for(Signal.SPEED), self._on_speed)

    @property
    def now(self) -> float:
        """Ultimo carimbo de tempo visto no fluxo de telemetria."""
        return self._now

    def snapshot(self) -> ChronometerSnapshot:
        """Fotografia do estado dos dois cronometros."""
        return ChronometerSnapshot(
            acceleration_running=self.acceleration.running,
            acceleration_elapsed=self.acceleration.elapsed,
            acceleration_last=self.acceleration.last_seconds,
            acceleration_best=self.acceleration.best_seconds,
            lap_running=self.lap.running,
            lap_current=self.lap.current,
            lap_last=self.lap.last,
            lap_best=self.lap.best,
            lap_count=self.lap.count,
        )

    async def _on_speed(self, reading: Reading) -> None:
        """Atualiza os cronometros e publica o novo estado."""
        self._now = reading.timestamp
        self.acceleration.update(reading.timestamp, reading.value)
        self.lap.tick(reading.timestamp)
        await self._bus.publish(TOPIC_CHRONOMETER, self.snapshot())

    async def start_lap(self) -> None:
        """Inicia a sessao de voltas."""
        self.lap.start(self._now)
        await self._bus.publish(TOPIC_CHRONOMETER, self.snapshot())

    async def split_lap(self) -> None:
        """Fecha a volta atual e comeca a proxima."""
        self.lap.split(self._now)
        await self._bus.publish(TOPIC_CHRONOMETER, self.snapshot())

    async def stop_lap(self) -> None:
        """Encerra a sessao de voltas."""
        self.lap.stop(self._now)
        await self._bus.publish(TOPIC_CHRONOMETER, self.snapshot())

    async def reset(self) -> None:
        """Zera os dois cronometros."""
        self.acceleration.reset()
        self.lap.reset()
        await self._bus.publish(TOPIC_CHRONOMETER, self.snapshot())

    def close(self) -> None:
        """Cancela a inscricao no barramento."""
        self._unsubscribe()
