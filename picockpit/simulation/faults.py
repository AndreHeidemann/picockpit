"""Injecao de falhas para desenvolver e testar a camada de alertas.

Sem um veiculo com defeito real nao ha como exercitar a luz de injecao nem a
tela de codigos. O injetor cobre esse vazio agora e continua util depois: da
para validar o comportamento do painel sem provocar defeito no carro.

Os codigos seguem o formato OBD-II padrao, o mesmo que o modo 03 devolve.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class TroubleCode:
    """Codigo de falha de diagnostico.

    Attributes:
        code: Codigo no formato OBD-II, por exemplo ``P0301``.
        description: Descricao legivel.
        illuminates_mil: Se a falha acende a luz de injecao no painel.
    """

    code: str
    description: str
    illuminates_mil: bool = True


#: Catalogo de falhas comuns em motor de injecao eletronica, usado tanto pelo
#: injetor quanto pela traducao dos codigos lidos por OBD-II na Etapa 8.
KNOWN_CODES: dict[str, TroubleCode] = {
    code.code: code
    for code in (
        TroubleCode("P0300", "Falha de combustao aleatoria em multiplos cilindros"),
        TroubleCode("P0301", "Falha de combustao no cilindro 1"),
        TroubleCode("P0171", "Mistura pobre demais no banco 1"),
        TroubleCode("P0128", "Motor nao atinge a temperatura de operacao"),
        TroubleCode("P0113", "Sensor de temperatura do ar com sinal alto"),
        TroubleCode("P0442", "Vazamento pequeno no sistema evaporativo", illuminates_mil=False),
    )
}


@dataclass(slots=True)
class FaultInjector:
    """Mantem o conjunto de falhas ativas do veiculo simulado."""

    _active: dict[str, TroubleCode] = field(default_factory=dict)

    @property
    def active(self) -> tuple[TroubleCode, ...]:
        """Falhas ativas, na ordem em que foram injetadas."""
        return tuple(self._active.values())

    @property
    def codes(self) -> tuple[str, ...]:
        """Apenas os codigos das falhas ativas."""
        return tuple(self._active)

    @property
    def mil_on(self) -> bool:
        """Indica se alguma falha ativa acende a luz de injecao."""
        return any(fault.illuminates_mil for fault in self._active.values())

    def inject(self, code: str, description: str | None = None) -> TroubleCode:
        """Ativa uma falha.

        Args:
            code: Codigo OBD-II. Codigos desconhecidos sao aceitos, para nao
                travar o desenvolvimento em cima do catalogo.
            description: Descricao opcional para codigos fora do catalogo.

        Returns:
            A falha ativada.
        """
        known = KNOWN_CODES.get(code)
        fault = known or TroubleCode(code, description or f"Falha {code}")
        self._active[fault.code] = fault
        return fault

    def clear(self, code: str | None = None) -> None:
        """Apaga uma falha especifica, ou todas quando ``code`` e omitido.

        Args:
            code: Codigo a apagar. ``None`` limpa tudo, como faz o modo 04.
        """
        if code is None:
            self._active.clear()
        else:
            self._active.pop(code, None)
