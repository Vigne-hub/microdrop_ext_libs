# coding: utf-8
import contextlib
import inspect
import logging
import os
import sys

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


@contextlib.contextmanager
def logging_restore(clear_handlers=False):
    '''
    Save logging state upon entering context and restore upon leaving.

    Parameters
    ----------
    clear_handlers : bool, optional
        If ``True``, clear active logging handlers while within context.

    Example
    -------

    Set logging level to ``DEBUG``, set logging level to ``INFO`` within
    context, and verify logging level is restored to ``DEBUG`` upon exiting
    context.

    >>> from microdrop.ext_libs import logging_helpers as lh
    >>> import logging
    >>> logging.basicConfig(level=logging.DEBUG)
    >>> logging.debug('hello, world!')
    DEBUG:root:hello, world!
    >>> with lh.logging_restore():
    ...     logging.root.setLevel(logging.DEBUG)
    ...
    >>> logging.debug('hello, world!')
    DEBUG:root:hello, world!

    '''
    handlers = logging.root.handlers[:]
    level = logging.root.getEffectiveLevel()
    if clear_handlers:
        for h in handlers:
            logging.root.removeHandler(h)
    yield
    handlers_to_remove = logging.root.handlers[:]
    [logging.root.removeHandler(h) for h in handlers_to_remove]
    [logging.root.addHandler(h) for h in handlers]
    logging.root.setLevel(level)


def _L(skip=0):
    '''Shorthand to get logger for current function frame.'''
    return logging.getLogger(caller_name(skip + 1))


# Public Domain, i.e. feel free to copy/paste
# Considered a hack in Python 2
#
# Ported from [here][1].
# See [here][2] for modifications.
#
# [1]: https://gist.github.com/techtonik/2151727
# [2]: https://gist.github.com/techtonik/2151727#gistcomment-2333747
def caller_name(skip=2):
    """
    Get a name of a caller in the format module.class.method

    `skip` specifies how many levels of stack to skip while getting caller
    name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.

    An empty string is returned if skipped levels exceed stack height


    .. versionchanged:: v0.4
        Look up the module name from the frame globals dictionary rather than
        by calling :func:`inspect.getmodule()`.  Calling
        :func:`inspect.getmodule()` is ~1000x slower compared to looking up the
        module name from the globals dictionary (~80 µs vs 90 ns).
    """
    def stack_(frame):
        framelist = []
        while frame:
            framelist.append(frame)
            frame = frame.f_back
        return framelist

    stack = stack_(sys._getframe(1))
    start = 0 + skip
    if len(stack) < start + 1:
        return ''
    parentframe = stack[start]

    # Look up module name from globals dictionary in frame rather than by
    # calling `inspect.getmodule()`.  Calling `inspect.getmodule()` is ~1000x
    # slower compared to looking up the module name from the globals dictionary
    # (~80 µs vs 90 ns).
    module_name = parentframe.f_globals['__name__']
    name = [module_name]

    # detect classname
    if 'self' in parentframe.f_locals:
        # I don't know any way to detect call from the object method
        # XXX: there seems to be no way to detect static method call - it will
        #      be just a function call
        name.append(parentframe.f_locals['self'].__class__.__name__)
    codename = parentframe.f_code.co_name
    if codename != '<module>':  # top level usually
        name.append(codename)  # function or a method
    return ".".join(name)
