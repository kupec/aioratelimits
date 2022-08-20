import asyncio
from functools import wraps
from typing import Callable, Awaitable, Coroutine


def ratelimit(count: int, period: int):
    rate_limiter = RateLimiter(count, period)

    def decorator(fn: Callable[..., Awaitable]):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            return await rate_limiter.run(fn(*args, **kwargs))

        return wrapper

    return decorator


class RateLimiter:
    def __init__(self, count: int, delay: int):
        self.workers = [asyncio.create_task(self.worker()) for _ in range(count)]
        self.delay = delay

        self.call_queue = asyncio.Queue()

    async def __aenter__(self):
        pass

    async def __aexit__(self):
        for worker in self.workers:
            worker.cancel()

    async def worker(self):
        while True:
            coro, result_queue = await self.call_queue.get()

            result = None
            error = None
            try:
                result = await coro
            except Exception as exc:
                error = exc
            await result_queue.put((result, error))

            await asyncio.sleep(self.delay)

    async def run(self, coro: Coroutine):
        result_queue = asyncio.Queue()
        await self.call_queue.put((coro, result_queue))
        result, error = await result_queue.get()

        if error:
            raise error

        return result
