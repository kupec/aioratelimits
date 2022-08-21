# aioratelimits

Client rate limiter. It enqueues function calls and run them as leaky bucket to
ensure specified rates.

## Implementation

Leaky bucket. We have one queue for requests and `count` number of workers.
Each worker can handle one request per `delay` seconds

## Install

```
pip install aioratelimits
```

## Use

The following code prints not more than 2 lines per second.

```python
import asyncio
from aioratelimits import RateLimiter


async def critical_resource(i: int):
    print('request:', i)


async def main():
    async with RateLimiter(count=2, delay=1) as limiter:
        await asyncio.gather(*(
            limiter.run(critical_resource(i))
            for i in range(10)
        ))


asyncio.run(main())
```

Arguments to `RateLimiter`:
- `count` - how many calls can we do in the specified interval
- `delay` - the interval in seconds 
