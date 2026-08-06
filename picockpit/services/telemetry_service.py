"""Servico que liga um provider de telemetria ao barramento de eventos.

E o unico ponto do sistema que conhece as duas pontas. Providers nao sabem que
existe um barramento; assinantes nao sabem de onde o dado veio.
"""

from __future__ import annotations

import asyncio
import logging

from picockpit.core.events import EventBus
from picockpit.core.models import Reading, Signal, VehicleState
from picockpit.services.providers import TelemetryProvider

logger = logging.getLogger(__name__)

#: Topico publicado a cada estado consolidado.
TOPIC_STATE = "vehicle.state"

#: Prefixo dos topicos por sinal, ex.: ``vehicle.signal.rpm``.
TOPIC_SIGNAL_PREFIX = "vehicle.signal."


def topic_for(signal: Signal) -> str:
    """Nome do topico de um sinal especifico.

    Args:
        signal: Sinal desejado.

    Returns:
        Nome do topico correspondente.
    """
    return f"{TOPIC_SIGNAL_PREFIX}{signal.value}"


class TelemetryService:
    """Consome o stream de um provider, mantem o estado e publica eventos."""

    def __init__(self, provider: TelemetryProvider, bus: EventBus) -> None:
        """Inicializa o servico.

        Args:
            provider: Fonte de leituras.
            bus: Barramento onde os eventos serao publicados.
        """
        self._provider = provider
        self._bus = bus
        self._state = VehicleState()
        self._task: asyncio.Task[None] | None = None
        self._dropped = 0

    @property
    def state(self) -> VehicleState:
        """Ultimo estado consolidado do veiculo."""
        return self._state

    @property
    def dropped_readings(self) -> int:
        """Quantidade de leituras descartadas por implausibilidade."""
        return self._dropped

    @property
    def is_running(self) -> bool:
        """Indica se o laco de consumo esta ativo."""
        return self._task is not None and not self._task.done()

    async def handle(self, reading: Reading) -> None:
        """Processa uma leitura: valida, atualiza o estado e publica.

        Leituras fora da faixa fisica do sinal sao descartadas em vez de
        propagadas. Num painel, exibir um valor absurdo e pior do que repetir
        o anterior.

        Args:
            reading: Leitura recebida do provider.
        """
        if not reading.is_plausible():
            self._dropped += 1
            logger.warning(
                "Leitura implausivel descartada: %s=%.2f", reading.signal.value, reading.value
            )
            return

        self._state = self._state.with_reading(reading)
        await self._bus.publish(topic_for(reading.signal), reading)
        await self._bus.publish(TOPIC_STATE, self._state)

    async def run(self) -> None:
        """Consome o provider ate ser cancelado."""
        async with self._provider:
            async for reading in self._provider.stream():
                await self.handle(reading)

    async def start(self) -> None:
        """Inicia o laco de consumo em segundo plano."""
        if self.is_running:
            return
        self._task = asyncio.create_task(self.run())

    async def stop(self) -> None:
        """Cancela o laco de consumo e aguarda seu encerramento."""
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None
