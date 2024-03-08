"""

This file is part of Microdrop.

Microdrop is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Microdrop is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Microdrop.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
try:
    import cPickle as pickle
except ImportError:
    import pickle
import logging

from microdrop_utility import Version, FutureVersionError
import numpy as np
import pandas as pd
from path_helpers import path
from svg_model import INKSCAPE_PPmm
from svg_model.detect_connections import auto_detect_adjacent_shapes
from svg_model.draw import draw_shapes_svg_layer
from svg_model.geo_path import Path, ColoredPath, Loop
from svg_model.merge import merge_svg_layers
from svg_model.path_group import PathGroup
from svg_model.svgload.path_parser import LoopTracer, ParseError
import yaml

logger = logging.getLogger(__name__)

# Add support for serialized device files where parent module is ``dmf_device``
# rather than the fully-qualified ``microdrop.dmf_device``.  This is done by
# adding the root of the ``microdrop_device_converter`` package to the Python
# path.
microdrop_root = path(__file__).parent.abspath()
if microdrop_root not in sys.path:
    sys.path.insert(0, microdrop_root)


class DeviceScaleNotSet(Exception):
    pass


class DmfDevice():
    class_version = str(Version(0, 3, 0))
    def __init__(self):
        self.electrodes = {}
        self.x_min = np.Inf
        self.x_max = 0
        self.y_min = np.Inf
        self.y_max = 0
        self.name = None
        self.scale = None
        self.path_group = None  # svg_model.path_group.PathGroup
        self.version = self.class_version
        self.electrode_name_map = {}
        self.name_electrode_map = {}

    @classmethod
    def load(cls, filename):
        """
        Load a DmfDevice from a file.

        Args:

            filename (str) : Path to file.

        Raises:

            TypeError : File is not a DmfDevice.
            FutureVersionError : File was written by a future version of the
                software.
        """
        logger.debug("[DmfDevice].load(\"%s\")" % filename)
        logger.info("Loading DmfDevice from %s" % filename)
        out = None

        # Assume file contains `pickle`-serialized device.
        with open(filename, 'rb') as f:
            try:
                out = pickle.load(f)
                logger.debug("Loaded object from pickle.")
            except Exception as e:
                logger.debug("Not a valid pickle file. %s." % e)

        # Assume file contains `pickle`-serialized device, but using
        # `microdrop.dmf_device` module.
        if out is None:
            device_data = path(filename).bytes()
            device_data = device_data.replace('microdrop.dmf_device',
                                              'microdrop_device_converter'
                                              '.dmf_device')
            try:
                out = pickle.loads(device_data)
                logger.debug('Loaded object from pickle.')
            except Exception as e:
                logger.debug('Not a valid pickle file.', exc_info=True)

        # Assume file contains `yaml`-serialized device.
        if out is None:
            with open(filename, 'rb') as f:
                try:
                    out = yaml.load(f)
                    logger.debug("Loaded object from YAML file.")
                except Exception as e:
                    logger.debug("Not a valid YAML file. %s." % e)

        if out is None:
            # File does not contain any supported serialized device format.
            raise TypeError
        if not hasattr(out, 'version'):
            out.version = '0'
        out._upgrade()
        return out

    def _upgrade(self):
        """
        Upgrade the serialized object if necessary.

        Raises:
            FutureVersionError: file was written by a future version of the
                software.
        """
        logger.debug("[DmfDevice]._upgrade()")
        version = Version.fromstring(self.version)
        logger.debug('[DmfDevice] version=%s, class_version=%s' % (str(version), self.class_version))
        if version > Version.fromstring(self.class_version):
            logger.debug('[DmfDevice] version>class_version')
            raise FutureVersionError
        elif version < Version.fromstring(self.class_version):
            if version < Version(0,1):
                self.version = str(Version(0,1))
                self.scale = None
                logger.info('[DmfDevice] upgrade to version %s' % self.version)
            if version < Version(0,2):
                self.version = str(Version(0,2))
                for id, e in self.electrodes.items():
                    if hasattr(e, "state"):
                        del self.electrodes[id].state
                logger.info('[DmfDevice] upgrade to version %s' % self.version)
            if version < Version(0,3):
                # Upgrade to use pymunk
                self.version = str(Version(0,3))

                x_min = min([e.x_min for e in self.electrodes.values()])
                x_max = max([e.x_max for e in self.electrodes.values()])
                y_min = min([e.y_min for e in self.electrodes.values()])
                y_max = max([e.y_max for e in self.electrodes.values()])

                boundary = Path([Loop([(x_min, y_min), (x_min, y_max),
                                       (x_max, y_max), (x_max, y_min)])])

                traced_paths = {}
                tracer = LoopTracer()
                for id, e in self.electrodes.items():
                    try:
                        path_tuples = []
                        for command in e.path:
                            keys_ok = True
                            for k in ['command', 'x', 'y']:
                                if k not in command:
                                    # Missing a parameter, skip
                                    keys_ok = False
                            if not keys_ok:
                                continue
                            path_tuples.append(
                                (command['command'], float(command['x']),
                                float(command['y'])))
                        path_tuples.append(('Z',))
                        loops = tracer.to_loops(path_tuples)
                        p = ColoredPath(loops)
                        p.color = (0, 0, 255)
                        traced_paths[str(id)] = p
                    except ParseError:
                        pass
                    except KeyError:
                        pass
                path_group = PathGroup(traced_paths, boundary)
                electrodes = self.electrodes
                self.electrodes = {}
                self.add_path_group(path_group)

                for id, e in electrodes.items():
                    if str(id) in self.name_electrode_map:
                        eid = self.name_electrode_map[str(id)]
                        self.electrodes[eid].channels = e.channels
                del electrodes
                logger.info('[DmfDevice] upgrade to version %s' % self.version)
        # else the versions are equal and don't need to be upgraded

    def to_frame(self):
        '''
        Returns
        -------
        pandas.DataFrame
            Frame with one row per electrode vertex, including vertex
            ``x``/``y`` coordinate and SVG electrode attributes (e.g.,
            ``"id"``, ``"style"``).
        '''
        vertices = []

        for i, e in self.electrodes.items():
            shape_id = 'electrode%03d' % i
            style = 'fill: rgb(%d,%d,%d)' % tuple(e.path.color)
            channels = ','.join(map(str, e.channels))
            shape_attrs_i = [shape_id, style, channels]

            vertices_i = [shape_attrs_i + [j] + [x, y]
                          for j, (x, y) in enumerate(e.path.loops[0].verts)]
            vertices.extend(vertices_i)

        if not vertices:
            vertices = None
        return pd.DataFrame(vertices, columns=['id', 'style', 'data-channels',
                                               'vertex_i', 'x', 'y'])

    def to_svg(self, use_svg_path=True, detect_connections=True, extend=.5):
        '''
        Args:

            use_svg_path (bool, optional) : If ``True``, electrodes are drawn
                as ``svg:path`` elements.  Otherwise, electrodes are drawn as
                ``svg:polygon`` elements.
            detect_connections (bool, optional) : If ``True``, add
                ``"Connections"`` layer to SVG by attempting to automatically
                detect adjacent electrodes.
            extend (float, optional) : The number of millimeters to extend
                electrode boundaries from the electrode center to find
                overlapping *adjacent* electrodes.

        Returns
        -------
        str
            SVG XML source with ``"Device"`` layer containing electrodes drawn
            as ``svg:path`` elements, and an optional ``"Connections"`` layer
            containing ``svg:line`` elements denoting *adjacent* electrodes
            (i.e., electrodes that a drop may transition between directly). '''
        df_shapes = self.to_frame()
        minx, miny = df_shapes[['x', 'y']].min().values

        df_shapes[['x', 'y']] -= minx, miny
        df_shapes[['x', 'y']] /= INKSCAPE_PPmm.magnitude

        shapes_svg = draw_shapes_svg_layer(df_shapes, 'id', 'Device',
                                           layer_number=1,
                                           use_svg_path=use_svg_path)
        if detect_connections:
            connections_svg = auto_detect_adjacent_shapes(shapes_svg, 'id',
                                                          extend=extend)
            shapes_svg = merge_svg_layers([shapes_svg, connections_svg])

        return shapes_svg.getvalue()


class Electrode:
    next_id = 0
    def __init__(self, path):
        self.id = Electrode.next_id
        Electrode.next_id += 1
        self.path = path
        self.channels = []

    def area(self):
        return self.path.get_area()
