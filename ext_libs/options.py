# -*- coding: utf-8 -*-
from collections import OrderedDict
import logging

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from ext_libs.pygtkhelpers.utils import gsignal
from ext_libs.pygtkhelpers.delegates import SlaveView

logger = logging.getLogger(__name__)


class DebugView(SlaveView):
    def create_ui(self):
        super(DebugView, self).create_ui()
        self.widget.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.ipython_button = Gtk.Button(label = 'IPython...')
        self.ipython_button.set_tooltip_text('Launch embedded IPython shell '
                                             '(`parent` is reference to parent'
                                             ' object.)')

        self.widget.pack_start(self.ipython_button, False, False, 0)

    def on_ipython_button__clicked(self, button):
        import IPython
        import inspect

        # Get parent from stack
        parent_stack = inspect.stack()[1]
        parent = parent_stack[0].f_locals['self']
        IPython.embed()


class DeviceViewInfo(SlaveView):
    def create_ui(self):
        super(DeviceViewInfo, self).create_ui()

        self.labels = OrderedDict([('electrode_count', Gtk.Label()),
                                   ('connection_count', Gtk.Label()),
                                   ('electrode_id', Gtk.Label()),
                                   ('channels', Gtk.Label())])

        self.electrode_id = ''
        self.channels = ''

        self.top_box = Gtk.HBox(False, 0)
        for k in ['electrode_count', 'connection_count']:
            self.top_box.pack_start(self.labels[k], False, False, 10)

        self.bottom_box = Gtk.HBox(False, 0)
        for k in ['electrode_id', 'channels']:
            self.bottom_box.pack_start(self.labels[k], False, False, 10)

        for box in (self.top_box, self.bottom_box):
            self.widget.pack_start(box, False, False, 0)

    def __setattr__(self, name, value):
        if name == 'electrode_id':
            self.labels[name].set_markup('<b>ID:</b> %s' % value)
        elif name == 'channels':
            self.labels[name].set_markup('<b>Channels:</b> %s' % value)
        elif name == 'electrode_count':
            self.labels[name].set_markup('<b>Electrodes:</b> %s' % value)
        elif name == 'connection_count':
            self.labels[name].set_markup('<b>Connections:</b> %s' % value)
        else:
            super(DeviceViewInfo, self).__setattr__(name, value)


class DeviceViewOptions(SlaveView):
    gsignal('connections-toggled', bool)
    gsignal('connections-alpha-changed', float)

    def create_ui(self):
        super(DeviceViewOptions, self).create_ui()
        self.widget.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.connections_button = Gtk.CheckButton('Connections')
        self.connections_alpha_label = Gtk.Label(label = 'Opacity:')

        # Note that the page_size value only makes a difference for scrollbar
        # widgets, and the highest value you'll get is actually
        # (upper - page_size).
        # value, lower, upper, step_increment, page_increment, page_size
        self.connections_alpha_adjustment = Gtk.Adjustment(value = 100, lower = 0, upper = 110, step_increment = 1, page_increment = 10, page_size = 10)
        # Gtk.Adjustment(100, 0, 110, 1, 10, 10) # gkreder

        self.connections_alpha_scale = \
            Gtk.HScale(self.connections_alpha_adjustment)
        self.connections_alpha_scale.set_size_request(100, 40)
        # self.connections_alpha_scale.set_update_policy(gtk.UPDATE_DELAYED) # gkreder
        self.connections_alpha_scale.set_digits(0)
        self.connections_alpha_scale.set_value_pos(Gtk.PositionType.TOP)
        self.connections_alpha_scale.set_draw_value(True)

        widgets = [self.connections_button, self.connections_alpha_label,
                   self.connections_alpha_scale]
        for w in widgets:
            self.widget.pack_start(w, False, False, 5)

    def on_connections_button__toggled(self, button):
        self.emit('connections-toggled', button.get_property('active'))

    def on_connections_alpha_adjustment__value_changed(self, adjustment):
        self.emit('connections-alpha-changed', adjustment.value / 100.)

    @property
    def connections_alpha(self):
        return self.connections_button.get_property('active')

    @connections_alpha.setter
    def connections_alpha(self, value):
        self.connections_alpha_adjustment.value = value * 100

    @property
    def connections(self):
        return self.connections_button.get_property('active')

    @connections.setter
    def connections(self, active):
        self.connections_button.set_property('active', active)


