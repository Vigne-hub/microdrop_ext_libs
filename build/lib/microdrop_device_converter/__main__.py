# coding: utf-8
import sys
import logging

from path_helpers import path

from . import convert_device_to_svg


def main():
    args = parse_args()
    convert_device_to_svg(args.input_device_path, args.output_device_path,
                          use_svg_path=args.path,
                          detect_connections=args.detect_connections,
                          extend_mm=args.extend_mm, overwrite=args.overwrite)

def parse_args(args=None):
    """Parses arguments, returns (options, args)."""
    from argparse import ArgumentParser

    if args is None:
        args = sys.argv

    parser = ArgumentParser(description='Microdrop device converter to convert'
                            ' device versions <=0.3.0 to SVG format.')
    parser.add_argument('input_device_path', type=path)
    parser.add_argument('output_device_path', type=path)
    parser.add_argument('-f', '--overwrite', action='store_true')
    parser.add_argument('-e', '--extend-mm', type=float, default=.5)
    parser.add_argument('-c', '--detect-connections', action='store_true')
    parser.add_argument('-p', '--path', action='store_true',
                        help='Draw `svg:path` elements instead of '
                        '`svg:polygon` elements.')

    args = parser.parse_args()
    if args.output_device_path.ext.lower() != '.svg':
        parser.error('Output path extension must be ".svg".')
    elif args.input_device_path.ext.lower() != '':
        parser.error('Input path must have no extension.')

    if args.output_device_path.isfile() and not args.overwrite:
        parser.error('Output path already exists.  Use `-f` to force '
                     'overwrite.')
    return args


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    main()
