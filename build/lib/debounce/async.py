'''
.. versionadded:: 0.3
'''
import asyncio

from . import DebounceBase


class Debounce(DebounceBase):
    '''
    .. versionadded:: 0.3

    Implementation using asyncio event loop for delayed function calls.
    '''
    def startTimer(self, pendingFunc, wait):
        loop = asyncio.get_event_loop()
        return loop.call_later(wait, pendingFunc)

    def cancelTimer(self, timer_id):
        return timer_id.cancel()
