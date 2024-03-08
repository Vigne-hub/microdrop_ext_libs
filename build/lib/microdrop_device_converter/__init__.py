import logging

from path_helpers import path

from .dmf_device import DmfDevice

logger = logging.getLogger(__name__)


def convert_device_to_svg(input_device_path, output_device_path,
                          use_svg_path=True, detect_connections=True,
                          extend_mm=.5, overwrite=False):
    '''
    Convert a Microdrop device v0.3.0 to SVG format.

    Args:

        input_device_path (str) : Input device file path
        output_device_path (str) : Output SVG device file path
        use_svg_path (bool, optional) : If ``True``, electrodes are drawn as
            ``svg:path`` elements.  Otherwise, electrodes are drawn as
            ``svg:polygon`` elements.
        detect_connections (bool, optional) : If ``True``, automatically detect
            connections between adjacent shapes and add a layer name
            ``"Connections"`` to the output SVG file.
        extend_mm (float, optional) : If ``detect_connections=True``, the
            distance each electrode is extended out from each boundary to
            detect adjacent electrodes.
        overwrite (bool, optional) : If ``True``, overwrite existing file.

    Returns:

        None
    '''
    input_device_path = path(input_device_path)
    output_device_path = path(output_device_path)

    if output_device_path.isfile() and not overwrite:
        raise IOError('Output path already exists.  Use `-f` to force '
                      'overwrite.')

    device = DmfDevice.load(input_device_path)
    logging.info('read input device from: %s' % input_device_path.abspath())

    with open(output_device_path, 'wb') as output:
        output.write(device.to_svg(use_svg_path=use_svg_path,
                                   detect_connections=detect_connections,
                                   extend=extend_mm))
    logging.info('wrote output device to: %s' % output_device_path.abspath())