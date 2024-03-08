# -*- coding: utf-8 -*-
import logging
from ext_libs.cairo_helpers.surface import flatten_surfaces
from ext_libs.cairo_helpers.font import aspect_fit_font_size
from ext_libs.svg_model import svg_shapes_to_df
from ext_libs.svg_model.shapes_canvas import ShapesCanvas
import cairo

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib

import pandas as pd

from ext_libs.pygtkhelpers.ui.views.cairo_view import GtkCairoView

logger = logging.getLogger(__name__)


def debounce(timeout):
    def decorator(func):
        def debounced(*args, **kwargs):
            if hasattr(debounced, '_timer'):
                GLib.source_remove(debounced._timer)
            debounced._timer = GLib.timeout_add(timeout, func, *args, **kwargs)
        return debounced
    return decorator


class GtkShapesCanvasView(GtkCairoView):
    def __init__(self, df_shapes, shape_i_columns, padding_fraction=0,
                 **kwargs):
        self.canvas = None
        self.df_shapes = df_shapes
        self.shape_i_columns = shape_i_columns
        self.padding_fraction = padding_fraction
        self._canvas_reset_request = None
        self.cairo_surface = None
        self.df_surfaces = pd.DataFrame(None, columns=['name', 'surface'])

        # Markers to indicate whether drawing needs to be resized, re-rendered,
        # and/or redrawn.
        self._dirty_size = None  # Either `None` or `(width, height)`
        self._dirty_render = False
        self._dirty_draw = False
        self._dirty_check_timeout_id = None  # Periodic callback identifier

        super(GtkShapesCanvasView, self).__init__(**kwargs)

    @classmethod
    def from_svg(cls, svg_filepath, **kwargs):
        df_shapes = svg_shapes_to_df(svg_filepath)
        return cls(df_shapes, 'id', **kwargs)

    def create_ui(self):
        '''
        .. versionchanged:: 0.20
            Debounce window expose and resize handlers to improve
            responsiveness.

        .. versionchanged:: X.X.X
            Call debounced `_on_expose_event` handler on _leading_ edge to make
            UI update more responsive when, e.g., changing window focus.

            Decrease debounce time to 250 ms.
        '''
        super(GtkShapesCanvasView, self).create_ui()
        self.widget.set_events(Gdk.EventType.BUTTON_PRESS |
                               Gdk.EventType.BUTTON_RELEASE |
                               Gdk.EventMask.BUTTON_MOTION_MASK |
                               Gdk.EventMask.BUTTON_PRESS_MASK |
                               Gdk.EventMask.BUTTON_RELEASE_MASK |
                               Gdk.EventMask.POINTER_MOTION_HINT_MASK
                               )
        self.widget.connect('draw', self.draw)

    def reset_canvas(self, width, height):
        canvas_shape = pd.Series([width, height], index=['width', 'height'])
        if self.canvas is None or self.canvas.df_shapes.shape[0] == 0:
            self.canvas = ShapesCanvas(self.df_shapes, self.shape_i_columns,
                                       canvas_shape=canvas_shape,
                                       padding_fraction=self.padding_fraction)
        else:
            self.canvas.reset_shape(canvas_shape)

    def draw(self, widget, cairo_context):
        if self.canvas is None:
            return
        if self.cairo_surface is not None:
            logger.debug('Paint canvas on widget Cairo surface.')
            cairo_context.set_source_surface(self.cairo_surface, 0, 0)
            cairo_context.paint()
        else:
            logger.warning('No Cairo surface to paint to.')

    def render(self):
        self.df_surfaces = pd.DataFrame([['shapes', self.render_shapes()]],
                                        columns=['name', 'surface'])
        self.cairo_surface = flatten_surfaces(self.df_surfaces)

    #TODO: check this @debounce(250)  # Ensure that this method is called at most once every 250 ms.
    def debounced_render(self, width, height):
        """
        Debounce rendering to improve responsiveness.

        ``debounced_render`` is called when the window is resized.
        """
        self._resize(width, height)
        self.render()
        GLib.idle_add(self.widget.queue_draw)

    def on_widget__configure_event(self, widget, event):
        '''
        Called when size of drawing area changes.
        '''
        width, height = event.width, event.height
        logger.debug("on_widget__configure_event: %s, %s", width, height)
        if width < 2 or height < 2:
            # Widget has not been allocated a size yet, so do nothing.
            return

        # The window has been resized; need to re-render the drawing.
        self.debounced_render(width, height)

    def _resize(self, width, height):
        '''
        .. versionadded:: 0.20

        Clear canvas, draw frame off screen, and mark dirty.

        ..notes::
            This method is debounced to improve responsiveness.
        '''
        self._dirty_size = width, height
        self.reset_canvas(width, height)
        GLib.idle_add(self.widget.queue_draw)
        self._dirty_draw = True

    ###########################################################################
    # Render methods
    def get_surface(self, format_=cairo.FORMAT_ARGB32):
        # x, y, width, height = self.widget.get_allocation() # gkreder
        rect = self.widget.get_allocation()
        x = rect.x
        y = rect.y
        width = rect.width
        height = rect.height
        surface = cairo.ImageSurface(format_, width, height)
        return surface

    def render_shapes(self, df_shapes=None, clip=False):
        surface = self.get_surface()
        cairo_context = cairo.Context(surface)

        if df_shapes is None:
            df_shapes = self.canvas.df_canvas_shapes
        logger.debug("Render shapes to Cairo surface: %s", df_shapes.shape[0])

        for path_id, df_path_i in (df_shapes
                                   .groupby(self.canvas
                                            .shape_i_columns)[['x', 'y']]):
            cairo_context.move_to(*df_path_i.iloc[0][['x', 'y']])
            for i, (x, y) in df_path_i[['x', 'y']].iloc[1:].iterrows():
                cairo_context.line_to(x, y)
            cairo_context.close_path()
            cairo_context.set_source_rgb(0, 0, 1)
            cairo_context.fill()
        return surface

    def render_label(self, cairo_context, shape_id, text=None, label_scale=.9):
        '''
        Draw label on specified shape.

        Parameters
        ----------
        cairo_context : cairo.Context
            Cairo context to draw text width.  Can be preconfigured, for
            example, to set font style, etc.
        shape_id : str
            Shape identifier.
        text : str, optional
            Label text.  If not specified, shape identifier is used.
        label_scale : float, optional
            Fraction of limiting dimension of shape bounding box to scale text
            to.
        '''
        text = shape_id if text is None else text
        shape = self.canvas.df_bounding_shapes.loc[shape_id]
        shape_center = self.canvas.df_shape_centers.loc[shape_id]
        font_size, text_shape = \
            aspect_fit_font_size(text, shape * label_scale,
                                 cairo_context=cairo_context)
        cairo_context.set_font_size(font_size)
        cairo_context.move_to(shape_center[0] - .5 * text_shape.width,
                              shape_center[1] + .5 * text_shape.height)
        cairo_context.show_text(text)

    def render_labels(self, labels, color_rgba=None):
        surface = self.get_surface()
        if self.canvas is None or not hasattr(self.canvas, 'df_shape_centers'):
            # Canvas is not initialized, so return empty cairo surface.
            return surface

        cairo_context = cairo.Context(surface)

        color_rgba = (1, 1, 1, 1) if color_rgba is None else color_rgba

        if not isinstance(color_rgba, pd.Series):
            shape_rgba_colors = pd.Series([color_rgba] * self.canvas.df_shape_centers.shape[0],
                                          index=self.canvas.df_shape_centers
                                          .index)
        else:
            shape_rgba_colors = color_rgba

        font_options = cairo.FontOptions()
        font_options.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
        cairo_context.set_font_options(font_options)

        for shape_id, label_i in labels.items():
            # cairo_context.set_source_rgba(*shape_rgba_colors.ix[shape_id]) # gkreder
            cairo_context.set_source_rgba(*shape_rgba_colors.loc[shape_id])
            self.render_label(cairo_context, shape_id, label_i,
                              label_scale=0.6)
        return surface


def parse_args(args=None):
    """Parses arguments, returns (options, args)."""
    import sys
    from argparse import ArgumentParser
    from path_helpers import path

    if args is None:
        args = sys.argv

    parser = ArgumentParser(description='Example app for drawing shapes from '
                            'dataframe, scaled to fit to GTK canvas while '
                            'preserving aspect ratio (a.k.a., aspect fit).')
    parser.add_argument('svg_filepath', type=path, default=None)
    parser.add_argument('-p', '--padding-fraction', type=float, default=0)

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    args = parse_args()
    view = GtkShapesCanvasView.from_svg(args.svg_filepath,
                                        padding_fraction=args.padding_fraction)
    view.widget.connect('destroy', Gtk.main_quit)
    view.show_and_run()
