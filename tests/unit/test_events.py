"""Testes do barramento de eventos."""

import asyncio

import pytest

from picockpit.core.events import WILDCARD, EventBus


async def test_publish_delivers_to_sync_and_async_handlers() -> None:
    bus = EventBus()
    received: list[str] = []

    async def async_handler(payload: str) -> None:
        received.append(f"async:{payload}")

    bus.subscribe("rpm", lambda payload: received.append(f"sync:{payload}"))
    bus.subscribe("rpm", async_handler)

    await bus.publish("rpm", "2500")

    assert sorted(received) == ["async:2500", "sync:2500"]


async def test_wildcard_receives_every_topic() -> None:
    bus = EventBus()
    seen: list[str] = []
    bus.subscribe(WILDCARD, lambda payload: seen.append(payload))

    await bus.publish("rpm", "a")
    await bus.publish("speed", "b")

    assert seen == ["a", "b"]


async def test_unsubscribe_stops_delivery() -> None:
    bus = EventBus()
    seen: list[str] = []
    cancel = bus.subscribe("rpm", lambda payload: seen.append(payload))

    await bus.publish("rpm", "first")
    cancel()
    await bus.publish("rpm", "second")

    assert seen == ["first"]
    assert bus.subscriber_count("rpm") == 0


async def test_failing_handler_does_not_block_others() -> None:
    bus = EventBus()
    survivors: list[str] = []

    def broken(_: str) -> None:
        raise ValueError("widget quebrado")

    async def broken_async(_: str) -> None:
        raise ValueError("widget assincrono quebrado")

    bus.subscribe("rpm", broken)
    bus.subscribe("rpm", broken_async)
    bus.subscribe("rpm", lambda payload: survivors.append(payload))

    await bus.publish("rpm", "3000")

    assert survivors == ["3000"]


async def test_publish_without_subscribers_is_noop() -> None:
    await EventBus().publish("vazio", None)


async def test_async_handlers_run_concurrently() -> None:
    bus = EventBus()

    async def slow(_: str) -> None:
        await asyncio.sleep(0.05)

    for _ in range(4):
        bus.subscribe("rpm", slow)

    loop = asyncio.get_running_loop()
    started = loop.time()
    await bus.publish("rpm", "x")
    elapsed = loop.time() - started

    assert elapsed < 0.15


def test_clear_removes_all_subscriptions() -> None:
    bus = EventBus()
    bus.subscribe("rpm", lambda _: None)
    bus.clear()
    assert bus.subscriber_count("rpm") == 0


@pytest.mark.parametrize("topic", ["rpm", "speed"])
def test_subscriber_count_is_per_topic(topic: str) -> None:
    bus = EventBus()
    bus.subscribe(topic, lambda _: None)
    assert bus.subscriber_count(topic) == 1
    assert bus.subscriber_count("outro") == 0
