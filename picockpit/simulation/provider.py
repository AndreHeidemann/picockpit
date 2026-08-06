"""Provider de telemetria sintetica.

Implementa o mesmo contrato que o provider OBD-II e o CAN vao implementar, de
modo que a troca de origem dos dados nao alcance servicos nem interface.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, replace

from picockpit.core.models import ProviderKind, Reading, Signal
from picockpit.services.providers import ProviderError, TelemetryProvider
from picockpit.simulation.driver import DriverProfile
from picockpit.simulation.faults import FaultInjector
from picockpit.simulation.model import VehicleModel
from picockpit.simulation.spec import FuelKind, VehicleSpec

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SimulationProvider(TelemetryProvider):
    """Gera telemetria plausivel sem qualquer hardware conectado.

    Attributes:
        sample_interval_s: Intervalo entre amostras publicadas.
        time_scale: Multiplicador do tempo simulado. Acima de 1 acelera o
            ciclo de conducao, util para exercitar o painel em testes sem
            esperar em tempo real.
    """

    kind = ProviderKind.SIMULATION

    sample_interval_s: float = 0.05
    time_scale: float = 1.0
    spec: VehicleSpec | None = None
    driver: DriverProfile | None = None
    faults: FaultInjector | None = None

    _model: VehicleModel | None = None
    _connected: bool = False
    _clock_s: float = 0.0

    def __post_init__(self) -> None:
        """Valida os parametros e garante uma especificacao de veiculo.

        A especificacao existe desde a construcao, e nao a partir do
        ``connect``: perguntar qual e o combustivel e uma consulta de
        configuracao, nao de estado de conexao. Amarrar as duas coisas fazia a
        tela de ajustes quebrar na inicializacao, antes de o provider conectar.
        """
        if self.sample_interval_s <= 0.0:
            raise ValueError("sample_interval_s deve ser positivo")
        if self.time_scale <= 0.0:
            raise ValueError("time_scale deve ser positivo")
        self.spec = self.spec or VehicleSpec()

    @property
    def is_connected(self) -> bool:
        """Indica se o simulador esta pronto para produzir leituras."""
        return self._connected

    @property
    def model(self) -> VehicleModel:
        """Modelo dinamico em uso.

        Raises:
            ProviderError: Se acessado antes de ``connect``.
        """
        if self._model is None:
            raise ProviderError("Simulador nao conectado")
        return self._model

    async def connect(self) -> None:
        """Instancia o modelo e o motorista sintetico."""
        self._model = VehicleModel(spec=self.spec)
        self.driver = self.driver or DriverProfile()
        self.faults = self.faults or FaultInjector()
        self._clock_s = 0.0
        self._connected = True
        logger.info("SimulationProvider conectado (intervalo=%.3fs)", self.sample_interval_s)

    async def disconnect(self) -> None:
        """Libera o modelo e marca o provider como desconectado."""
        self._connected = False
        self._model = None
        logger.info("SimulationProvider desconectado")

    def fault_codes(self) -> tuple[str, ...]:
        """Codigos de falha injetados no veiculo simulado."""
        return self.faults.codes if self.faults else ()

    @property
    def supports_simulation_controls(self) -> bool:
        """A simulacao aceita escolher combustivel e provocar falhas."""
        return True

    def fuel(self) -> str:
        """Combustivel em uso pelo veiculo simulado."""
        return self.spec.fuel.value if self.spec else ""

    def set_fuel(self, fuel: str) -> None:
        """Troca o combustivel preservando o estado do veiculo.

        Recriar o modelo do zero apagaria nivel de tanque, temperatura e
        hodometro - o carro pareceria ter sido trocado, nao abastecido com
        outro combustivel. O que de fato reinicia e a media de consumo, e isso
        e correto: etanol e gasolina rendem diferente.

        Args:
            fuel: Identificador do combustivel.

        Raises:
            ProviderError: Se o combustivel for desconhecido.
        """
        try:
            kind = FuelKind(fuel)
        except ValueError as error:
            raise ProviderError(f"Combustivel desconhecido: {fuel}") from error

        self.spec = replace(self.spec, fuel=kind) if self.spec else VehicleSpec(fuel=kind)

        if self._model is None:
            logger.info("Combustivel definido como %s antes de conectar", kind.value)
            return

        current = self._model
        self._model = VehicleModel(
            spec=self.spec,
            speed_ms=current.speed_ms,
            rpm=current.rpm,
            gear=current.gear,
            coolant_temp_c=current.coolant_temp_c,
            intake_temp_c=current.intake_temp_c,
            fuel_l=current.fuel_l,
            uptime_s=current.uptime_s,
            odometer_km=current.odometer_km,
        )
        logger.info("Combustivel alterado para %s", kind.value)

    def inject_fault(self, code: str) -> None:
        """Provoca uma falha de diagnostico no veiculo simulado."""
        if self.faults is None:
            raise ProviderError("Simulador nao conectado")
        self.faults.inject(code)

    def clear_faults(self) -> None:
        """Apaga todas as falhas ativas."""
        if self.faults is None:
            raise ProviderError("Simulador nao conectado")
        self.faults.clear()

    def sample(self) -> list[Reading]:
        """Avanca a simulacao em um passo e devolve as leituras do instante.

        Exposto separadamente do ``stream`` para permitir testes deterministicos
        sem envolver o laco de eventos.

        Returns:
            Uma leitura por sinal, todas com o mesmo carimbo de tempo.

        Raises:
            ProviderError: Se o provider nao estiver conectado.
        """
        if not self._connected or self.driver is None:
            raise ProviderError("Simulador nao conectado")

        dt = self.sample_interval_s * self.time_scale
        self._clock_s += dt
        throttle, brake = self.driver.step(dt)
        values = self.model.step(dt, throttle, brake)
        values[Signal.MIL] = 1.0 if (self.faults and self.faults.mil_on) else 0.0

        return [
            Reading(signal=signal, value=value, timestamp=self._clock_s, source=self.kind)
            for signal, value in values.items()
        ]

    async def stream(self) -> AsyncIterator[Reading]:
        """Emite leituras indefinidamente, respeitando o intervalo de amostragem.

        Yields:
            Leituras individuais, na ordem em que o modelo as produz.

        Raises:
            ProviderError: Se o provider nao estiver conectado.
        """
        if not self._connected:
            raise ProviderError("Simulador nao conectado")

        while self._connected:
            for reading in self.sample():
                yield reading
            await asyncio.sleep(self.sample_interval_s)
