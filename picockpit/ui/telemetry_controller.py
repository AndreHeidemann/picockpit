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
from picockpit.core.units import UnitSystem, convert
from picockpit.services.telemetry_service import TOPIC_FAULTS, TOPIC_STATE

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
        self._units = UnitSystem.METRIC
        self._faults: list[str] = []
        self._unsubscribe_state = bus.subscribe(TOPIC_STATE, self._on_state)
        self._unsubscribe_faults = bus.subscribe(TOPIC_FAULTS, self._on_faults)

    def _on_state(self, state: VehicleState) -> None:
        """Recebe o estado consolidado e notifica a interface."""
        self._state = state
        self.updated.emit()

    def _on_faults(self, codes: tuple[str, ...]) -> None:
        """Recebe a lista de codigos de falha ativos."""
        self._faults = list(codes)
        self.updated.emit()

    def set_units(self, units: str | UnitSystem) -> None:
        """Troca o sistema de unidades de exibicao.

        O dominio continua em unidade canonica; so a borda converte. Guardar
        valor convertido tornaria o historico incomparavel depois de uma troca.

        Args:
            units: Sistema de unidades desejado.
        """
        try:
            system = UnitSystem(units)
        except ValueError:
            return
        if system is self._units:
            return
        self._units = system
        self.updated.emit()

    def _value(self, signal: Signal) -> float:
        """Le um sinal do estado corrente, ja convertido para exibicao."""
        return convert(signal, self._state.get(signal), self._units).value

    def _raw(self, signal: Signal) -> float:
        """Le um sinal na unidade canonica, sem conversao."""
        return self._state.get(signal)

    def _unit(self, signal: Signal) -> str:
        """Rotulo da unidade de exibicao de um sinal."""
        return convert(signal, 0.0, self._units).unit

    @Property(str, notify=updated)  # type: ignore[operator]
    def speedUnit(self) -> str:  # noqa: N802 - nome consumido pelo QML
        """Unidade de velocidade em uso."""
        return self._unit(Signal.SPEED)

    @Property(str, notify=updated)  # type: ignore[operator]
    def temperatureUnit(self) -> str:  # noqa: N802 - nome consumido pelo QML
        """Unidade de temperatura em uso."""
        return self._unit(Signal.COOLANT_TEMP)

    @Property(str, notify=updated)  # type: ignore[operator]
    def consumptionUnit(self) -> str:  # noqa: N802 - nome consumido pelo QML
        """Unidade de consumo em uso."""
        return self._unit(Signal.CONSUMPTION)

    @Property(str, notify=updated)  # type: ignore[operator]
    def fuelRateUnit(self) -> str:  # noqa: N802 - nome consumido pelo QML
        """Unidade de consumo horario em uso."""
        return self._unit(Signal.FUEL_RATE)

    @Property(str, notify=updated)  # type: ignore[operator]
    def distanceUnit(self) -> str:  # noqa: N802 - nome consumido pelo QML
        """Unidade de distancia em uso."""
        return self._unit(Signal.ODOMETER)

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
    def map(self) -> float:
        """Pressao do coletor de admissao em kPa."""
        return self._value(Signal.MAP)

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
        return int(self._raw(Signal.GEAR))

    @Property(str, notify=updated)  # type: ignore[operator]
    def gearLabel(self) -> str:  # noqa: N802 - nome consumido pelo QML
        """Marcha em forma textual, com ``N`` para ponto morto."""
        gear = self.gear
        return "N" if gear <= 0 else str(gear)

    @Property(float, notify=updated)  # type: ignore[operator]
    def intakeTemp(self) -> float:  # noqa: N802 - nome consumido pelo QML
        """Temperatura do ar admitido em C."""
        return self._value(Signal.INTAKE_TEMP)

    @Property(float, notify=updated)  # type: ignore[operator]
    def fuelRate(self) -> float:  # noqa: N802 - nome consumido pelo QML
        """Consumo horario em L/h."""
        return self._value(Signal.FUEL_RATE)

    @Property(float, notify=updated)  # type: ignore[operator]
    def consumption(self) -> float:
        """Consumo instantaneo em km/L. Zero significa parado."""
        return self._value(Signal.CONSUMPTION)

    @Property(bool, notify=updated)  # type: ignore[operator]
    def moving(self) -> bool:
        """Indica se ha velocidade suficiente para o consumo ter significado."""
        return self._raw(Signal.CONSUMPTION) > 0.0

    @Property(float, notify=updated)  # type: ignore[operator]
    def range(self) -> float:
        """Autonomia estimada em km."""
        return self._value(Signal.RANGE)

    @Property(bool, notify=updated)  # type: ignore[operator]
    def milOn(self) -> bool:  # noqa: N802 - nome consumido pelo QML
        """Indica luz de injecao acesa."""
        return self._value(Signal.MIL) >= 1.0

    @Property("QStringList", notify=updated)  # type: ignore[operator]
    def faultCodes(self) -> list[str]:  # noqa: N802 - nome consumido pelo QML
        """Codigos de falha ativos."""
        return list(self._faults)

    @Property(bool, notify=updated)  # type: ignore[operator]
    def lowFuel(self) -> bool:  # noqa: N802 - nome consumido pelo QML
        """Indica reserva de combustivel."""
        return self._raw(Signal.FUEL_LEVEL) <= LOW_FUEL_PCT

    @Property(bool, notify=updated)  # type: ignore[operator]
    def overheating(self) -> bool:
        """Indica temperatura acima do limite seguro.

        Comparado sempre em Celsius: limiar de seguranca e propriedade do
        motor, nao da unidade que o motorista escolheu ver.
        """
        return self._raw(Signal.COOLANT_TEMP) >= HIGH_COOLANT_C

    @Property(bool, notify=updated)  # type: ignore[operator]
    def lowVoltage(self) -> bool:  # noqa: N802 - nome consumido pelo QML
        """Indica tensao de sistema abaixo do esperado."""
        voltage = self._raw(Signal.VOLTAGE)
        return 0.0 < voltage <= LOW_VOLTAGE_V

    def close(self) -> None:
        """Cancela as inscricoes no barramento."""
        self._unsubscribe_state()
        self._unsubscribe_faults()
