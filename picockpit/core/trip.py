"""Modelo de viagem.

Uma viagem e o resumo de um trecho rodado: quanto andou, quanto gastou, quanto
tempo levou e o que deu errado no caminho. E a unidade que faz sentido guardar
- registrar cada amostra encheria o cartao sem acrescentar nada que o motorista
va olhar.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Trip:
    """Resumo de um trecho rodado.

    Attributes:
        started_at: Instante de inicio, em segundos desde a epoca.
        ended_at: Instante de encerramento, em segundos desde a epoca.
        duration_s: Duracao total, incluindo paradas.
        moving_s: Tempo efetivamente em movimento.
        distance_km: Distancia percorrida.
        fuel_used_l: Combustivel consumido.
        max_speed_kmh: Velocidade maxima atingida.
        fuel: Combustivel em uso durante a viagem.
        fault_codes: Codigos de falha vistos durante a viagem.
        trip_id: Identificador atribuido pelo banco.
    """

    started_at: float
    ended_at: float
    duration_s: float
    moving_s: float
    distance_km: float
    fuel_used_l: float
    max_speed_kmh: float
    fuel: str = "gasoline"
    fault_codes: tuple[str, ...] = field(default_factory=tuple)
    trip_id: int | None = None

    @property
    def average_consumption_km_l(self) -> float:
        """Consumo medio da viagem, em km/L.

        Returns:
            Zero quando nao houve consumo mensuravel, para nao dividir por zero
            nem exibir infinito no historico.
        """
        if self.fuel_used_l <= 0.0:
            return 0.0
        return self.distance_km / self.fuel_used_l

    @property
    def average_speed_kmh(self) -> float:
        """Velocidade media considerando apenas o tempo em movimento.

        Media sobre o tempo total afundaria com qualquer semaforo e diria mais
        sobre o transito do que sobre a viagem.
        """
        if self.moving_s <= 0.0:
            return 0.0
        return self.distance_km / (self.moving_s / 3600.0)
