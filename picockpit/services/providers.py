"""Contrato unico de fornecimento de telemetria.

Toda origem de dados implementa ``TelemetryProvider``. Trocar simulacao por
OBD-II ou CAN e trocar a implementacao registrada, sem alterar servicos nem UI.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from picockpit.core.models import ProviderKind, Reading


class TelemetryProvider(ABC):
    """Fonte assincrona de leituras de telemetria."""

    #: Identifica a origem dos dados produzidos por esta implementacao.
    kind: ProviderKind

    @abstractmethod
    async def connect(self) -> None:
        """Estabelece a conexao com a fonte de dados."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Encerra a conexao e libera recursos."""

    @abstractmethod
    def stream(self) -> AsyncIterator[Reading]:
        """Emite leituras continuamente ate ser cancelado."""

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Indica se a fonte esta pronta para fornecer dados."""

    def fault_codes(self) -> tuple[str, ...]:
        """Codigos de falha ativos no veiculo.

        Implementacao padrao vazia: nem toda fonte sabe responder isso. O
        provider OBD-II atendera pelo modo 03 na Etapa 8.

        Returns:
            Codigos no formato OBD-II.
        """
        return ()

    @property
    def supports_simulation_controls(self) -> bool:
        """Indica se a fonte aceita comandos que so fazem sentido simulando.

        Escolher o combustivel e provocar uma falha sao acoes sem equivalente
        num veiculo real: o OBD-II le o que existe, nao inventa. A interface
        consulta esta propriedade para esconder os controles quando a origem
        for hardware de verdade.
        """
        return False

    def set_fuel(self, fuel: str) -> None:
        """Troca o combustivel em uso.

        Args:
            fuel: Identificador do combustivel.

        Raises:
            NotImplementedError: Quando a fonte nao suporta a troca.
        """
        raise NotImplementedError("Esta fonte nao permite escolher o combustivel")

    def fuel(self) -> str:
        """Combustivel em uso, ou string vazia quando desconhecido."""
        return ""

    def inject_fault(self, code: str) -> None:
        """Provoca uma falha de diagnostico.

        Args:
            code: Codigo OBD-II a ativar.

        Raises:
            NotImplementedError: Quando a fonte nao suporta injecao.
        """
        raise NotImplementedError("Esta fonte nao permite provocar falhas")

    def clear_faults(self) -> None:
        """Apaga as falhas ativas.

        O provider OBD-II implementara pelo modo 04, que e o mesmo comando que
        um scanner usa para apagar a luz de injecao.

        Raises:
            NotImplementedError: Quando a fonte nao suporta a limpeza.
        """
        raise NotImplementedError("Esta fonte nao permite apagar falhas")

    async def __aenter__(self) -> TelemetryProvider:
        """Conecta ao entrar no contexto assincrono."""
        await self.connect()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        """Desconecta ao sair do contexto assincrono."""
        await self.disconnect()


class ProviderError(RuntimeError):
    """Falha na comunicacao com a fonte de telemetria."""
