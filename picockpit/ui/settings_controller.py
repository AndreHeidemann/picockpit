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
from picockpit.core.units import UnitSystem
from picockpit.data.preferences import PreferenceStore
from picockpit.services.providers import TelemetryProvider
from picockpit.services.telemetry_service import TOPIC_FAULTS
from picockpit.simulation.faults import KNOWN_CODES
from picockpit.simulation.spec import FUEL_PROPERTIES, FuelKind

logger = logging.getLogger(__name__)

#: Chaves usadas na tabela de preferencias.
KEY_THEME = "theme"
KEY_FUEL = "fuel"
KEY_UNITS = "units"
KEY_SCALE = "ui_scale"
KEY_TARGET_FPS = "target_fps"

#: Escalas de interface oferecidas. Tela automotiva instalada longe do
#: motorista pede tipografia maior do que a de bancada.
UI_SCALES: tuple[float, ...] = (0.9, 1.0, 1.15, 1.3)

#: Alvos de quadro oferecidos. Reduzir alivia GPU em telas grandes.
FPS_OPTIONS: tuple[int, ...] = (30, 60)


class SettingsController(QObject):
    """Expoe combustivel e injecao de falhas a camada QML."""

    changed = QtSignal()

    def __init__(
        self,
        provider: TelemetryProvider,
        bus: EventBus,
        preferences: PreferenceStore | None = None,
        defaults: dict[str, str] | None = None,
        parent: QObject | None = None,
    ) -> None:
        """Inicializa o controlador e aplica as preferencias guardadas.

        Args:
            provider: Fonte de telemetria ativa.
            bus: Barramento, usado para acompanhar as falhas ativas.
            preferences: Repositorio das preferencias. Sem ele o controlador
                funciona, mas nada e lembrado entre execucoes.
            defaults: Valores de fabrica vindos do arquivo de configuracao.
            parent: Pai Qt opcional.
        """
        super().__init__(parent)
        self._provider = provider
        self._preferences = preferences
        self._defaults = defaults or {}
        self._faults: list[str] = []
        self._unsubscribe = bus.subscribe(TOPIC_FAULTS, self._on_faults)

        stored_fuel = self._stored(KEY_FUEL, "")
        if stored_fuel and provider.supports_simulation_controls:
            try:
                provider.set_fuel(stored_fuel)
            except (NotImplementedError, RuntimeError, ValueError):
                logger.exception("Preferencia de combustivel ignorada: %s", stored_fuel)

    def _stored(self, key: str, default: str) -> str:
        """Le uma preferencia, caindo no valor de fabrica."""
        fallback = self._defaults.get(key, default)
        if self._preferences is None:
            return fallback
        return self._preferences.get(key, fallback)

    def _remember(self, key: str, value: str) -> None:
        """Grava uma preferencia, se houver onde gravar."""
        if self._preferences is not None:
            self._preferences.set(key, value)

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

    # --------------------------------------------------------- preferencias

    @Property(str, notify=changed)  # type: ignore[operator]
    def theme(self) -> str:
        """Tema guardado nas preferencias."""
        return self._stored(KEY_THEME, "normal")

    @Slot(str)
    def setTheme(self, theme: str) -> None:  # noqa: N802 - nome consumido pelo QML
        """Guarda o tema escolhido.

        Args:
            theme: Identificador do tema.
        """
        self._remember(KEY_THEME, theme)
        self.changed.emit()

    @Property(str, notify=changed)  # type: ignore[operator]
    def units(self) -> str:
        """Sistema de unidades ativo."""
        return self._stored(KEY_UNITS, UnitSystem.METRIC.value)

    @Property("QStringList", constant=True)  # type: ignore[operator]
    def unitOptions(self) -> list[str]:  # noqa: N802 - nome consumido pelo QML
        """Sistemas de unidades disponiveis."""
        return [system.value for system in UnitSystem]

    @Slot(str)
    def setUnits(self, units: str) -> None:  # noqa: N802 - nome consumido pelo QML
        """Troca o sistema de unidades.

        Args:
            units: Identificador do sistema.
        """
        if units not in self.unitOptions or units == self.units:
            return
        self._remember(KEY_UNITS, units)
        self.changed.emit()

    @Property(float, notify=changed)  # type: ignore[operator]
    def uiScale(self) -> float:  # noqa: N802 - nome consumido pelo QML
        """Escala da interface."""
        if self._preferences is None:
            return float(self._defaults.get(KEY_SCALE, 1.0))
        return self._preferences.get_float(KEY_SCALE, 1.0)

    @Property("QVariantList", constant=True)  # type: ignore[operator]
    def scaleOptions(self) -> list[float]:  # noqa: N802 - nome consumido pelo QML
        """Escalas oferecidas."""
        return list(UI_SCALES)

    @Slot(float)
    def setUiScale(self, scale: float) -> None:  # noqa: N802 - nome consumido pelo QML
        """Troca a escala da interface.

        Args:
            scale: Fator de escala.
        """
        if scale not in UI_SCALES:
            return
        self._remember(KEY_SCALE, str(scale))
        self.changed.emit()

    @Property(int, notify=changed)  # type: ignore[operator]
    def targetFps(self) -> int:  # noqa: N802 - nome consumido pelo QML
        """Alvo de quadros por segundo."""
        if self._preferences is None:
            return int(self._defaults.get(KEY_TARGET_FPS, 60))
        return self._preferences.get_int(KEY_TARGET_FPS, 60)

    @Property("QVariantList", constant=True)  # type: ignore[operator]
    def fpsOptions(self) -> list[int]:  # noqa: N802 - nome consumido pelo QML
        """Alvos de quadro oferecidos."""
        return list(FPS_OPTIONS)

    @Slot(int)
    def setTargetFps(self, fps: int) -> None:  # noqa: N802 - nome consumido pelo QML
        """Troca o alvo de quadros.

        Args:
            fps: Quadros por segundo.
        """
        if fps not in FPS_OPTIONS:
            return
        self._remember(KEY_TARGET_FPS, str(fps))
        self.changed.emit()

    @Slot()
    def restoreDefaults(self) -> None:  # noqa: N802 - nome consumido pelo QML
        """Apaga as preferencias, voltando aos valores de fabrica."""
        if self._preferences is not None:
            self._preferences.clear()
        self.changed.emit()

    # ------------------------------------------------------------- comandos

    @Slot(str)
    def setFuel(self, fuel: str) -> None:  # noqa: N802 - nome consumido pelo QML
        """Troca o combustivel em uso e guarda a escolha.

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
        self._remember(KEY_FUEL, fuel)
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
