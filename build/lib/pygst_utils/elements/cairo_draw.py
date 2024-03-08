#!/usr/bin/env python
__author__ = 'Christian Fobel <christian@fobel.net>'

import traceback
from math import pi
try:
    import cPickle as pickle
except ImportError:
    import pickle

import gi
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gst
from gi.repository import Gtk, GObject

import cairo


def other_draw_on(buf):
    try:
        caps = buf.get_caps()
        width = caps[0]['width']
        height = caps[0]['height']
        framerate = caps[0]['framerate']
        surface = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, width, height, 4 * width)
        ctx = cairo.Context(surface)
    except:
        print("Failed to create cairo surface for buffer")
        traceback.print_exc()
        return

    try:
        center_x = width/4
        center_y = 3*height/4

        # draw a circle
        radius = float(min(width, height)) * 0.25
        ctx.set_source_rgba(0.0, 0.0, 1.0, 0.7)
        ctx.move_to(center_x, center_y)
        ctx.arc(center_x, center_y, radius, 0, 2.0 * pi)
        ctx.close_path()
        ctx.fill()
        ctx.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        ctx.set_font_size(0.3 * radius)
        txt = "Hello World"
        extents = ctx.text_extents(txt)
        ctx.move_to(center_x - extents[2]/2, center_y + extents[3]/2)
        ctx.text_path(txt)
        ctx.fill()
    except:
        print("Failed cairo render")
        traceback.print_exc()


def registered_element(class_):
    """Class decorator for registering a Python element.  Note that decorator
    syntax was extended from functions to classes in Python 2.6, so until 2.6
    becomes the norm we have to invoke this as a function instead of by
    saying::

        @Gstlal_element_register
        class foo(Gst.Element):
            ...

    Until then, you have to do::

        class foo(Gst.Element):
            ...
        Gstlal_element_register(foo)
    """
    from inspect import getmodule
    GObject.type_register(class_)
    getmodule(class_).__Gstelementfactory__ = (class_.__name__, Gst.RANK_NONE,
            class_)
    return class_


@registered_element
class CairoDrawBase(Gst.BaseTransform):
    '''
    Draw using Cairo
    '''
    __Gstdetails__ = (
        "Cairo Draw",
        "Filter",
        __doc__.strip(),
        __author__
    )
    __gproperties__ = {
        'draw-queue': (
            GObject.TYPE_STRING,
            'Pickle-dumped DrawQueue instance',
            'Pickle-dump string of DrawQueue instance',
            'N.', # Default to None
            GObject.PARAM_READWRITE | GObject.PARAM_CONSTRUCT
        ),
    }
    __Gsttemplates__ = (
        Gst.PadTemplate("sink",
            Gst.PAD_SINK, Gst.PAD_ALWAYS,
            Gst.caps_from_string('video/x-raw-rgb,depth=32')
        ),
        Gst.PadTemplate("src",
            Gst.PAD_SRC, Gst.PAD_ALWAYS,
            Gst.caps_from_string('video/x-raw-rgb,depth=32')
        )
    )

    def __init__(self, name, draw_func=other_draw_on):
        self.__GObject_init__()
        self.set_name(name)
        self.set_passthrough(False)
        self.set_in_place(True)
        if draw_func:
            self.draw_on = draw_func

    def do_transform_ip(self, buffer):
        self.draw_on(buffer)
        return Gst.FLOW_OK

    def draw_on(self, buf):
        try:
            caps = buf.get_caps()
            width = caps[0]['width']
            height = caps[0]['height']
            framerate = caps[0]['framerate']
            surface = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, width, height, 4 * width)
            ctx = cairo.Context(surface)
        except:
            print("Failed to create cairo surface for buffer")
            traceback.print_exc()
            return

        try:
            center_x = width/4
            center_y = 3*height/4

            # draw a circle
            radius = float(min(width, height)) * 0.25
            ctx.set_source_rgba(0.0, 0.0, 0.0, 0.7)
            ctx.move_to(center_x, center_y)
            ctx.arc(center_x, center_y, radius, 0, 2.0 * pi)
            ctx.close_path()
            ctx.fill()
            ctx.set_source_rgba(1.0, 1.0, 1.0, 1.0)
            ctx.set_font_size(0.3 * radius)
            txt = "Hello World"
            extents = ctx.text_extents(txt)
            ctx.move_to(center_x - extents[2]/2, center_y + extents[3]/2)
            ctx.text_path(txt)
            ctx.fill()
        except:
            print("Failed cairo render")
            traceback.print_exc()

    def do_set_property(self, prop, val):
        """GObject->set_property virtual method."""
        if prop.name == 'draw-queue':
            self.draw_queue = pickle.loads(val)

    def do_get_property(self, prop):
        """GObject->get_property virtual method."""
        if prop.name == 'draw-queue':
            return pickle.dumps(self.draw_queue)


class CairoDrawQueue(CairoDrawBase):
    def __init__(self, name):
        self.draw_queue = None
        super(CairoDrawQueue, self).__init__(name,
                draw_func=self.render_draw_queue)

    def render_draw_queue(self, buf):
        if self.draw_queue:
            try:
                caps = buf.get_caps()
                width = caps[0]['width']
                height = caps[0]['height']
                surface = cairo.ImageSurface.create_for_data(buf,
                        cairo.FORMAT_ARGB32, width, height, 4 * width)
                ctx = cairo.Context(surface)
            except:
                print("Failed to create cairo surface for buffer")
                traceback.print_exc()
                return
            self.draw_queue.render(ctx)
