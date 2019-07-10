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
import pandas as pd
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from pprint import pprint
from typing import List


DATE_COLS: List[str] = [
    'Tile_Production_Date',
    'acquisitionDate',
    'dateUpdated'
]


def _str_to_datetime(date: str)-> datetime:
    if isinstance(date, datetime):
        return date
    elif isinstance(date, str):
        try:
            return datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return datetime.strptime(date, '%Y/%m/%d')
    raise ValueError(f'Cannot parse \'{date}\'')


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
        '--overwrite',
        action='store_true',
        help='(Optional) automatically overwrite output file'
    )
    parser.add_argument(
        '-sd', '--start-date',
        type=_str_to_datetime,
        action='store',
        required=False,
        help='(Optional) starting/minimum date (YYYY-MM-DD) of the desired scenes'
    )
    parser.add_argument(
        '-ed', '--end-date',
        type=_str_to_datetime,
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


def _paths_good(input_path: Path, output_path: Path, overwrite: bool) -> bool:
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
    if output_path.exists() and not overwrite:
        print(f'File \'{output_path.as_posix()}\' exists!')
        do_del = input('Delete/overwrite? [y/N] ')
        if do_del == 'y':
            output_path.unlink()
            output_path.touch()
        else:
            print('Not continuing.')
            return False
    elif output_path.exists() and overwrite:
        output_path.unlink()
        output_path.touch()
    elif not output_path.exists():
        output_path.touch()
    if not output_path.is_file():
        raise OSError(f'Output must be a filename')
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
    if not _paths_good(input_file, output_file, args.overwrite):
        return
    # Read file and begin parsing
    input_csv = pd.read_csv(input_file,
                            nrows=5,  # 5 for testing
                            parse_dates=DATE_COLS,
                            date_parser=_str_to_datetime
                            )


def main() -> None:
    args: Namespace = parse_args()
    print(type(args))
    pprint(args)
    parse_csv(args)


if __name__ == '__main__':
    main()
