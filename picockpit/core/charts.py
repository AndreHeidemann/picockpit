"""Quais grandezas ganham grafico em tempo real, e em que escala.

Mora no nucleo pelo mesmo motivo que os temas: e decisao de dominio - o que o
motorista precisa ver variando no tempo - e nao detalhe da camada Qt. No nucleo
tambem fica verificavel no container, sem PySide6.
"""

from __future__ import annotations

from picockpit.core.models import Signal

#: Sinais acompanhados pelos graficos, na ordem de exibicao.
CHARTED_SIGNALS: tuple[Signal, ...] = (
    Signal.SPEED,
    Signal.RPM,
    Signal.CONSUMPTION,
    Signal.ENGINE_LOAD,
)

#: Escalas verticais fixas, em unidade canonica. Sinal ausente daqui usa escala
#: automatica.
#:
#: Ficam em unidade canonica de proposito: a serie tambem e guardada assim, e
#: velocidade e consumo convertem por fator puro, sem deslocamento - a curva
#: normalizada tem a mesma forma nos dois sistemas.
FIXED_SCALES: dict[Signal, tuple[float, float]] = {
    Signal.SPEED: (0.0, 140.0),
    Signal.RPM: (0.0, 7000.0),
    Signal.ENGINE_LOAD: (0.0, 100.0),
}
