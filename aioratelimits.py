import asyncio
from typing import Coroutine


class RateLimiter:
    def __init__(self, count: int, delay: int):
        self.worker_count = count
        self.delay = delay

        self.call_queue = asyncio.Queue()
        self.initialized = False
        self.workers = []

    async def __aenter__(self):
        self.workers = [
            asyncio.create_task(self.worker()) for _ in range(self.worker_count)
        ]
        return self

    async def __aexit__(self, exc_type, exc, tb):
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
