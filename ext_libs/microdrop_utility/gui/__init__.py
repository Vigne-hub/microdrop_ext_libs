import logging
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from .. import is_float, is_int


def register_shortcuts(window, shortcuts, enabled_widgets=None,
                       disabled_widgets=None):
    logging.debug('register_shortcuts()...')
    accelgroup = get_accel_group(window, shortcuts,
                                 enabled_widgets=enabled_widgets,
                                 disabled_widgets=disabled_widgets)
    window.add_accel_group(accelgroup)
    logging.debug('DONE')
    return accelgroup


def get_accel_group(window, shortcuts, enabled_widgets=None,
                    disabled_widgets=None):
    if enabled_widgets and disabled_widgets:
        raise ValueError('''Only an enabled list OR a disabled list of'''\
                            ''' widgets is permitted.''')
    accelgroup = Gtk.AccelGroup()

    def action_wrapper(action, enabled, disabled, *args, **kwargs):
        active = window.get_focus()
        if (enabled and active in enabled) or \
            (enabled is None and (disabled is None or active not in disabled)):
            # Perform associated action and stop propagation of key event
            action(*args, **kwargs)
            return True
        else:
            # Ignore shortcut and pass control to default handlers
            return False

    for shortcut, action in shortcuts.items():
        key, modifier = Gtk.accelerator_parse(shortcut)
        accelgroup.connect(key, modifier, Gtk.AccelFlags.VISIBLE,
                                 lambda a, b, c, d, action=action:
                                 action_wrapper(action, enabled_widgets,
                                                disabled_widgets)) # gkreder
        # accelgroup.connect_group(key, modifier, Gtk.AccelFlags.VISIBLE,
        #                          lambda a, b, c, d, action=action:
        #                          action_wrapper(action, enabled_widgets,
        #                                         disabled_widgets))
    return accelgroup


def textentry_validate(textentry, prev_value, type_):
    val = textentry.get_text()
    if val and type_ is float:
        if is_float(val):
            return float(val)
    elif val and type_ is int:
        if is_int(val):
            return int(val)
    textentry.set_text(str(prev_value))
    return prev_value


def contains_pointer(widget, coords=None):
    if coords is None:
        (x,y) = widget.get_pointer()
    else:
        (x,y) = coords

    #try .get_allocated_width() and .get_allocated_height() if .allocate.width fails
    return 0<=x<=widget.get_allocated_width() and 0<=y<=widget.get_allocated_height()
