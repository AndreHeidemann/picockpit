"""Controlador da tela de configuracoes.

Reune o que a interface pode mudar em tempo de execucao. Os comandos que so
existem em simulacao ficam atras de uma capacidade declarada pelo provider, e
nao de um `if` sobre o tipo concreto - assim a tela continua correta quando a
origem virar OBD-II ou CAN.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Property, QObject, Slot
from PySide6.QtCore import Signal as QtSignal

from picockpit.core.events import EventBus
from picockpit.services.providers import TelemetryProvider
from picockpit.services.telemetry_service import TOPIC_FAULTS
from picockpit.simulation.faults import KNOWN_CODES
from picockpit.simulation.spec import FUEL_PROPERTIES, FuelKind

logger = logging.getLogger(__name__)


class SettingsController(QObject):
    """Expoe combustivel e injecao de falhas a camada QML."""

    changed = QtSignal()

    def __init__(
        self,
        provider: TelemetryProvider,
        bus: EventBus,
        parent: QObject | None = None,
    ) -> None:
        """Inicializa o controlador.

        Args:
            provider: Fonte de telemetria ativa.
            bus: Barramento, usado para acompanhar as falhas ativas.
            parent: Pai Qt opcional.
        """
        super().__init__(parent)
        self._provider = provider
        self._faults: list[str] = []
        self._unsubscribe = bus.subscribe(TOPIC_FAULTS, self._on_faults)

    def _on_faults(self, codes: tuple[str, ...]) -> None:
        """Acompanha a lista de falhas ativas."""
        self._faults = list(codes)
        self.changed.emit()

    @Property(bool, constant=True)  # type: ignore[operator]
    def simulationControls(self) -> bool:  # noqa: N802 - nome consumido pelo QML
        """Indica se a fonte aceita comandos de simulacao."""
        return self._provider.supports_simulation_controls

    @Property(str, notify=changed)  # type: ignore[operator]
    def fuel(self) -> str:
        """Combustivel em uso."""
        return self._provider.fuel()

    @Property("QStringList", constant=True)  # type: ignore[operator]
    def fuels(self) -> list[str]:
        """Combustiveis disponiveis."""
        return [kind.value for kind in FuelKind]

    @Property("QStringList", notify=changed)  # type: ignore[operator]
    def faultCodes(self) -> list[str]:  # noqa: N802 - nome consumido pelo QML
        """Codigos de falha ativos."""
        return list(self._faults)

    @Property("QStringList", constant=True)  # type: ignore[operator]
    def knownCodes(self) -> list[str]:  # noqa: N802 - nome consumido pelo QML
        """Codigos de falha do catalogo, para o menu de injecao."""
        return list(KNOWN_CODES)

    @Slot(str, result=str)
    def fuelLabel(self, fuel: str) -> str:  # noqa: N802 - nome consumido pelo QML
        """Nome de exibicao de um combustivel.

        Args:
            fuel: Identificador do combustivel.

        Returns:
            Rotulo correspondente, ou o proprio identificador se desconhecido.
        """
        try:
            return FUEL_PROPERTIES[FuelKind(fuel)].label
        except ValueError:
            return fuel

    @Slot(str, result=str)
    def codeDescription(self, code: str) -> str:  # noqa: N802 - nome consumido pelo QML
        """Descricao de um codigo de falha do catalogo.

        Args:
            code: Codigo OBD-II.

        Returns:
            Descricao legivel, ou o proprio codigo se desconhecido.
        """
        known = KNOWN_CODES.get(code)
        return known.description if known else code

    @Slot(str)
    def setFuel(self, fuel: str) -> None:  # noqa: N802 - nome consumido pelo QML
        """Troca o combustivel em uso.

        Args:
            fuel: Identificador do combustivel.
        """
        if not self.simulationControls or fuel == self.fuel:
            return
        try:
            self._provider.set_fuel(fuel)
        except (NotImplementedError, ValueError, RuntimeError):
            logger.exception("Falha ao trocar o combustivel para %s", fuel)
            return
        self.changed.emit()

    @Slot(str)
    def injectFault(self, code: str) -> None:  # noqa: N802 - nome consumido pelo QML
        """Provoca uma falha de diagnostico.

        Args:
            code: Codigo OBD-II a ativar.
        """
        if not self.simulationControls:
            return
        try:
            self._provider.inject_fault(code)
        except (NotImplementedError, RuntimeError):
            logger.exception("Falha ao injetar o codigo %s", code)

    @Slot()
    def clearFaults(self) -> None:  # noqa: N802 - nome consumido pelo QML
        """Apaga as falhas ativas."""
        try:
            self._provider.clear_faults()
        except (NotImplementedError, RuntimeError):
            logger.exception("Falha ao apagar os codigos")

    def close(self) -> None:
        """Cancela a inscricao no barramento."""
        self._unsubscribe()
