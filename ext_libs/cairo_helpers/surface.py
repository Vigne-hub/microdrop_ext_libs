from collections import OrderedDict
import types

import cairo
import numpy as np


def np_cairo_view(surface):
    '''
    Args:

        surface (cairo.Surface)

    Returns:

        (numpy.array) : Array *view* of surface image data.
    '''
    return (np.frombuffer(surface.get_data(), dtype='uint8')
            .reshape(surface.get_width(), surface.get_height(), -1))


def flatten_surfaces(df_surfaces, op=cairo.OPERATOR_OVER):
    '''
    Args:

        df_surfaces (pandas.DataFrame) : Frame containing an array of
            `cairo.Surface` instances in a column named `surface`.  Optionally,
            an alpha/opacity value in the range [0, 1] may be specified for
            each surface in the `alpha` column.
        op (cairo.OPERATOR...) : Operator to use for cairo compositing.

    Returns:

        (cairo.Surface) : Flattened surface.
    '''
    df_surfaces = df_surfaces.copy()
    if 'alpha' not in df_surfaces:
        df_surfaces['alpha'] = 1.

    try:
        max_width = max([s.get_width() for s in df_surfaces.surface])
        max_height = max([s.get_height() for s in df_surfaces.surface])
    except ValueError:
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
        return surface

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, max_width, max_height)
    surface_context = cairo.Context(surface)

    # Only paint surfaces with positive alpha value.
    for surface_i, alpha_i in df_surfaces.loc[df_surfaces.alpha > 0,
                                              ['surface', 'alpha']].values:
        surface_context.set_operator(op)
        surface_context.set_source_surface(surface_i)
        surface_context.paint_with_alpha(alpha_i)
    return surface


def composite_surface(surfaces, op=cairo.OPERATOR_OVER, alphas=None):
    max_width = max([s.get_width() for s in surfaces])
    max_height = max([s.get_height() for s in surfaces])

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, max_width, max_height)
    surface_context = cairo.Context(surface)

    for i, surface_i in enumerate(surfaces):
        surface_context.set_operator(op)
        surface_context.set_source_surface(surface_i)
        if alphas is not None:
            surface_context.paint_with_alpha(alphas[i])
        else:
            surface_context.paint()
    return surface


def ensure_list(value):
    if isinstance(value, types.StringTypes):
        return [value]
    else:
        return value


class SurfaceManager(object):
    '''
    Manage ordered surface layers.
    '''
    def __init__(self, surfaces=None):
        self.surfaces = OrderedDict()
        self.hidden = set()
        if surfaces is not None:
            if hasattr(surfaces, 'keys'):
                self.update(surfaces)
            else:
                self.extend(surfaces)

    def append(self, surface, name=None):
        '''
        Append surface.

        Args:

            surface (cairo.Surface)
            name (str) : Label for surface.
        '''
        if name is None:
            name = 'surface%d' % len(self.surfaces)
        self.surfaces[name] = surface
        return name, surface

    def insert(self, index, surface, name=None):
        '''
        Append surface.

        Args:

            surface (cairo.Surface)
            name (str) : Label for surface.
        '''
        if name is None:
            name = 'surface%d' % index
        before_items = self.surfaces.items()[:index]
        after_items = self.surfaces.items()[index:]
        self.surfaces = OrderedDict(before_items + [(name, surface)] +
                                    after_items)
        return name, surface

    def extend(self, surfaces):
        next_index = len(self.surfaces)
        surfaces = [('surface%d' % (next_index + i), surface)
                    for i, surface in enumerate(surfaces)]
        self.surfaces.update(surfaces)
        return surfaces

    def update(self, named_surfaces):
        self.surfaces.update(named_surfaces)
        return named_surfaces.items()

    def flatten(self, name_or_names=None):
        if name_or_names is None:
            name_or_names = self.visible_surface_names()
        surfaces = self[name_or_names]
        return composite_surface(surfaces)

    def visible_surface_names(self):
        return [k for k in self.surfaces.keys() if k not in self.hidden]

    def __getitem__(self, name_or_names=None):
        if isinstance(name_or_names, types.StringTypes):
            return self.surfaces[name_or_names]
        else:
            return [self.surfaces[k] for k in name_or_names]

    def hide(self, name_or_names):
        names = ensure_list(name_or_names)
        for surface in names:
            self.hidden.add(surface)

    def show(self, name_or_names):
        names = ensure_list(name_or_names)
        for surface in names:
            if surface in self.hidden:
                self.hidden.remove(surface)

    def clear(self):
        self.hidden.clear()
        self.surfaces.clear()

    def remove(self, name_or_names):
        names = ensure_list(name_or_names)
        for surface in names:
            if surface in self.hidden:
                self.hidden.remove(surface)
            del self.surfaces[surface]

    def to_frame(self):
        import pandas as pd

        return pd.DataFrame(self.surfaces.items(), columns=['name', 'surface'])


class AlphaSurfaceManager(SurfaceManager):
    '''
    Manage ordered surface layers, each layer with a corresponding alpha
    multiplier in the inclusive range [0, 1].
    '''
    def __init__(self, surfaces=None):
        self.alphas = {}
        super(AlphaSurfaceManager, self).__init__(surfaces=surfaces)

    def append(self, surface, name=None, alpha=1.):
        name = super(AlphaSurfaceManager, self).append(surface, name=name)
        self.alphas[name] = alpha

    def insert(self, index, surface, name=None, alpha=1.):
        name = super(AlphaSurfaceManager, self).insert(index, surface, name=name)
        self.alphas[name] = alpha

    def extend(self, surfaces, alphas=None):
        if alphas is not None:
            assert(len(surfaces) == len(alphas))
        surface_pairs = super(AlphaSurfaceManager, self).extend(surfaces)
        for i, (name, surface) in enumerate(surface_pairs):
            self.alphas[name] = alphas[i] if alphas is not None else 1.

    def update(self, named_surfaces, alphas=None):
        if alphas is not None:
            assert(len(named_surfaces) == len(alphas))
        surface_pairs = super(AlphaSurfaceManager, self).update(named_surfaces)
        for i, (name, surface) in enumerate(surface_pairs):
            self.alphas[name] = alphas[i] if alphas is not None else 1.

    def flatten(self, name_or_names=None):
        if name_or_names is None:
            name_or_names = self.visible_surface_names()
        names = ensure_list(name_or_names)
        surfaces = self[names]
        return composite_surface(surfaces, alphas=[self.alphas[n]
                                                   for n in names])

    def clear(self):
        super(AlphaSurfaceManager, self).clear()
        self.alphas.clear()

    def remove(self, name_or_names):
        super(AlphaSurfaceManager, self).remove()
        for name in ensure_list(name_or_names):
            del self.alphas[name]

    def to_frame(self):
        df_surfaces = super(AlphaSurfaceManager, self).to_frame()
        df_surfaces['alpha'] = [self.alphas[k] for k in df_surfaces['name']]
        return df_surfaces
