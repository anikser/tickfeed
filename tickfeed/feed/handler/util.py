import asyncio
from typing import Any, Awaitable, Callable, Iterable


class FanoutFeedCallback:
    def __init__(self, callbacks: Iterable[Callable[[Any, float], Awaitable]]):
        self.callbacks = callbacks

    # This is dangerous. Callbacks MUST NOT modify the tick object
    async def __call__(self, data: Any, timestamp: float):
        await asyncio.gather(*[cb(data, timestamp) for cb in self.callbacks])

    def start(self, loop: asyncio.AbstractEventLoop, multiprocess=False):
        for cb in self.callbacks:
            if hasattr(cb, "start"):
                cb.start(loop, multiprocess)
