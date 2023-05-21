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
        while not self.call_queue.empty():
            coro, future = await self.call_queue.get()
            future.cancel()
            coro.close()

    async def worker(self):
        while True:
            coro, future = await self.call_queue.get()

            try:
                result = await coro
                future.set_result(result)
            except Exception as exc:
                future.set_exception(exc)

            await asyncio.sleep(self.delay)

    def run(self, coro: Coroutine) -> asyncio.Future:
        future = asyncio.get_running_loop().create_future()
        self.call_queue.put_nowait((coro, future))
        return future
