"""Modelos de dominio da telemetria veicular.

Os valores trafegam entre provider e UI exclusivamente por estes tipos, de modo
que a interface nunca precise saber se a origem foi simulacao, OBD-II ou CAN.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any


class Signal(str, Enum):
    """Sinais de telemetria suportados pela plataforma.

    Herda de ``str`` para serializar direto em JSON/SQLite e para permitir uso
    como chave de topico no barramento de eventos.
    """

    RPM = "rpm"
    SPEED = "speed"
    COOLANT_TEMP = "coolant_temp"
    FUEL_LEVEL = "fuel_level"
    MAP = "map"
    MAF = "maf"
    THROTTLE = "throttle"
    VOLTAGE = "voltage"
    ENGINE_LOAD = "engine_load"
    UPTIME = "uptime"
    GEAR = "gear"
    ODOMETER = "odometer"


#: Unidade canonica de cada sinal. A conversao para unidade de exibicao
#: (km/h vs mph, C vs F) e responsabilidade da camada de apresentacao.
SIGNAL_UNITS: dict[Signal, str] = {
    Signal.RPM: "rpm",
    Signal.SPEED: "km/h",
    Signal.COOLANT_TEMP: "C",
    Signal.FUEL_LEVEL: "%",
    Signal.MAP: "kPa",
    Signal.MAF: "g/s",
    Signal.THROTTLE: "%",
    Signal.VOLTAGE: "V",
    Signal.ENGINE_LOAD: "%",
    Signal.UPTIME: "s",
    Signal.GEAR: "",
    Signal.ODOMETER: "km",
}

#: Faixa fisica plausivel de cada sinal, usada para validar leituras vindas de
#: hardware ruidoso antes de propaga-las para a UI.
SIGNAL_RANGES: dict[Signal, tuple[float, float]] = {
    Signal.RPM: (0.0, 8000.0),
    Signal.SPEED: (0.0, 300.0),
    Signal.COOLANT_TEMP: (-40.0, 215.0),
    Signal.FUEL_LEVEL: (0.0, 100.0),
    Signal.MAP: (0.0, 255.0),
    Signal.MAF: (0.0, 655.0),
    Signal.THROTTLE: (0.0, 100.0),
    Signal.VOLTAGE: (0.0, 18.0),
    Signal.ENGINE_LOAD: (0.0, 100.0),
    Signal.UPTIME: (0.0, 1_000_000.0),
    # Zero representa ponto morto.
    Signal.GEAR: (0.0, 8.0),
    Signal.ODOMETER: (0.0, 9_999_999.0),
}


class ProviderKind(str, Enum):
    """Origem dos dados de telemetria."""

    SIMULATION = "simulation"
    OBD = "obd"
    CAN = "can"


@dataclass(frozen=True, slots=True)
class Reading:
    """Leitura individual de um sinal, ja normalizada para a unidade canonica.

    Attributes:
        signal: Sinal medido.
        value: Valor na unidade canonica de ``SIGNAL_UNITS``.
        timestamp: Instante da medicao, em segundos de relogio monotonico.
        source: Origem do dado.
    """

    signal: Signal
    value: float
    timestamp: float
    source: ProviderKind = ProviderKind.SIMULATION

    @property
    def unit(self) -> str:
        """Unidade canonica do sinal."""
        return SIGNAL_UNITS[self.signal]

    def is_plausible(self) -> bool:
        """Indica se o valor esta dentro da faixa fisica esperada do sinal."""
        low, high = SIGNAL_RANGES[self.signal]
        return low <= self.value <= high


@dataclass(frozen=True, slots=True)
class VehicleState:
    """Fotografia imutavel do estado do veiculo em um instante.

    Mantido imutavel de proposito: a UI recebe sempre um objeto novo, o que
    elimina uma classe inteira de bugs de mutacao concorrente entre a thread do
    Qt e as tarefas asyncio dos providers.
    """

    timestamp: float = 0.0
    source: ProviderKind = ProviderKind.SIMULATION
    values: dict[Signal, float] = field(default_factory=dict)

    def get(self, signal: Signal, default: float = 0.0) -> float:
        """Retorna o valor do sinal, ou ``default`` se ainda nao foi lido."""
        return self.values.get(signal, default)

    def with_reading(self, reading: Reading) -> VehicleState:
        """Devolve um novo estado com a leitura aplicada.

        Args:
            reading: Leitura a incorporar.

        Returns:
            Nova instancia; a original permanece intacta.
        """
        merged = dict(self.values)
        merged[reading.signal] = reading.value
        return replace(
            self,
            timestamp=reading.timestamp,
            source=reading.source,
            values=merged,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serializa o estado para tipos primitivos (log, IPC, persistencia)."""
        return {
            "timestamp": self.timestamp,
            "source": self.source.value,
            "values": {signal.value: value for signal, value in self.values.items()},
        }
