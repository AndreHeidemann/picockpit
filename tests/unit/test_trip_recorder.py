"""Testes do gravador de viagens."""

import pytest

from picockpit.core.events import EventBus
from picockpit.core.models import Reading, Signal
from picockpit.data.database import connect
from picockpit.data.trip_repository import TripRepository
from picockpit.services.telemetry_service import TelemetryService
from picockpit.services.trip_recorder import TOPIC_TRIP_SAVED, TripRecorder
from picockpit.simulation.provider import SimulationProvider


class FakeClock:
    """Relogio de parede controlavel."""

    def __init__(self) -> None:
        self.now = 1_000_000.0

    def __call__(self) -> float:
        return self.now


def build() -> tuple[TelemetryService, TripRecorder, TripRepository, EventBus]:
    bus = EventBus()
    repository = TripRepository(connect(":memory:"))
    recorder = TripRecorder(bus, repository, idle_timeout_s=10.0, clock=FakeClock())
    return TelemetryService(SimulationProvider(), bus), recorder, repository, bus


async def drive(
    service: TelemetryService,
    speed: float,
    seconds: float,
    start: float = 0.0,
    odometer: float = 0.0,
    fuel_rate: float = 6.0,
    step: float = 1.0,
) -> tuple[float, float]:
    """Publica um trecho a velocidade constante.

    O hodometro precisa seguir continuo entre chamadas, como num veiculo real,
    por isso entra e sai da funcao.

    Returns:
        Par ``(instante final, hodometro final)``.
    """
    timestamp = start
    for _ in range(int(seconds / step)):
        timestamp += step
        odometer += speed * step / 3600.0
        await service.handle(Reading(signal=Signal.SPEED, value=speed, timestamp=timestamp))
        await service.handle(Reading(signal=Signal.ODOMETER, value=odometer, timestamp=timestamp))
        await service.handle(Reading(signal=Signal.FUEL_RATE, value=fuel_rate, timestamp=timestamp))
    return timestamp, odometer


async def test_starts_recording_once_the_car_moves() -> None:
    service, recorder, _, _ = build()

    await drive(service, speed=40.0, seconds=5)

    assert recorder.recording


async def test_does_not_start_while_idling() -> None:
    service, recorder, _, _ = build()

    await drive(service, speed=0.0, seconds=20)

    assert not recorder.recording


async def test_accumulates_distance_and_fuel() -> None:
    service, recorder, _, _ = build()

    await drive(service, speed=60.0, seconds=60, fuel_rate=6.0)
    trip = recorder.snapshot()

    # 60 km/h por 60 s = 1 km; 6 L/h por 60 s = 0,1 L.
    assert trip.distance_km == pytest.approx(1.0, abs=0.05)
    assert trip.fuel_used_l == pytest.approx(0.1, abs=0.01)


async def test_records_the_top_speed() -> None:
    service, recorder, _, _ = build()

    end, odometer = await drive(service, speed=50.0, seconds=10)
    await drive(service, speed=110.0, seconds=5, start=end, odometer=odometer)

    assert recorder.snapshot().max_speed_kmh == pytest.approx(110.0)


async def test_idle_timeout_closes_the_trip() -> None:
    service, recorder, repository, _ = build()

    end, odometer = await drive(service, speed=60.0, seconds=60)
    await drive(service, speed=0.0, seconds=15, start=end, odometer=odometer)

    assert not recorder.recording
    assert repository.count() == 1


async def test_saved_trip_is_published() -> None:
    service, recorder, _, bus = build()
    seen: list = []
    bus.subscribe(TOPIC_TRIP_SAVED, seen.append)

    await drive(service, speed=60.0, seconds=60)
    await recorder.finish()

    assert len(seen) == 1
    assert seen[0].trip_id is not None


async def test_trip_without_distance_is_discarded() -> None:
    """Ligar o carro e deixar em marcha lenta nao e uma viagem."""
    service, recorder, repository, _ = build()

    await drive(service, speed=40.0, seconds=2, step=1.0)
    recorder._distance_km = 0.0
    saved = await recorder.finish()

    assert saved is None
    assert repository.count() == 0


async def test_finish_without_a_trip_is_safe() -> None:
    _, recorder, repository, _ = build()

    assert await recorder.finish() is None
    assert repository.count() == 0


async def test_moving_time_ignores_stops() -> None:
    service, recorder, _, _ = build()

    end, odometer = await drive(service, speed=60.0, seconds=30)
    await drive(service, speed=0.0, seconds=5, start=end, odometer=odometer)

    trip = recorder.snapshot()
    assert trip.moving_s == pytest.approx(30.0, abs=1.5)
    assert trip.duration_s > trip.moving_s


async def test_faults_seen_during_the_trip_are_stored() -> None:
    service, recorder, repository, bus = build()

    _, odometer = await drive(service, speed=60.0, seconds=30)
    await bus.publish("vehicle.faults", ("P0301",))
    await drive(service, speed=60.0, seconds=30, start=30.0, odometer=odometer)
    saved = await recorder.finish()

    assert saved is not None
    assert saved.fault_codes == ("P0301",)
    assert repository.recent()[0].fault_codes == ("P0301",)


async def test_a_new_trip_starts_clean() -> None:
    service, recorder, repository, _ = build()

    end, odometer = await drive(service, speed=60.0, seconds=60)
    end, odometer = await drive(service, speed=0.0, seconds=15, start=end, odometer=odometer)
    await drive(service, speed=80.0, seconds=30, start=end, odometer=odometer)

    assert recorder.recording
    trip = recorder.snapshot()
    # 80 km/h por 30 s sao 0,67 km; o trecho anterior nao pode vazar para ca.
    assert trip.distance_km == pytest.approx(0.67, abs=0.1)
    assert repository.count() == 1


async def test_odometer_jump_does_not_inflate_the_trip() -> None:
    """Salto no hodometro nao pode virar quilometro rodado."""
    service, recorder, _, _ = build()

    end, odometer = await drive(service, speed=60.0, seconds=30)
    honest = recorder.snapshot().distance_km

    # Hodometro pula 500 km de uma amostra para a outra.
    await drive(service, speed=60.0, seconds=5, start=end, odometer=odometer + 500.0)

    assert recorder.snapshot().distance_km < honest + 0.5
