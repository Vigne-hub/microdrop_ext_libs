# coding: utf-8
import logging

from path_helpers import path
import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst

import pandas as pd
import platform


if platform.system() == 'Linux':
    VIDEO_SOURCE_PLUGIN = 'v4l2src'
    DEVICE_KEY = 'device'
else:
    VIDEO_SOURCE_PLUGIN = 'dshowvideosrc'
    DEVICE_KEY = 'device-name'


class DeviceNotFound(Exception):
    pass


def get_video_source_names():
    '''
    Returns
    -------
    list
        List of names (:class:`str`) of video source devices available for use
        with GStreamer.
    '''
    if platform.system() == 'Linux':
        try:
            devices = path('/dev/v4l/by-id').listdir()
        except OSError:
            raise DeviceNotFound('No devices available')
    else:
        try:
            video_source = Gst.element_factory_make(VIDEO_SOURCE_PLUGIN,
                                                    'video_source')
            devices = video_source.probe_get_values_name(DEVICE_KEY)
        except Exception:
            devices = []
        if not devices:
            raise DeviceNotFound('No devices available')
    return devices


def get_allowed_capabilities(device_name):
    '''
    Parameters
    ----------
    device_name : str
        Name of device to query.

    Returns
    -------
    pandas.DataFrame
        Video source capabilities queried from source pad of device with
        specified device name.  Columns contain GStreamer data types (e.g.,
        :class:`Gst.Fourcc`, :class:`Gst.Fraction`, etc.).

        See :func:`expand_allowed_capabilities` to convert output of this
        function to data frame using only basic types (i.e., string and numeric
        data types).


    .. versionchanged:: 0.3.2
        Handle sources with no allowed capabilities.
    '''
    pipeline = Gst.Pipeline()

    video_source = Gst.element_factory_make(VIDEO_SOURCE_PLUGIN, 'video_source')
    video_source.set_property(DEVICE_KEY, device_name)

    source_pad = video_source.get_pad('src')
    video_sink = Gst.element_factory_make('autovideosink', 'video_sink')
    pipeline.add(video_source)
    pipeline.add(video_sink)
    try:
        video_source.link(video_sink)
        pipeline.set_state(Gst.STATE_READY)
        allowed_caps = [dict([(k, c[k]) for k in c.keys()] + [('name',
                                                               c.get_name())])
                        for c in source_pad.get_allowed_caps()]
        pipeline.set_state(Gst.STATE_NULL)
    except Gst.LinkError:
        logging.debug('Unable to link to %s to get capabilities', device_name)
        allowed_caps = []
    finally:
        del pipeline

    return pd.DataFrame(allowed_caps)


def extract_dimensions(dimensions_obj):
    '''
    Parameters
    ----------
    dimensions_obj : pandas.Series
        Width and height.

    Returns
    -------
    pandas.Series
        Replace width/height values in :class:`Gst.IntRange` form with maximum
        value in range.
    '''
    for field in ['width', 'height']:
        if isinstance(dimensions_obj[field], Gst.IntRange):
            dimensions_obj[field] = dimensions_obj[field].high
    return [dimensions_obj['width'], dimensions_obj['height']]


def extract_format(format_obj):
    '''
    Parameters
    ----------
    format_obj : Gst.Fourcc
        Four CC video format code.

        See `list of FOURCC codes <https://www.fourcc.org/codecs.php>`.

    Returns
    -------
    str
        Four CC code as four character string.
    '''
    return format_obj.fourcc


def extract_fps(framerate_obj):
    '''
    Parameters
    ----------
    framerate_obj : Gst.Fraction, Gst.FractionRange
        Either a single GStreamer frame rate fraction, or a range of fractions.

    Returns
    -------
    list
        One fractional frames-per-second tuple
        (i.e., ``(numerator, denominator``) for each frame rate fraction
        (multiple if :data:`framerate_obj` is a :class:`Gst.FractionRange`).
    '''
    framerates = []
    try:
        for fps in framerate_obj:
            framerates.append((fps.num, fps.denom))
    except TypeError:
        if isinstance(framerate_obj, Gst.FractionRange):
            for fps in (framerate_obj.low,
                        framerate_obj.high):
                framerates.append((fps.num, fps.denom))
        else:
            fps = framerate_obj
            framerates.append((fps.num, fps.denom))
    return sorted(set(framerates))


def expand_allowed_capabilities(df_allowed_caps):
    '''
    Convert GStreamer data types to basic Python types.

    For example, `format` in `df_allowed_caps` is of type `Gst.Fourcc`, but can
    simply be converted to a string of four characters.

    Parameters
    ----------
    df_allowed_caps : pandas.DataFrame
        Video capabilities configurations in form returned by
        :func:`get_allowed_capabilities`.

    Returns
    -------
    pandas.DataFrame
        One row per video configuration containing only basic string or numeric
        data types.  Also, lists of frame rates in :data:`df_allowed_caps` are
        expanded to multiple rows.
    '''
    df_modes = df_allowed_caps.copy().drop(['framerate', 'width', 'height',
                                            'format'], axis=1)
    df_modes['fourcc'] = df_allowed_caps.format.map(lambda v:
                                                    extract_format(v))
    df_dimensions = (df_allowed_caps[['width', 'height']]
                     .apply(lambda v: extract_dimensions(v), axis=1))
    df_modes.insert(0, 'width', df_dimensions.width)
    df_modes.insert(1, 'height', df_dimensions.height)

    # From GStreamer, framerates are encoded as either a ratio or a list of
    # ratios.
    # The `expand_fps` function normalizes the framerate entry for each row to
    # be a *`list`* of GStreamer ratios.
    frame_rates = df_allowed_caps.framerate.map(lambda v: extract_fps(v))

    # Expand the list of ratios for each row into one row per ratio, and
    # replace `framerate` column with *numerator* (`framerate_num`) and
    # *denominator* (`framerate_denom`).
    frames = []

    for (i, mode_i), framerates_i in zip(df_modes.iterrows(), frame_rates):
        frame_i = [mode_i.tolist() + list(fps_j) for fps_j in framerates_i]
        frames.extend(frame_i)
    df_modes = pd.DataFrame(frames, columns=df_modes.columns.tolist() +
                            ['framerate_num', 'framerate_denom'])
    # Compute framerate as float for convenience (ratio form is required for
    # setting GStreamer capabilities when creating a pipeline).
    df_modes['framerate'] = (df_modes['framerate_num'] /
                             df_modes['framerate_denom'])
    return df_modes


def get_source_capabilities(video_source_names=None):
    '''
    Parameters
    ----------
    video_source_names : list
        List of video source names.  See :func:`get_video_source_names`
        function to query available device names.

    Returns
    -------
    pandas.DataFrame
        One row per available video source configuration.


    .. versionchanged:: 0.3.2
        Handle no sources available and sources with no allowed capabilities.
    '''
    if video_source_names is None:
        video_source_names = get_video_source_names()

    frames = []

    for device_name_i in video_source_names:
        df_allowed_caps_i = get_allowed_capabilities(device_name_i)
        if not df_allowed_caps_i.shape[0]:
            # No allowed caps for the device
            continue
        df_source_caps_i = expand_allowed_capabilities(df_allowed_caps_i)
        df_source_caps_i.insert(0, 'device_name', device_name_i)
        frames.append(df_source_caps_i)
    if frames:
        return pd.concat(frames).reset_index(drop=True)
    else:
        return pd.DataFrame()
