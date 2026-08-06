"""Perfil de conducao: gera acelerador e freio ao longo do tempo.

Sem isso o simulador produziria ou uma reta sem graca ou ruido sem sentido
fisico. O ciclo abaixo alterna marcha lenta, aceleracao, cruzeiro e frenagem,
que e o suficiente para exercitar todos os sinais do painel.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum


class Phase(str, Enum):
    """Fases do ciclo de conducao."""

    IDLE = "idle"
    ACCELERATE = "accelerate"
    CRUISE = "cruise"
    BRAKE = "brake"


#: Duracao nominal de cada fase, em segundos.
PHASE_DURATION: dict[Phase, float] = {
    Phase.IDLE: 6.0,
    Phase.ACCELERATE: 14.0,
    Phase.CRUISE: 20.0,
    Phase.BRAKE: 8.0,
}

#: Sequencia ciclica das fases.
PHASE_ORDER: tuple[Phase, ...] = (Phase.IDLE, Phase.ACCELERATE, Phase.CRUISE, Phase.BRAKE)


@dataclass(slots=True)
class DriverProfile:
    """Motorista sintetico que percorre o ciclo de fases.

    A saida passa por um filtro de primeira ordem: pedal real nao muda em
    degrau, e transicao suave evita picos irreais de RPM e MAF.
    """

    seed: int | None = 42
    #: Constante de tempo do movimento do pedal, em segundos.
    pedal_tau_s: float = 0.45

    _rng: random.Random = None  # type: ignore[assignment]
    _phase_index: int = 0
    _elapsed: float = 0.0
    _throttle: float = 0.0
    _brake: float = 0.0

    def __post_init__(self) -> None:
        """Inicializa o gerador aleatorio deterministico."""
        self._rng = random.Random(self.seed)

    @property
    def phase(self) -> Phase:
        """Fase atual do ciclo."""
        return PHASE_ORDER[self._phase_index]

    @property
    def throttle(self) -> float:
        """Posicao atual do acelerador, de 0 a 100."""
        return self._throttle

    @property
    def brake(self) -> float:
        """Posicao atual do freio, de 0 a 100."""
        return self._brake

    def _targets(self) -> tuple[float, float]:
        """Alvos de acelerador e freio para a fase atual."""
        if self.phase is Phase.IDLE:
            return 0.0, 0.0
        if self.phase is Phase.ACCELERATE:
            return 55.0 + self._rng.uniform(-10.0, 30.0), 0.0
        if self.phase is Phase.CRUISE:
            return 22.0 + self._rng.uniform(-6.0, 6.0), 0.0
        return 0.0, 45.0 + self._rng.uniform(-10.0, 25.0)

    def step(self, dt: float) -> tuple[float, float]:
        """Avanca o ciclo e devolve acelerador e freio.

        Args:
            dt: Passo de tempo em segundos.

        Returns:
            Tupla ``(acelerador, freio)``, ambos de 0 a 100.
        """
        self._elapsed += dt
        if self._elapsed >= PHASE_DURATION[self.phase]:
            self._elapsed = 0.0
            self._phase_index = (self._phase_index + 1) % len(PHASE_ORDER)

        throttle_target, brake_target = self._targets()
        alpha = min(1.0, dt / self.pedal_tau_s)
        self._throttle += (throttle_target - self._throttle) * alpha
        self._brake += (brake_target - self._brake) * alpha

        self._throttle = max(0.0, min(100.0, self._throttle))
        self._brake = max(0.0, min(100.0, self._brake))
        return self._throttle, self._brake
