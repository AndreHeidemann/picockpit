"""Adaptador entre o barramento de eventos e a camada QML.

Unico ponto onde telemetria vira propriedade de UI. Assina o barramento e
expoe valores ja prontos para binding, sem que o QML saiba se a origem foi
simulacao, OBD-II ou CAN.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject
from PySide6.QtCore import Signal as QtSignal

from picockpit.core.events import EventBus
from picockpit.core.models import Signal, VehicleState
from picockpit.services.telemetry_service import TOPIC_STATE

#: Limites usados para acender os alertas do painel.
LOW_FUEL_PCT = 12.0
HIGH_COOLANT_C = 105.0
LOW_VOLTAGE_V = 12.0


class TelemetryController(QObject):
    """Expoe o estado do veiculo ao QML como propriedades notificaveis.

    Um unico sinal ``updated`` dispara a reavaliacao de todos os bindings. Com
    amostragem na casa de 20 Hz isso e mais barato do que manter um sinal por
    propriedade, e evita atualizacoes fora de sincronia entre ponteiros que
    deveriam representar o mesmo instante.
    """

    updated = QtSignal()

    def __init__(self, bus: EventBus, parent: QObject | None = None) -> None:
        """Inscreve o controlador no barramento.

        Args:
            bus: Barramento de onde o estado consolidado sera lido.
            parent: Pai Qt opcional.
        """
        super().__init__(parent)
        self._state = VehicleState()
        self._unsubscribe = bus.subscribe(TOPIC_STATE, self._on_state)

    def _on_state(self, state: VehicleState) -> None:
        """Recebe o estado consolidado e notifica a interface."""
        self._state = state
        self.updated.emit()

    def _value(self, signal: Signal) -> float:
        """Le um sinal do estado corrente."""
        return self._state.get(signal)

    @Property(float, notify=updated)  # type: ignore[operator]
    def rpm(self) -> float:
        """Rotacao do motor."""
        return self._value(Signal.RPM)

    @Property(float, notify=updated)  # type: ignore[operator]
    def speed(self) -> float:
        """Velocidade em km/h."""
        return self._value(Signal.SPEED)

    @Property(float, notify=updated)  # type: ignore[operator]
    def coolantTemp(self) -> float:  # noqa: N802 - nome consumido pelo QML
        """Temperatura do liquido de arrefecimento em C."""
        return self._value(Signal.COOLANT_TEMP)

    @Property(float, notify=updated)  # type: ignore[operator]
    def fuelLevel(self) -> float:  # noqa: N802 - nome consumido pelo QML
        """Nivel de combustivel em porcentagem."""
        return self._value(Signal.FUEL_LEVEL)

    @Property(float, notify=updated)  # type: ignore[operator]
    def throttle(self) -> float:
        """Posicao do acelerador em porcentagem."""
        return self._value(Signal.THROTTLE)

    @Property(float, notify=updated)  # type: ignore[operator]
    def engineLoad(self) -> float:  # noqa: N802 - nome consumido pelo QML
        """Carga do motor em porcentagem."""
        return self._value(Signal.ENGINE_LOAD)

    @Property(float, notify=updated)  # type: ignore[operator]
    def voltage(self) -> float:
        """Tensao do sistema eletrico."""
        return self._value(Signal.VOLTAGE)

    @Property(float, notify=updated)  # type: ignore[operator]
    def odometer(self) -> float:
        """Distancia percorrida em km."""
        return self._value(Signal.ODOMETER)

    @Property(int, notify=updated)  # type: ignore[operator]
    def gear(self) -> int:
        """Marcha engatada. Zero representa ponto morto."""
        return int(self._value(Signal.GEAR))

    @Property(str, notify=updated)  # type: ignore[operator]
    def gearLabel(self) -> str:  # noqa: N802 - nome consumido pelo QML
        """Marcha em forma textual, com ``N`` para ponto morto."""
        gear = self.gear
        return "N" if gear <= 0 else str(gear)

    @Property(bool, notify=updated)  # type: ignore[operator]
    def lowFuel(self) -> bool:  # noqa: N802 - nome consumido pelo QML
        """Indica reserva de combustivel."""
        return self._value(Signal.FUEL_LEVEL) <= LOW_FUEL_PCT

    @Property(bool, notify=updated)  # type: ignore[operator]
    def overheating(self) -> bool:
        """Indica temperatura acima do limite seguro."""
        return self._value(Signal.COOLANT_TEMP) >= HIGH_COOLANT_C

    @Property(bool, notify=updated)  # type: ignore[operator]
    def lowVoltage(self) -> bool:  # noqa: N802 - nome consumido pelo QML
        """Indica tensao de sistema abaixo do esperado."""
        voltage = self._value(Signal.VOLTAGE)
        return 0.0 < voltage <= LOW_VOLTAGE_V

    def close(self) -> None:
        """Cancela a inscricao no barramento."""
        self._unsubscribe()
