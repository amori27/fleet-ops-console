import asyncio
import json
from collections import defaultdict


class PubSub:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)

    async def publish(self, channel: str, message: dict) -> None:
        payload = json.dumps(message)
        for queue in list(self._subscribers.get(channel, set())):
            await queue.put(payload)

    async def subscribe(self, channel: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers[channel].add(q)
        return q

    def unsubscribe(self, channel: str, queue: asyncio.Queue) -> None:
        self._subscribers[channel].discard(queue)
