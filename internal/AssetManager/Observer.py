"""
Author: G4PLS
Year: 2024
"""

import asyncio

class Observer:
    def __init__(self):
        self.observers: list = []

    def subscribe(self, observer: callable):
        if observer not in self.observers:
            self.observers.append(observer)

    def unsubscribe(self, observer: callable):
        if observer in self.observers:
            self.observers.remove(observer)

    def notify(self, *args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._notify(*args, **kwargs))

    async def _notify(self, *args, **kwargs):
        coroutines = [self._ensure_coroutine(observer, *args, **kwargs) for observer in self.observers]
        await asyncio.gather(*coroutines)

    async def _ensure_coroutine(self, callback: callable, *args, **kwargs):
        if asyncio.iscoroutinefunction(callback):
            return await callback(*args, **kwargs)
        else:
            try:
                return await asyncio.to_thread(callback, *args, **kwargs)
            except Exception as e:
                #log.error(f"Callback {callback.__name__} in {self.event_id} could not be called")
                return await asyncio.sleep(0)