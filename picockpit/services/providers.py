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

    async def __aenter__(self) -> TelemetryProvider:
        """Conecta ao entrar no contexto assincrono."""
        await self.connect()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        """Desconecta ao sair do contexto assincrono."""
        await self.disconnect()


class ProviderError(RuntimeError):
    """Falha na comunicacao com a fonte de telemetria."""
