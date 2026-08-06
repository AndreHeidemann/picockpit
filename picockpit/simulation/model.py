"""Modelo dinamico do veiculo.

O metodo ``step`` e puro no sentido que importa: dado o mesmo estado inicial,
a mesma especificacao e a mesma sequencia de entradas, produz sempre a mesma
saida. Nao consulta relogio nem sorteia nada - o tempo entra como argumento.
Isso torna o comportamento inteiramente testavel e reproduzivel.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from picockpit.core.models import Signal
from picockpit.simulation.spec import (
    AIR_DENSITY_G_PER_L,
    AIR_DENSITY_KG_M3,
    ATMOSPHERIC_KPA,
    FUEL_DENSITY_G_PER_L,
    GRAVITY,
    STOICH_AFR,
    VehicleSpec,
)

#: Pressao no coletor com o acelerador fechado, em kPa.
IDLE_MAP_KPA = 30.0


@dataclass(slots=True)
class VehicleModel:
    """Estado dinamico do veiculo e sua evolucao no tempo."""

    spec: VehicleSpec = field(default_factory=VehicleSpec)

    speed_ms: float = 0.0
    rpm: float = 0.0
    gear: int = 1
    coolant_temp_c: float = 0.0
    fuel_l: float = 0.0
    uptime_s: float = 0.0
    odometer_km: float = 0.0
    throttle: float = 0.0
    brake: float = 0.0

    _shift_timer_s: float = 0.0

    def __post_init__(self) -> None:
        """Coloca o veiculo no estado de partida a frio."""
        self.rpm = self.rpm or self.spec.idle_rpm
        self.coolant_temp_c = self.coolant_temp_c or self.spec.ambient_temp_c
        self.fuel_l = self.fuel_l or self.spec.tank_capacity_l

    # ----------------------------------------------------------------- motor

    def _torque_at(self, rpm: float) -> float:
        """Torque disponivel a plena carga na rotacao informada.

        Curva parabolica com pico em ``peak_torque_rpm``, truncada em zero fora
        da faixa util. Simples de conferir e boa o bastante para um painel.

        Args:
            rpm: Rotacao do motor.

        Returns:
            Torque em Nm, nunca negativo.
        """
        spread = self.spec.redline_rpm - self.spec.peak_torque_rpm
        offset = (rpm - self.spec.peak_torque_rpm) / spread
        return max(0.0, self.spec.peak_torque_nm * (1.0 - 0.55 * offset * offset))

    def _manifold_pressure_kpa(self) -> float:
        """Pressao do coletor de admissao.

        Aspirado: perto do vacuo em marcha lenta, perto da atmosferica em plena
        carga.
        """
        span = ATMOSPHERIC_KPA - IDLE_MAP_KPA
        return IDLE_MAP_KPA + span * (self.throttle / 100.0)

    def _mass_air_flow_g_s(self) -> float:
        """Fluxo de massa de ar admitido, em g/s.

        Um motor quatro tempos admite meia cilindrada por revolucao; o resto e
        a densidade do ar corrigida pela pressao do coletor.
        """
        revs_per_s = self.rpm / 60.0
        volume_per_rev_l = self.spec.displacement_l / 2.0
        density_ratio = self._manifold_pressure_kpa() / ATMOSPHERIC_KPA
        return revs_per_s * volume_per_rev_l * density_ratio * AIR_DENSITY_G_PER_L

    def _engine_load_pct(self) -> float:
        """Carga do motor, como fracao do enchimento maximo do cilindro."""
        return min(100.0, (self._manifold_pressure_kpa() / ATMOSPHERIC_KPA) * 100.0)

    # --------------------------------------------------------- transmissao

    def _rpm_for_speed(self, speed_ms: float, gear: int) -> float:
        """Rotacao imposta pela velocidade na marcha informada."""
        wheel_rps = speed_ms / (2.0 * math.pi * self.spec.wheel_radius_m)
        return wheel_rps * self.spec.total_ratio(gear) * 60.0

    def _update_gear(self, dt: float) -> None:
        """Aplica a logica de cambio automatico com histerese."""
        self._shift_timer_s += dt
        if self._shift_timer_s < self.spec.shift_cooldown_s:
            return

        if self.rpm > self.spec.upshift_rpm and self.gear < self.spec.gear_count():
            self.gear += 1
            self._shift_timer_s = 0.0
        elif self.rpm < self.spec.downshift_rpm and self.gear > 1:
            self.gear -= 1
            self._shift_timer_s = 0.0

    # ------------------------------------------------------------ dinamica

    def _longitudinal_force_n(self) -> float:
        """Soma das forcas longitudinais: tracao, arrasto, rolamento e freio."""
        throttle_fraction = self.throttle / 100.0
        engine_torque = self._torque_at(self.rpm) * throttle_fraction
        engine_torque -= self.spec.engine_brake_nm * (1.0 - throttle_fraction)

        traction = engine_torque * self.spec.total_ratio(self.gear) / self.spec.wheel_radius_m

        drag = 0.5 * AIR_DENSITY_KG_M3 * self.spec.drag_area_m2 * self.speed_ms**2
        rolling = self.spec.rolling_resistance * self.spec.mass_kg * GRAVITY
        braking = self.spec.max_brake_force_n * (self.brake / 100.0)

        resistive = drag + braking
        if self.speed_ms > 0.01:
            resistive += rolling

        return traction - resistive

    # -------------------------------------------------------------- termica

    def _update_temperature(self, dt: float) -> None:
        """Aproxima a temperatura do alvo com constante de tempo unica.

        O alvo sobe com a carga: motor exigido esquenta acima do ponto de
        operacao, o que e o que faz o ponteiro se mexer no painel.
        """
        load_fraction = self._engine_load_pct() / 100.0
        target = self.spec.operating_temp_c + 12.0 * load_fraction
        alpha = min(1.0, dt / self.spec.thermal_tau_s)
        self.coolant_temp_c += (target - self.coolant_temp_c) * alpha

    def _consume_fuel(self, dt: float) -> None:
        """Desconta o combustivel queimado no intervalo."""
        fuel_g_s = self._mass_air_flow_g_s() / STOICH_AFR
        fuel_g_s = max(fuel_g_s, self.spec.idle_fuel_fraction)
        self.fuel_l = max(0.0, self.fuel_l - (fuel_g_s / FUEL_DENSITY_G_PER_L) * dt)

    def _voltage(self) -> float:
        """Tensao do sistema eletrico, com queda proporcional a carga."""
        return self.spec.charging_voltage - 0.5 * (self._engine_load_pct() / 100.0)

    # ---------------------------------------------------------------- passo

    def step(self, dt: float, throttle: float, brake: float) -> dict[Signal, float]:
        """Avanca a simulacao em ``dt`` segundos.

        Args:
            dt: Passo de tempo em segundos. Deve ser positivo.
            throttle: Posicao do acelerador, de 0 a 100.
            brake: Posicao do freio, de 0 a 100.

        Returns:
            Mapa de sinal para valor na unidade canonica.

        Raises:
            ValueError: Se ``dt`` nao for positivo.
        """
        if dt <= 0.0:
            raise ValueError("dt deve ser positivo")

        self.throttle = max(0.0, min(100.0, throttle))
        self.brake = max(0.0, min(100.0, brake))
        self.uptime_s += dt

        acceleration = self._longitudinal_force_n() / self.spec.mass_kg
        self.speed_ms = max(0.0, self.speed_ms + acceleration * dt)
        self.odometer_km += (self.speed_ms * dt) / 1000.0

        # Com o carro parado o motor desacopla e volta para a marcha lenta;
        # em movimento a rotacao e imposta pela transmissao.
        if self.speed_ms < 0.5:
            self.gear = 1
            idle_target = self.spec.idle_rpm + 25.0 * self.throttle
            self.rpm += (idle_target - self.rpm) * min(1.0, dt / 0.3)
        else:
            self.rpm = self._rpm_for_speed(self.speed_ms, self.gear)
            self._update_gear(dt)
            self.rpm = self._rpm_for_speed(self.speed_ms, self.gear)

        self.rpm = max(self.spec.idle_rpm, min(self.spec.redline_rpm, self.rpm))

        self._update_temperature(dt)
        self._consume_fuel(dt)

        return {
            Signal.RPM: self.rpm,
            Signal.SPEED: self.speed_ms * 3.6,
            Signal.COOLANT_TEMP: self.coolant_temp_c,
            Signal.FUEL_LEVEL: (self.fuel_l / self.spec.tank_capacity_l) * 100.0,
            Signal.MAP: self._manifold_pressure_kpa(),
            Signal.MAF: self._mass_air_flow_g_s(),
            Signal.THROTTLE: self.throttle,
            Signal.VOLTAGE: self._voltage(),
            Signal.ENGINE_LOAD: self._engine_load_pct(),
            Signal.UPTIME: self.uptime_s,
            Signal.GEAR: float(self.gear if self.speed_ms >= 0.5 else 0),
            Signal.ODOMETER: self.odometer_km,
        }
