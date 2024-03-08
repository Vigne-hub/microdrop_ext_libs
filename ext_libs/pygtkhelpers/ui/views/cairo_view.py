# -*- coding: utf-8 -*-
import logging
import os
from pathlib import Path

import ctypes


import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk

# gi.require_version('GdkWin32', '3.0')
# from gi.repository import GdkWin32

from ...delegates import SlaveView

logger = logging.getLogger(__name__)


def find_bin(glob_pattern: str) -> Path:
    """
    Locates a file in system binary paths (i.e., `PATH`) based on a glob pattern.

    Raises
    ------
    RuntimeError
        If no matching file is found.
    """
    search_paths = list(map(Path, os.getenv("PATH").split(";")))
    try:
        return next(
            bin_file
            for lib_dir in search_paths
            for bin_file in lib_dir.glob(glob_pattern)
        )
    except StopIteration:
        raise RuntimeError(
            f"Could not find file matching `{glob_pattern}`. "
            f"Searched the following paths: {search_paths}"
        )


class GtkCairoView(SlaveView):
    """
    SlaveView for Cairo drawing surface.
    """
    def __init__(self, width=None, height=None):
        if width is None:
            self.width = 640
        else:
            self.width = width
        if height is None:
            self.height = 480
        else:
            self.height = height
        super(GtkCairoView, self).__init__()

    def create_ui(self):
        self.widget = Gtk.DrawingArea()
        self.widget.set_size_request(self.width, self.height)
        self.window_xid = None
        self._set_window_title = False

    def show_and_run(self):
        self._set_window_title = True
        super(GtkCairoView, self).show_and_run()
