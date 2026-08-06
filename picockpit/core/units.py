"""Sistemas de unidades e conversao para exibicao.

O dominio trabalha sempre na unidade canonica - km/h, C, km/L, km. A conversao
acontece so na borda, na hora de exibir. Guardar valor convertido seria abrir
mao de comparar historico depois de o usuario trocar de unidade.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from picockpit.core.models import Signal

#: Quilometros por milha.
KM_PER_MILE = 1.609344

#: Litros por galao americano.
LITRES_PER_US_GALLON = 3.785411784


class UnitSystem(str, Enum):
    """Sistema de unidades escolhido pelo usuario."""

    METRIC = "metric"
    IMPERIAL = "imperial"


@dataclass(frozen=True, slots=True)
class Measurement:
    """Valor ja convertido, com o rotulo da unidade correspondente."""

    value: float
    unit: str


def celsius_to_fahrenheit(celsius: float) -> float:
    """Converte temperatura de Celsius para Fahrenheit."""
    return celsius * 9.0 / 5.0 + 32.0


def km_to_miles(km: float) -> float:
    """Converte distancia de quilometros para milhas."""
    return km / KM_PER_MILE


def km_per_litre_to_mpg(km_per_litre: float) -> float:
    """Converte consumo de km/L para milhas por galao americano."""
    return km_per_litre / KM_PER_MILE * LITRES_PER_US_GALLON


def litres_to_gallons(litres: float) -> float:
    """Converte volume de litros para galoes americanos."""
    return litres / LITRES_PER_US_GALLON


#: Conversores por sinal no sistema imperial. Sinal ausente daqui nao muda -
#: rotacao, porcentagem e tensao sao iguais nos dois sistemas.
_IMPERIAL: dict[Signal, tuple[object, str]] = {
    Signal.SPEED: (km_to_miles, "mph"),
    Signal.COOLANT_TEMP: (celsius_to_fahrenheit, "F"),
    Signal.INTAKE_TEMP: (celsius_to_fahrenheit, "F"),
    Signal.ODOMETER: (km_to_miles, "mi"),
    Signal.RANGE: (km_to_miles, "mi"),
    Signal.CONSUMPTION: (km_per_litre_to_mpg, "mpg"),
    Signal.FUEL_RATE: (litres_to_gallons, "gal/h"),
}


def convert(signal: Signal, value: float, system: UnitSystem) -> Measurement:
    """Converte um valor canonico para o sistema de unidades pedido.

    Args:
        signal: Sinal ao qual o valor pertence.
        value: Valor na unidade canonica.
        system: Sistema de unidades de destino.

    Returns:
        Valor convertido e o rotulo da unidade.
    """
    from picockpit.core.models import SIGNAL_UNITS

    if system is UnitSystem.METRIC:
        return Measurement(value, SIGNAL_UNITS[signal])

    conversion = _IMPERIAL.get(signal)
    if conversion is None:
        return Measurement(value, SIGNAL_UNITS[signal])

    converter, unit = conversion
    return Measurement(converter(value), unit)  # type: ignore[operator]
