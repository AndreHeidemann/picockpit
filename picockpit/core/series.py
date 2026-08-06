"""Series temporais em memoria para os graficos em tempo real.

Fica no nucleo, sem Qt: a janela deslizante, a reamostragem e a escala sao
regras de dominio, testaveis no container. A camada grafica so recebe pontos
prontos.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass(slots=True)
class TimeSeries:
    """Janela deslizante de amostras com reamostragem para desenho.

    Guardar tudo e desenhar tudo seria desperdicio: a 20 Hz, um minuto de
    historico sao 1200 pontos para uns 300 pixels de largura. A serie mantem o
    historico bruto e entrega ao desenho apenas o numero de pontos que cabe na
    tela.

    Attributes:
        window_s: Duracao da janela visivel, em segundos.
        capacity: Numero maximo de amostras retidas.
        minimum: Limite inferior fixo da escala vertical.
        maximum: Limite superior fixo da escala vertical. Quando ``None``, a
            escala acompanha o maior valor da janela.
    """

    window_s: float = 60.0
    capacity: int = 1500
    minimum: float = 0.0
    maximum: float | None = None

    _samples: deque[tuple[float, float]] = field(default_factory=deque)

    def __post_init__(self) -> None:
        """Aplica a capacidade maxima ao buffer."""
        self._samples = deque(maxlen=self.capacity)

    def __len__(self) -> int:
        """Quantidade de amostras retidas."""
        return len(self._samples)

    @property
    def samples(self) -> tuple[tuple[float, float], ...]:
        """Amostras retidas, da mais antiga para a mais recente."""
        return tuple(self._samples)

    @property
    def latest(self) -> float:
        """Ultimo valor recebido, ou zero quando a serie esta vazia."""
        return self._samples[-1][1] if self._samples else 0.0

    def append(self, timestamp: float, value: float) -> None:
        """Acrescenta uma amostra e descarta o que saiu da janela.

        Args:
            timestamp: Instante da amostra, em segundos.
            value: Valor medido.
        """
        self._samples.append((timestamp, value))
        cutoff = timestamp - self.window_s
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()

    def clear(self) -> None:
        """Descarta todas as amostras."""
        self._samples.clear()

    def bounds(self) -> tuple[float, float]:
        """Limites verticais efetivos da janela atual.

        Returns:
            Par ``(minimo, maximo)``, sempre com maximo maior que o minimo.
        """
        if self.maximum is not None:
            return self.minimum, max(self.maximum, self.minimum + 1e-6)

        peak = max((value for _, value in self._samples), default=self.minimum)
        return self.minimum, max(peak, self.minimum + 1e-6)

    def normalized(self, resolution: int = 120) -> list[tuple[float, float]]:
        """Reamostra a janela em coordenadas de 0 a 1.

        O eixo horizontal cobre a janela inteira mesmo quando ha pouco
        historico, para o grafico crescer da direita para a esquerda em vez de
        esticar os primeiros segundos pela tela toda.

        Args:
            resolution: Numero maximo de pontos devolvidos.

        Returns:
            Lista de pares ``(x, y)`` normalizados, em ordem cronologica.
        """
        if len(self._samples) < 2 or resolution < 2:
            return []

        low, high = self.bounds()
        span = high - low
        newest = self._samples[-1][0]
        oldest = newest - self.window_s

        step = max(1, len(self._samples) // resolution)
        points: list[tuple[float, float]] = []
        for index in range(0, len(self._samples), step):
            timestamp, value = self._samples[index]
            x = (timestamp - oldest) / self.window_s
            y = (value - low) / span
            points.append((min(1.0, max(0.0, x)), min(1.0, max(0.0, y))))

        last_time, last_value = self._samples[-1]
        points.append(
            (
                min(1.0, max(0.0, (last_time - oldest) / self.window_s)),
                min(1.0, max(0.0, (last_value - low) / span)),
            )
        )
        return points
