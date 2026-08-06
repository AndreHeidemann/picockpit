"""Parametros fisicos do veiculo simulado.

Separado do modelo para que trocar de "carro" seja trocar de dados, nao de
codigo - util quando o painel for calibrado contra um veiculo real na Etapa 8.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Aceleracao da gravidade em m/s^2.
GRAVITY = 9.81

#: Densidade do ar ao nivel do mar, em g/L (equivale a kg/m^3).
AIR_DENSITY_G_PER_L = 1.2

#: Mesma densidade na unidade usada no calculo de arrasto.
AIR_DENSITY_KG_M3 = AIR_DENSITY_G_PER_L

#: Relacao ar/combustivel estequiometrica para gasolina.
STOICH_AFR = 14.7

#: Densidade da gasolina em g/L.
FUEL_DENSITY_G_PER_L = 745.0

#: Pressao atmosferica ao nivel do mar, em kPa.
ATMOSPHERIC_KPA = 101.3


@dataclass(frozen=True, slots=True)
class VehicleSpec:
    """Caracteristicas mecanicas do veiculo simulado.

    Os valores padrao descrevem um hatch medio de 2.0 L aspirado, escolhido por
    ser um ponto de operacao comum e de numeros facilmente conferiveis.
    """

    mass_kg: float = 1400.0
    #: Produto Cd * area frontal, em m^2.
    drag_area_m2: float = 0.65
    rolling_resistance: float = 0.013
    wheel_radius_m: float = 0.31
    final_drive: float = 3.9
    gear_ratios: tuple[float, ...] = (3.55, 2.05, 1.38, 1.03, 0.81, 0.67)
    displacement_l: float = 2.0
    idle_rpm: float = 800.0
    redline_rpm: float = 6500.0
    #: Torque maximo em Nm e a rotacao onde ocorre.
    peak_torque_nm: float = 200.0
    peak_torque_rpm: float = 3500.0
    max_brake_force_n: float = 7000.0
    #: Torque de freio-motor com acelerador fechado, em Nm.
    engine_brake_nm: float = 35.0
    tank_capacity_l: float = 50.0
    #: Temperatura de operacao do liquido de arrefecimento, em C.
    operating_temp_c: float = 90.0
    ambient_temp_c: float = 25.0
    #: Constante de tempo do aquecimento do motor, em segundos.
    thermal_tau_s: float = 150.0
    #: Rotacoes de troca de marcha para cima e para baixo.
    upshift_rpm: float = 3200.0
    downshift_rpm: float = 1300.0
    #: Intervalo minimo entre trocas, evita oscilacao de marcha.
    shift_cooldown_s: float = 0.8
    #: Tensao do sistema com o motor em funcionamento.
    charging_voltage: float = 14.2

    #: Consumo em marcha lenta como fracao do consumo maximo. Mantido explicito
    #: para nao depender de um valor magico espalhado pelo modelo.
    idle_fuel_fraction: float = field(default=0.03)

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
