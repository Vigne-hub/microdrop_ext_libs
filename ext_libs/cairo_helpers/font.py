from ext_libs.svg_model import scale_to_fit_a_in_b
import cairo


def aspect_fit_font_size(text, shape, cairo_context=None):
    """
    Calculate the maximum font size to fit the provided text into the specified
    shape.

    Args:

        text (str) : Text to fit in shape.
        shape (pandas.Series) : Shape to fit text into (indexed by ['width',
            'height']).
        cairo_context (cairo.Context) : Optional Cairo context.  Can be used,
            for example, to set font style, etc. for fit.

    Returns:

        (tuple) : First item is font size (`float`), and second item is shape
            of text (same format as `shape` input argument) using the font
            size.
    """
    if cairo_context is None:
        surface = cairo.ImageSurface(cairo.FORMAT_A1, 1, 1)
        cairo_context = cairo.Context(surface)

    font_size = 20

    cairo_context.save()
    cairo_context.set_font_size(font_size)
    (x, y, width, height, dx, dy) = cairo_context.text_extents(text)
    text_shape = shape.astype(float)
    text_shape[:] = width, height

    font_scale = scale_to_fit_a_in_b(text_shape, shape)
    font_size *= font_scale
    cairo_context.set_font_size(font_size)
    (x, y, width, height, dx, dy) = cairo_context.text_extents(text)
    cairo_context.restore()

    text_shape[:] = width, height
    return font_size, text_shape
