#!/usr/bin/env python
# Python 3.7

"""
The USGS provides bulk metadata for their Landsat products.

However, the files are presented in two options: csv or xml, and both multiple
gigabytes in size (when extracted).

This project aims to parse the csv version of the metadata, and output a list of
the scene IDs necessary to download the desired scenes.
"""

import argparse
import errno
import os
from argparse import Namespace
from pathlib import Path
from pprint import pprint


def parse_args() -> Namespace:
    parser = argparse.ArgumentParser(
        description='Parse and filter Landsat metadata CSV file'
    )
    parser.add_argument(
        '-f', '--filename',
        type=Path,
        action='store',
        required=True,
        help='(Required) filename of the CSV file'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        action='store',
        required=False,
        help='(Optional) filename of output text file'
    )
    parser.add_argument(
        '-sd', '--start-date',
        type=str,
        action='store',
        required=False,
        help='(Optional) starting/minimum date (YYYY-MM-DD) of the desired scenes'
    )
    parser.add_argument(
        '-ed', '--end-date',
        type=str,
        action='store',
        required=False,
        help='(Optional) ending/maximum date (YYYY-MM-DD) of the desired scenes'
    )
    parser.add_argument(
        '-c', '--cloud-cover',
        type=int,
        action='store',
        required=False,
        help=('(Optional) maximum percentage of cloud cover\n\n'
              'e.g. "-c 80" means that cloud coverage greater than'
              '80 percent will be discarded'
              )
    )
    parser.add_argument(
        '-g', '--grid',
        type=str,
        action='store',
        required=False,
        help=('(Optional) ARD tile grid horizontal and vertical value\n'
              'e.g. \'-g 3,12\' is the grid with a hor. 3 and vert. 12\n'
              'Note: most useful when specifying -r/--region below too'
              )
    )
    parser.add_argument(
        '-r', '--region',
        type=str,
        action='store',
        required=False,
        help=('(Optional) region, one of CU/AK/HI for the Continental US,\n'
              'Alaska, or Hawaii, respectively.'
              )
    )
    args = parser.parse_args()
    if not args.output:
        args.output = Path('./scene_ids.txt')
    return args


def _paths_good(input_path: Path, output_path: Path) -> bool:
    """
    Check appropriate conditions for paths, raising necessary errors

    :param input_path: Path
    :param output_path: Path
    :return: None
    """
    if not input_path.exists():
        raise FileNotFoundError(errno.ENOENT,
                                os.strerror(errno.ENOENT),
                                input_path.as_posix())
    if input_path == output_path:
        raise ValueError('Input and output must be different!')
    if not output_path.is_file():
        raise OSError(f'Output must be a filename')
    if output_path.exists():
        print(f'File \'{output_path.as_posix()}\' exists!')
        do_del = input('Delete/overwrite? [y/N] ')
        if do_del == 'y':
            output_path.unlink()
        else:
            print('Not continuing.')
            return False
    return True


def parse_csv(args: Namespace) -> None:
    """
    Parse the given CSV file, filtering as necessary, and write out the scenes

    :param args: Namespace
    :return: None
    """
    input_file: Path = args.filename
    output_file: Path = args.output
    # Quick file tests
    if not _paths_good(input_file, output_file):
        return



def main() -> None:
    args: Namespace = parse_args()
    print(type(args))
    pprint(args)
    parse_csv(args)


if __name__ == '__main__':
    main()
