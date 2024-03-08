# -*- coding: utf-8 -*-

"""
    pygtkhelpers.proxy
    ~~~~~~~~~~~~~~~~~~

    Controllers for managing data display widgets.

    :copyright: 2005-2008 by pygtkhelpers Authors
    :license: LGPL 2 or later (see README/COPYING/LICENSE)

    An example session of using a proxy::

        >>> import gi
        >>> gi.require_version('Gtk', '3.0')
        >>> from gi.repository import Gtk
        >>> from microdrop.pygtkhelpers.proxy import proxy_for
        >>> widget = Gtk.Entry()
        >>> proxy = proxy_for(widget)
        >>> proxy
        <GtkEntryProxy object at 0x9aea25c (PyGTKHelperGObjectProxy at 0x9e6ec50)>
        >>> proxy.update('hello')
        >>> proxy.read()
        'hello'
        >>> def changed(proxy, value):
        ...     print proxy, 'changed to', value
        ...
        ...
        >>> proxy.connect('changed', changed)
        32L
        >>> proxy.update('bye bye')
        <GtkEntryProxy object at 0x9aea25c (PyGTKHelperGObjectProxy at 0x9e6ec50)> changed to bye bye
        >>> widget.get_text()
        'bye bye'
        >>> widget.set_text('banana')
        <GtkEntryProxy object at 0x9aea25c (PyGTKHelperGObjectProxy at 0x9e6ec50)> changed to banana
        >>> proxy.read()
        'banana'
"""


import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GObject


from .utils import gsignal
from .ui.widgets import StringList, SimpleComboBox


class GObjectProxy(GObject.GObject):
    """A proxy for a Gtk.Widget

    This proxy provides a common api to gtk widgets, so that they can be used
    without knowing which specific widget they are. All proxy types should
    extend this class.
    """
    __gtype_name__ = 'PyGTKHelperGObjectProxy'

    gsignal('changed', object)

    signal_name = None

    def __init__(self, widget):
        GObject.GObject.__init__(self)
        self.widget = widget
        self.connections = []
        self.connect_widget()

    # public API

    def update(self, value):
        """Update the widget's value
        """
        self.update_internal(value)
        self.emit('changed', self.get_widget_value())

    def read(self):
        """Get the widget's value
        """
        return self.get_widget_value()

    # implementor API

    def block(self):
        for signal_id in self.connections:
            self.widget.handler_block(signal_id)

    def unblock(self):
        for signal_id in self.connections:
            self.widget.handler_unblock(signal_id)

    def update_internal(self, value):
        """Update the widget's value without firing a changed signal
        """
        self.block()
        self.set_widget_value(value)
        self.unblock()

    def widget_changed(self, *args):
        """Called to indicate that a widget's value has been changed.

        This will usually be called from a proxy implementation on response to
        whichever signal was connected in `connect_widget`

        The `*args` are there so you can use this as a signal handler.
        """
        self.emit('changed', self.get_widget_value())

    def set_widget_value(self, value):
        """Set the value of the widget.

        This will update the view to match the value given. This is called
        internally, and is called while the proxy is blocked, so no signals
        are emitted from this action.

        This method should be overriden in subclasses depending on how a
        widget's value is set.
        """

    def get_widget_value(self):
        """Get the widget value.

        This method should be overridden in subclasses to return a value from
        the widget.
        """

    def connect_widget(self):
        """Perform the initial connection of the widget

        the default implementation will connect to the widgets signal
        based on self.signal_name
        """
        if self.signal_name is not None:
            # None for read only widgets
            sid = self.widget.connect(self.signal_name, self.widget_changed)
            self.connections.append(sid)


class SinglePropertyGObjectProxy(GObjectProxy):
    """Proxy which uses a single property to set and get the value.
    """
    prop_name = None

    def set_widget_value(self, value):
        return self.widget.set_property(self.prop_name, value)

    def get_widget_value(self):
        return self.widget.get_property(self.prop_name)


class SingleDelegatedPropertyGObjectProxy(SinglePropertyGObjectProxy):
    """Proxy which uses a delegated property on its widget.
    """
    prop_name = None
    dprop_name = None

    def __init__(self, widget):
        self.owidget = widget
        widget = widget.get_property(self.dprop_name)
        GObjectProxy.__init__(self, widget)


class GtkEntryProxy(SinglePropertyGObjectProxy):
    """Proxy for a Gtk.Entry.
    """
    prop_name = 'text'
    signal_name = 'changed'


class GtkToggleButtonProxy(SinglePropertyGObjectProxy):
    """Proxy for a Gtk.ToggleButton.
    """
    prop_name = 'active'
    signal_name = 'toggled'


class GtkColorButtonProxy(SinglePropertyGObjectProxy):
    """Proxy for a Gtk.ColorButton
    """
    prop_name = 'color'
    signal_name = 'color-set'


class StringListProxy(GObjectProxy):
    """Proxy for a pygtkhelpers.ui.widgets.StringList.
    """
    signal_name = 'content-changed'

    def get_widget_value(self):
        return self.widget.value

    def set_widget_value(self, value):
        self.widget.value = value


class GtkRangeProxy(GObjectProxy):
    """Base class for widgets employing a Gtk.Range.
    """
    signal_name = 'value-changed'

    def get_widget_value(self):
        return self.widget.get_value()

    def set_widget_value(self, value):
        self.widget.set_value(value)


class GtkFileChooserProxy(GObjectProxy):
    """Proxy for a Gtk.FileChooser.
    """
    signal_name = 'selection-changed'

    def get_widget_value(self):
        if self.widget.get_select_multiple():
            return self.widget.get_filenames()
        else:
            return self.widget.get_filename()

    def set_widget_value(self, value):
        if self.widget.get_select_multiple():
            self.widget.unselect_all()
            for filename in value:
                self.widget.select_file(filename)
        else:
            self.widget.set_filename(value)


class GtkFontButtonProxy(SinglePropertyGObjectProxy):
    """Proxy for a Gtk.FontButton.
    """
    signal_name = 'font-set'
    prop_name = 'font-name'


class GtkComboBoxProxy(GObjectProxy):
    """Proxy for a Gtk.ComboBox.
    """
    signal_name = 'changed'

    def get_widget_value(self):
        if not self.active_row:
            return
        return self.get_row_value(self.active_row)

    def set_widget_value(self, value):
        # what a pain in the arse
        for i, row in enumerate(self.model):
            if self.get_row_value(row) == value:
                self.widget.set_active(i)

    @property
    def active_row(self):
        if self.widget.get_active() == -1:
            return
        return self.model[self.widget.get_active()]

    @property
    def model(self):
        return self.widget.get_model()

    def get_row_value(self, row):
        row = list(row)  # XXX: that sucks
        '''
        value = row[1:]
        if not value:
            value = row[0]
        elif len(value) == 1:
            value = value[0]
        '''
        value = row[0]
        return value


class GtkTextViewProxy(SingleDelegatedPropertyGObjectProxy):
    """Proxy for a Gtk.TextView.
    """
    signal_name = 'changed'
    prop_name = 'text'
    dprop_name = 'buffer'


class GtkLabelProxy(SinglePropertyGObjectProxy):
    """Proxy for a Gtk.Label.
    """
    prop_name = 'label'


class GtkImageProxy(SinglePropertyGObjectProxy):
    """Proxy for a Gtk.Image.
    """
    prop_name = 'file'


class GtkLinkButtonProxy(SinglePropertyGObjectProxy):
    """Proxy for a Gtk.LinkButton.
    """
    prop_name = 'uri'


class GtkProgressBarProxy(SinglePropertyGObjectProxy):
    """Proxy for a Gtk.ProgressBar.
    """
    prop_name = 'fraction'


widget_proxies = {
    Gtk.Entry: GtkEntryProxy,
    Gtk.ToggleButton: GtkToggleButtonProxy,
    Gtk.CheckButton: GtkToggleButtonProxy,
    Gtk.RadioButton: GtkToggleButtonProxy,
    Gtk.CheckMenuItem: GtkToggleButtonProxy,
    Gtk.ColorButton: GtkColorButtonProxy,
    Gtk.ComboBox: GtkComboBoxProxy,
    Gtk.SpinButton: GtkRangeProxy,
    Gtk.HScale: GtkRangeProxy,
    Gtk.VScale: GtkRangeProxy,
    Gtk.VScrollbar: GtkRangeProxy,
    Gtk.HScrollbar: GtkRangeProxy,
    Gtk.FileChooserButton: GtkFileChooserProxy,
    Gtk.FileChooserWidget: GtkFileChooserProxy,
    Gtk.FontButton: GtkFontButtonProxy,
    Gtk.Label: GtkLabelProxy,
    Gtk.Image: GtkImageProxy,
    Gtk.LinkButton: GtkLinkButtonProxy,
    Gtk.ProgressBar: GtkProgressBarProxy,
    Gtk.TextView: GtkTextViewProxy,
    StringList: StringListProxy,
    SimpleComboBox: GtkComboBoxProxy,
}


def proxy_for(widget):
    """Create a proxy for a Widget

    :param widget: A Gtk.Widget to proxy

    This will raise a KeyError if there is no proxy type registered for the
    widget type.
    """
    proxy_type = widget_proxies.get(widget.__class__)
    if proxy_type is None:
        raise KeyError('There is no proxy type registered for %r' % widget)
    return proxy_type(widget)


class ProxyGroup(GObject.GObject):
    """A controller to handle multiple proxies, and sub-groups

    A ProxyGroup is a bridge to reduce multiple proxies and sub-groups to a
    single signal based on the key of the individual proxies.
    """

    gsignal('changed', object, str, object)

    def __init__(self):
        GObject.GObject.__init__(self)

    def add_proxy(self, name, proxy):
        """Add a proxy to this group

        :param name: The name or key of the proxy, which will be emitted with
                     the changed signal
        :param proxy: The proxy instance to add
        """
        proxy.connect('changed', self._on_proxy_changed, name)

    def add_proxy_for(self, name, widget):
        """Create a proxy for a widget and add it to this group

        :param name: The name or key of the proxy, which will be emitted with
                     the changed signal
        :param widget: The widget to create a proxy for
        """
        proxy = proxy_for(widget)
        self.add_proxy(name, proxy)

    def add_group(self, group):
        """Add an existing group to this group and proxy its signals

        :param group: The ProxyGroup instance to add
        """
        group.connect('changed', self._on_group_changed)

    def _on_proxy_changed(self, proxy, value, name):
        self.emit('changed', proxy, name, value)

    # XXX namespacing
    def _on_group_changed(self, group, proxy, value, name):
        self.emit('changed', proxy, name, value)
