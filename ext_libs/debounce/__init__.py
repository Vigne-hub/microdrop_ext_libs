'''
.. versionadded:: 0.1

Ported from `lodash/debounce.js <https://github.com/lodash/lodash/blob/75690245aae87f85afe8f5309230f2029e757f93/debounce.js>`_.

lodash license text::

    The MIT License

    Copyright JS Foundation and other contributors <https://js.foundation/>

    Based on Underscore.js, copyright Jeremy Ashkenas,
    DocumentCloud and Investigative Reporters & Editors <http://underscorejs.org/>

    This software consists of voluntary contributions made by many
    individuals. For exact contribution history, see the revision history
    available at https://github.com/lodash/lodash

    The following license applies to all parts of this software except as
    documented below:

    ====

    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject to
    the following conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
    LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
    WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    ====

    Copyright and related rights for sample code are waived via CC0. Sample
    code is defined as all source code displayed within the prose of the
    documentation.

    CC0: http://creativecommons.org/publicdomain/zero/1.0/

    ====

    Files located in the node_modules and vendor directories are externally
    maintained libraries used by this software which have their own
    licenses; we recommend you read them, as their terms may differ from the
    terms above.
'''
import time

from ext_libs.logging_helpers import _L

from ._version import get_versions


__version__ = get_versions()['version']
del get_versions


class DebounceBase(object):
    def __init__(self, func, wait, leading=False, max_wait=None,
                 trailing=True, debug=False):
        '''
        Creates a debounced function that delays invoking :data:`func` until
        after :data:`wait` milliseconds have elapsed since the last time the
        debounced function was invoked, or until the next browser frame is
        drawn. The debounced function comes with a :meth:`cancel` method to cancel
        delayed :data:`func` invocations and a :meth:`flush` method to immediately
        invoke them.

        Provide optional keyword args to indicate whether :data:`func` should
        be invoked on the leading and/or trailing edge of the :data:`wait`
        timeout. The :data:`func` is invoked with the last arguments provided
        to the debounced function. Subsequent calls to the debounced function
        return the result of the last :data:`func` invocation.

        **Note:** If `leading` and `trailing` options are ``True``,
        :data:`func` is invoked on the trailing edge of the timeout only if the
        debounced function is invoked more than once during the :data:`wait`
        timeout.

        If :data:`wait` is `0` and `leading` is `false`, :data:`func`
        invocation is deferred until the next tick, similar to
        :func:`setTimeout` with a timeout of `0`.

        See `David Corbacho's article <https://css-tricks.com/debouncing-throttling-explained-examples/>`_
        for more information about the **debounce** concept.

        Parameters
        ----------
        func : function
            The function to debounce.
        wait : int
            The number of milliseconds to delay.
        leading : bool, optional
            Specify invoking on the leading edge of the timeout.
        max_wait : int, optional
            The maximum time (in milliseconds) :data:`func` is allowed to be
            delayed before it's invoked.
        trailing : bool, optional
            Specify invoking on the trailing edge of the timeout.

        .. versionchanged:: 0.3
            Use `time.time()` instead of `datetime.datetime.now()` for time
            calculations to reduce overhead by ~10x.

        .. versionchanged:: 0.4
            Add support to accept keyword arguments.

        .. versionchanged:: 0.4.1
            Fix where :data:`max_wait` is not set.
        '''
        self.lastArgs = None
        self.lastKwArgs = None
        self.result = None
        self.timerId = None
        self.lastCallTime = None
        self.leading = leading
        self.trailing = trailing
        self.debug = debug

        self.T_0 = time.time()
        self.lastInvokeTime = self.T_0
        self.maxing = max_wait is not None

        self.wait = 1e-3 * wait
        self.max_wait =  (1e-3 * max(max_wait, wait)
                          if self.maxing else None)
        self.func = func

    def __call__(self, *args, **kwargs):
        '''
        .. versionchanged:: 0.4
            Accept keyword arguments.
        '''
        time_ = time.time()
        isInvoking = self.shouldInvoke(time_)

        self.lastArgs = args
        self.lastKwArgs = kwargs
        self.lastCallTime = time_

        if isInvoking:
            if self.timerId is None:
                return self.leadingEdge(self.lastCallTime)
            if self.maxing:
                # Handle invocations in a tight loop.
                self.timerId = self.startTimer(self.timerExpired, self.wait)
                return self.invokeFunc(self.lastCallTime)
        if self.timerId is None:
            self.timerId = self.startTimer(self.timerExpired, self.wait)
        return self.result

    def invokeFunc(self, time_):
        args = self.lastArgs
        kwargs = self.lastKwArgs

        self.lastArgs = None
        self.lastKwArgs = None
        self.lastInvokeTime = time_
        self.result = self.func(*args, **kwargs)
        if self.debug:
            _L().debug('time: %s, result: %s', time_, self.result)
        return self.result

    def startTimer(self, pendingFunc, wait):
        raise NotImplementedError

    def cancelTimer(self, timer_id):
        raise NotImplementedError

    def leadingEdge(self, time_):
        # Reset any `max_wait` timer.
        self.lastInvokeTime = time_
        # Start the timer for the trailing edge.
        self.timerId = self.startTimer(self.timerExpired, self.wait)
        # Invoke the leading edge.
        return self.invokeFunc(time_) if self.leading else self.result

    def remainingWait(self, time_):
        timeSinceLastCall = time_ - self.lastCallTime
        timeSinceLastInvoke = time_ - self.lastInvokeTime
        timeWaiting = self.wait - timeSinceLastCall

        if self.maxing:
            return min(timeWaiting, self.max_wait - timeSinceLastInvoke)
        else:
            return timeWaiting

    def shouldInvoke(self, time_):
        result = False
        if self.lastCallTime is None:
            # This is the first call.
            result = True
        elif self.maxing:
            timeSinceLastInvoke = time_ - self.lastInvokeTime
            if timeSinceLastInvoke >= self.max_wait:
                # We've hit the `max_wait` limit.
                result = True
        else:
            timeSinceLastCall = time_ - self.lastCallTime

            #  - activity has stopped and we're at the trailing edge; or
            #  - the system time has gone backwards and we're treating it
            #    as the trailing edge
            result = ((timeSinceLastCall >= self.wait) or
                      (timeSinceLastCall < 0))
        if self.debug:
            _L().debug('%s', result)
        return result

    def timerExpired(self):
        time_ = time.time()
        if self.debug:
            _L().debug('time: %s', time_)
        if self.shouldInvoke(time_):
            return self.trailingEdge(time_)
        # Restart the timer.
        self.timerId = self.startTimer(self.timerExpired,
                                       self.remainingWait(time_))

    def trailingEdge(self, time_):
        self.timerId = None
        if self.debug:
            _L().debug('trailing: %s, lastArgs: %s, lastKwArgs: %s',
                       self.trailing, self.lastArgs, self.lastKwArgs)

        # Only invoke if we have `self.lastArgs` which means `func` has been
        # debounced at least once.
        if self.trailing and self.lastArgs is not None:
            return self.invokeFunc(time_)
        self.lastArgs = None
        self.lastKwArgs = None
        return self.result

    def cancel(self):
        if self.timerId is not None:
            self.cancelTimer(self.timerId)
        self.lastInvokeTime = self.T_0
        self.lastArgs = None
        self.lastKwArgs = None
        self.lastCallTime = None
        self.timerId = None

    def flush(self):
        return (self.result if self.timerId is None
                else self.trailingEdge(time.time()))

    def pending(self):
        return self.timerId is not None


class Debounce(DebounceBase):
    '''
    .. versionadded:: 0.3

    Implementation using GObject event loop for delayed function calls.
    '''
    def startTimer(self, pendingFunc, wait):
        '''
        .. versionchanged:: 0.4.1
            Fix timeout duration.
        '''
        from gi.repository import GObject

        def _wrapped(*args):
            pendingFunc()
            # Only call once.
            return False
        timer_id = GObject.timeout_add(int(wait * 1e3), _wrapped)
        _L().debug('timer_id: %s', timer_id)
        return timer_id

    def cancelTimer(self, timer_id):
        from gi.repository import GObject

        _L().debug('timer_id: %s', timer_id)
        return GObject.source_remove(timer_id)
