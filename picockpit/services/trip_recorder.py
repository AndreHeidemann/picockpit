"""Gravacao de viagens.

Detecta inicio e fim de viagem pelo proprio fluxo de telemetria e grava um
unico registro no encerramento. Gravar amostra a amostra encheria o cartao SD
de escrita continua sem produzir nada que o motorista va consultar - o que
interessa e o resumo do trecho.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from picockpit.core.events import EventBus
from picockpit.core.models import Signal, VehicleState
from picockpit.core.trip import Trip
from picockpit.data.trip_repository import TripRepository
from picockpit.services.telemetry_service import TOPIC_FAULTS, TOPIC_STATE

logger = logging.getLogger(__name__)

#: Publicado quando uma viagem e gravada.
TOPIC_TRIP_SAVED = "vehicle.trip.saved"

#: Velocidade que caracteriza inicio de viagem, em km/h.
START_SPEED_KMH = 3.0

#: Velocidade abaixo da qual o veiculo conta como parado, em km/h.
STOPPED_KMH = 1.0

#: Tempo parado que encerra a viagem, em segundos.
IDLE_TIMEOUT_S = 120.0

#: Avanco maximo aceito do hodometro entre duas atualizacoes, em km.
#: Acima disso e salto da fonte - troca de provider, reinicio, leitura
#: corrompida - e nao distancia percorrida.
MAX_ODOMETER_STEP_KM = 1.0


class TripRecorder:
    """Acompanha a telemetria e grava o resumo de cada viagem."""

    def __init__(
        self,
        bus: EventBus,
        repository: TripRepository,
        idle_timeout_s: float = IDLE_TIMEOUT_S,
        clock: Callable[[], float] = time.time,
    ) -> None:
        """Inicializa o gravador.

        Args:
            bus: Barramento de eventos.
            repository: Onde as viagens sao gravadas.
            idle_timeout_s: Tempo parado que encerra a viagem.
            clock: Relogio de parede, injetavel para testes. Os carimbos da
                telemetria sao relativos ao inicio da sessao e nao servem para
                datar um registro historico.
        """
        self._bus = bus
        self._repository = repository
        self._idle_timeout_s = idle_timeout_s
        self._clock = clock

        self.recording = False
        self._started_at = 0.0
        self._distance_km = 0.0
        self._fuel_used_l = 0.0
        self._moving_s = 0.0
        self._elapsed_s = 0.0
        self._idle_s = 0.0
        self._max_speed = 0.0
        self._fuel = "gasoline"
        self._faults: set[str] = set()
        self._previous_time: float | None = None
        self._previous_odometer: float | None = None

        self._unsubscribe_state = bus.subscribe(TOPIC_STATE, self._on_state)
        self._unsubscribe_faults = bus.subscribe(TOPIC_FAULTS, self._on_faults)

    # ------------------------------------------------------------- consumo

    def _on_faults(self, codes: tuple[str, ...]) -> None:
        """Registra os codigos vistos durante a viagem."""
        if self.recording:
            self._faults.update(codes)

    async def _on_state(self, state: VehicleState) -> None:
        """Acumula a viagem em andamento e decide inicio e fim."""
        previous_time = self._previous_time
        self._previous_time = state.timestamp
        speed = state.get(Signal.SPEED)

        if previous_time is None:
            self._previous_odometer = state.get(Signal.ODOMETER)
            return

        dt = max(0.0, state.timestamp - previous_time)

        if not self.recording:
            if speed >= START_SPEED_KMH:
                self._start(state)
            else:
                self._previous_odometer = state.get(Signal.ODOMETER)
            return

        self._accumulate(state, dt, speed)

        if speed <= STOPPED_KMH:
            self._idle_s += dt
            if self._idle_s >= self._idle_timeout_s:
                await self.finish()
        else:
            self._idle_s = 0.0

    def _start(self, state: VehicleState) -> None:
        """Abre uma viagem."""
        self.recording = True
        self._started_at = self._clock()
        self._distance_km = 0.0
        self._fuel_used_l = 0.0
        self._moving_s = 0.0
        self._elapsed_s = 0.0
        self._idle_s = 0.0
        self._max_speed = 0.0
        self._faults.clear()
        self._previous_odometer = state.get(Signal.ODOMETER)
        logger.info("Viagem iniciada")

    def _accumulate(self, state: VehicleState, dt: float, speed: float) -> None:
        """Soma distancia, consumo e tempo do intervalo."""
        self._elapsed_s += dt

        # O hodometro e a fonte preferida por ja vir integrado. O servico de
        # telemetria publica um estado por leitura, entao varios estados
        # chegam com o mesmo carimbo de tempo e apenas um deles traz o
        # hodometro novo - por isso a validacao nao pode depender do intervalo
        # de tempo, que nesses casos e zero. O criterio e absoluto: avanco
        # maior que MAX_ODOMETER_STEP_KM entre atualizacoes so pode ser salto
        # de fonte, nao quilometro rodado.
        if Signal.ODOMETER in state.values:
            odometer = state.values[Signal.ODOMETER]
            if self._previous_odometer is not None:
                delta = odometer - self._previous_odometer
                if 0.0 <= delta <= MAX_ODOMETER_STEP_KM:
                    self._distance_km += delta
                else:
                    logger.warning("Salto de %.1f km no hodometro ignorado", delta)
            self._previous_odometer = odometer
        else:
            # Fonte sem hodometro: integra a velocidade.
            self._distance_km += speed * dt / 3600.0

        # Integrar o consumo horario dispensa saber o tamanho do tanque e
        # funciona igual para simulacao e para OBD-II.
        self._fuel_used_l += state.get(Signal.FUEL_RATE) * dt / 3600.0

        if speed > STOPPED_KMH:
            self._moving_s += dt
        self._max_speed = max(self._max_speed, speed)

    # -------------------------------------------------------------- fecho

    def snapshot(self) -> Trip:
        """Monta a viagem em andamento sem grava-la."""
        return Trip(
            started_at=self._started_at,
            ended_at=self._clock(),
            duration_s=self._elapsed_s,
            moving_s=self._moving_s,
            distance_km=self._distance_km,
            fuel_used_l=self._fuel_used_l,
            max_speed_kmh=self._max_speed,
            fuel=self._fuel,
            fault_codes=tuple(sorted(self._faults)),
        )

    async def finish(self) -> Trip | None:
        """Encerra e grava a viagem em andamento.

        Viagens sem distancia sao descartadas: ligar o carro, deixar em marcha
        lenta e desligar nao e uma viagem, e poluiria o historico.

        Returns:
            A viagem gravada, ou ``None`` se nao havia nada a gravar.
        """
        if not self.recording:
            return None

        trip = self.snapshot()
        self.recording = False
        self._idle_s = 0.0

        if trip.distance_km <= 0.0:
            logger.info("Viagem descartada: sem distancia percorrida")
            return None

        saved = self._repository.save(trip)
        logger.info(
            "Viagem gravada: %.2f km, %.2f L, %.1f km/L",
            saved.distance_km,
            saved.fuel_used_l,
            saved.average_consumption_km_l,
        )
        await self._bus.publish(TOPIC_TRIP_SAVED, saved)
        return saved

    def set_fuel(self, fuel: str) -> None:
        """Informa o combustivel em uso na viagem corrente."""
        self._fuel = fuel

    def close(self) -> None:
        """Cancela as inscricoes no barramento."""
        self._unsubscribe_state()
        self._unsubscribe_faults()
