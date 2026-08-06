"""Parametros fisicos do veiculo simulado.

Separado do modelo para que trocar de "carro" seja trocar de dados, nao de
codigo. Os valores atuais descrevem um Ford Ka 1.0 Ti-VCT flex e sao
aproximacoes de catalogo: serao calibrados contra o veiculo real na Etapa 8,
quando houver leitura de OBD-II para comparar.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

#: Aceleracao da gravidade em m/s^2.
GRAVITY = 9.81

#: Densidade do ar ao nivel do mar, em g/L (equivale a kg/m^3).
AIR_DENSITY_G_PER_L = 1.2

#: Mesma densidade na unidade usada no calculo de arrasto.
AIR_DENSITY_KG_M3 = AIR_DENSITY_G_PER_L

#: Pressao atmosferica ao nivel do mar, em kPa.
ATMOSPHERIC_KPA = 101.3


class FuelKind(str, Enum):
    """Combustivel em uso. Num flex, muda a quimica da queima."""

    GASOLINE = "gasoline"
    ETHANOL = "ethanol"


@dataclass(frozen=True, slots=True)
class FuelProperties:
    """Propriedades do combustivel que entram no calculo de consumo.

    Attributes:
        afr: Relacao ar/combustivel estequiometrica.
        density_g_per_l: Densidade em g/L.
        label: Nome curto para exibicao.
        nominal_km_per_l: Consumo tipico em ciclo misto, usado como estimativa
            inicial de autonomia antes de haver historico suficiente.
        torque_factor: Multiplicador de torque. Motor flex rende mais com
            etanol, por causa da octanagem maior e do avanco de ignicao que
            ela permite.
    """

    afr: float
    density_g_per_l: float
    label: str
    nominal_km_per_l: float
    torque_factor: float = 1.0


#: Etanol precisa de bem mais massa de combustivel para a mesma massa de ar,
#: e por isso rende menos quilometros por litro.
FUEL_PROPERTIES: dict[FuelKind, FuelProperties] = {
    FuelKind.GASOLINE: FuelProperties(
        afr=14.7,
        density_g_per_l=745.0,
        label="Gasolina",
        nominal_km_per_l=13.0,
        torque_factor=1.0,
    ),
    FuelKind.ETHANOL: FuelProperties(
        afr=9.0,
        density_g_per_l=789.0,
        label="Etanol",
        nominal_km_per_l=9.0,
        torque_factor=1.07,
    ),
}


@dataclass(frozen=True, slots=True)
class VehicleSpec:
    """Caracteristicas mecanicas do veiculo simulado.

    Padroes correspondentes ao Ford Ka 1.0 Ti-VCT flex, cambio manual de cinco
    marchas, rodas 175/65 R14.
    """

    name: str = "Ford Ka 1.0 Ti-VCT"
    fuel: FuelKind = FuelKind.GASOLINE

    #: Massa em ordem de marcha com um ocupante.
    mass_kg: float = 1050.0
    #: Produto Cd * area frontal, em m^2.
    drag_area_m2: float = 0.66
    rolling_resistance: float = 0.013
    #: Raio dinamico do pneu 175/65 R14.
    wheel_radius_m: float = 0.29
    final_drive: float = 4.06
    gear_ratios: tuple[float, ...] = (3.58, 1.93, 1.28, 0.95, 0.76)
    displacement_l: float = 1.0
    idle_rpm: float = 850.0
    redline_rpm: float = 6500.0
    #: Torque maximo em Nm e a rotacao onde ocorre.
    peak_torque_nm: float = 98.0
    peak_torque_rpm: float = 4250.0
    #: Perdas de transmissao entre volante e roda.
    drivetrain_efficiency: float = 0.85
    max_brake_force_n: float = 6000.0
    #: Torque de freio-motor com acelerador fechado, em Nm.
    engine_brake_nm: float = 22.0
    tank_capacity_l: float = 42.0
    #: Temperatura de operacao do liquido de arrefecimento, em C.
    operating_temp_c: float = 92.0
    ambient_temp_c: float = 25.0
    #: Constante de tempo do aquecimento do motor, em segundos.
    thermal_tau_s: float = 150.0
    #: Constante de tempo do ar admitido, que responde bem mais rapido.
    intake_tau_s: float = 30.0
    #: Rotacoes de troca de marcha para cima e para baixo.
    #: Rotacao de troca com acelerador leve; sobe junto com o acelerador.
    upshift_rpm: float = 2300.0
    downshift_rpm: float = 1350.0
    #: Intervalo minimo entre trocas, evita oscilacao de marcha.
    shift_cooldown_s: float = 0.8
    #: Tensao do sistema com o motor em funcionamento.
    charging_voltage: float = 14.2
    #: Consumo minimo em marcha lenta, em g/s.
    idle_fuel_g_s: float = 0.17
    #: Velocidade abaixo da qual km/L perde sentido e o painel mostra L/h.
    consumption_floor_kmh: float = 5.0
    #: Constante de tempo da media de consumo usada na autonomia, em segundos
    #: de movimento. Curta demais faz a autonomia pular a cada pisada.
    consumption_average_tau_s: float = 90.0

    @property
    def fuel_properties(self) -> FuelProperties:
        """Propriedades do combustivel configurado."""
        return FUEL_PROPERTIES[self.fuel]

    def gear_count(self) -> int:
        """Numero de marchas a frente."""
        return len(self.gear_ratios)

    def total_ratio(self, gear: int) -> float:
        """Relacao total de transmissao para a marcha informada.

        Args:
            gear: Marcha, de 1 ao numero total de marchas.

        Returns:
            Produto da relacao da marcha pela relacao final.
        """
        return self.gear_ratios[gear - 1] * self.final_drive
