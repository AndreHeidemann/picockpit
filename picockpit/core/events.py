"""Barramento de eventos assincrono usado para desacoplar produtores da UI.

Um provider publica leituras sem saber quem consome; widgets se inscrevem em
sinais especificos sem saber de onde os dados vieram. E o mecanismo que
sustenta a troca ``SimulationProvider -> OBDProvider -> CANProvider`` sem tocar
na camada de apresentacao.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

Handler = Callable[[Any], Any | Awaitable[Any]]

#: Topico curinga: recebe todos os eventos publicados no barramento.
WILDCARD = "*"


class EventBus:
    """Publish/subscribe assincrono, em processo, com isolamento de falhas.

    Um handler que levanta excecao e registrado no log e descartado daquele
    ciclo, sem derrubar os demais assinantes nem o produtor. Num painel
    automotivo, um widget quebrado nunca pode congelar o velocimetro.
    """

    def __init__(self) -> None:
        """Inicializa um barramento vazio."""
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Handler) -> Callable[[], None]:
        """Inscreve ``handler`` em ``topic``.

        Args:
            topic: Nome do topico, ou ``WILDCARD`` para receber tudo.
            handler: Callable sincrono ou corrotina que recebe o payload.

        Returns:
            Funcao que cancela esta inscricao quando chamada.
        """
        self._handlers[topic].append(handler)

        def unsubscribe() -> None:
            with_topic = self._handlers.get(topic)
            if with_topic and handler in with_topic:
                with_topic.remove(handler)

        return unsubscribe

    async def publish(self, topic: str, payload: Any) -> None:
        """Publica ``payload`` em ``topic`` e aguarda todos os handlers.

        Handlers sincronos rodam inline; corrotinas rodam concorrentemente.

        Args:
            topic: Topico do evento.
            payload: Dado entregue aos assinantes.
        """
        handlers = [*self._handlers.get(topic, []), *self._handlers.get(WILDCARD, [])]
        if not handlers:
            return

        pending: list[Awaitable[Any]] = []
        for handler in handlers:
            try:
                result = handler(payload)
            except Exception:
                logger.exception("Handler sincrono falhou no topico %s", topic)
                continue
            if inspect.isawaitable(result):
                pending.append(result)

        if not pending:
            return

        results = await asyncio.gather(*pending, return_exceptions=True)
        for result in results:
            if isinstance(result, BaseException):
                logger.error("Handler assincrono falhou no topico %s", topic, exc_info=result)

    def subscriber_count(self, topic: str) -> int:
        """Numero de handlers inscritos diretamente em ``topic``."""
        return len(self._handlers.get(topic, []))

    def clear(self) -> None:
        """Remove todas as inscricoes. Usado principalmente em testes."""
        self._handlers.clear()
