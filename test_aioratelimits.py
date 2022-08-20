import asyncio
import math
from unittest import mock

import pytest

from aioratelimits import RateLimiter


class Sleep:
    def __init__(self, mocked):
        self.mocked = mocked
        self.mocked.side_effect = self.call
        self.signal_queue = asyncio.Queue()
        self.time = 0

    async def call(self, seconds: int):
        while self.time < seconds:
            await self.signal_queue.get()

    async def scroll_time_by(self, seconds: int):
        self.time += seconds
        await self.signal_queue.put(self.time)


@pytest.fixture(autouse=True)
async def sleep():
    with mock.patch('asyncio.sleep') as mocked:
        sleep_mock = Sleep(mocked)
        yield sleep_mock
        await sleep_mock.scroll_time_by(math.inf)


async def wait_before_suspended(tasks):
    try:
        await asyncio.wait_for(asyncio.gather(*tasks), 0.001)
    except asyncio.TimeoutError:
        pass


async def test_run_immediately_success():
    async def f(a, b):
        return a + b

    async with RateLimiter(count=1, delay=1000) as limiter:
        result = await limiter.run(f('x', 'y'))
        assert result == 'xy'


async def test_run_immediately_exception():
    async def f(a, b):
        raise Exception()

    with pytest.raises(Exception):
        async with RateLimiter(count=1, delay=1000) as limiter:
            await limiter.run(f('x', 'y'))


@pytest.mark.parametrize(
    ('rates_count', 'call_count', 'skip_slots', 'expected_call_count'),
    (
        (1, 1, 0, 1),
        (1, 2, 0, 1),
        (1, 2, 1, 2),
        (2, 1, 0, 1),
        (2, 2, 0, 2),
        (2, 3, 0, 2),
        (2, 3, 1, 3),
    )
)
async def test_run_delay(
    sleep: Sleep,
    rates_count: int,
    call_count: int,
    skip_slots: int,
    expected_call_count: int,
):
    f = mock.AsyncMock()

    async with RateLimiter(count=rates_count, delay=1000) as limiter:
        await sleep.scroll_time_by(skip_slots * 1000)
        await wait_before_suspended([
            limiter.run(f())
            for _ in range(call_count)
        ])

    assert f.await_count == expected_call_count
