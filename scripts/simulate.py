"""Demonstracao do simulador no terminal.

A Etapa 2 nao tem resultado visual na interface: os dados so chegam ao painel
na Etapa 3. Este script existe para inspecionar os sinais a olho nu, tanto no
container quanto no Raspberry Pi.

Uso:
    python scripts/simulate.py [segundos] [escala_de_tempo]
"""

from __future__ import annotations

import asyncio
import sys

from picockpit.core.events import EventBus
from picockpit.core.models import SIGNAL_UNITS, Signal
from picockpit.services.telemetry_service import TOPIC_STATE, TelemetryService
from picockpit.simulation.provider import SimulationProvider

COLUMNS = (
    Signal.SPEED,
    Signal.RPM,
    Signal.THROTTLE,
    Signal.ENGINE_LOAD,
    Signal.MAP,
    Signal.MAF,
    Signal.COOLANT_TEMP,
    Signal.FUEL_LEVEL,
    Signal.VOLTAGE,
)


async def main(duration_s: float, time_scale: float) -> None:
    """Roda o simulador imprimindo o estado uma vez por segundo."""
    bus = EventBus()
    provider = SimulationProvider(sample_interval_s=0.05, time_scale=time_scale)
    service = TelemetryService(provider, bus)

    header = " | ".join(f"{signal.value:>12}" for signal in COLUMNS)
    units = " | ".join(f"{SIGNAL_UNITS[signal]:>12}" for signal in COLUMNS)
    print(header)
    print(units)
    print("-" * len(header))

    latest = {}
    bus.subscribe(TOPIC_STATE, lambda state: latest.update(state.values))

    await service.start()
    try:
        for _ in range(int(duration_s)):
            await asyncio.sleep(1.0)
            row = " | ".join(f"{latest.get(signal, 0.0):>12.1f}" for signal in COLUMNS)
            print(row, flush=True)
    finally:
        await service.stop()


if __name__ == "__main__":
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
    scale = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
    asyncio.run(main(seconds, scale))
