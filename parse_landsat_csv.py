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
USE_COLS :List[str] = [
    *DATE_COLS,
    'Entity_ID',
    'Fill',
    'Tile_Grid_Horizontal',
    'Tile_Grid_Region',
    'Tile_Grid_Vertical',
    'Tile_Identifier',
    'cloudCover',
    'sensor'
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
    parser.add_argument(
        '-s', '--sensor',
        type=str,
        action='store',
        required=False,
        help=('(Optional) sensor type. Comma-separated values of:\n'
              'OLI/TIRS or ETM\n'
              'e.g. \'-s OLI/TIRS\' will only return entries that used only'
              'the OLI/TIRS sensor (i.e., Landsat 8)'
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
    print(f'{input_file.as_posix()} -> {output_file.as_posix()}')
    input_csv = pd.read_csv(input_file,
                            nrows=10000,  # 10,000 for testing
                            parse_dates=DATE_COLS,
                            date_parser=_str_to_datetime,
                            usecols=USE_COLS,
                            verbose=True
                            )
    # Start filtering
    if any([args.start_date,
            args.end_date,
            args.cloud_cover,
            args.grid,
            args.region,
            args.sensor]):
        # List of bools of rows to keep
        nrows: int = input_csv.shape[0]
        to_keep = [True] * nrows  # Start with all of them
        print(f'Filtering on {nrows} entries')
        if args.start_date:
            print(f'Removing entries before {args.start_date}')
            to_keep = [
                all(t) for t in
                zip(to_keep, input_csv['acquisitionDate']>=args.start_date)
            ]
        if args.end_date:
            print(f'Removing entries after {args.end_date}')
            to_keep = [
                all(t) for t in
                zip(to_keep, input_csv['acquisitionDate']<=args.end_date)
            ]
        if args.cloud_cover:
            print(f'Removing entries with more than {args.cloud_cover}% CC')
            to_keep = [
                all(t) for t in
                zip(to_keep, input_csv['cloudCover']<=args.cloud_cover)
            ]
        if args.grid:
            print(f'Filtering on grid values {args.grid}')
            # Parse grid value
            h,v = args.grid.split(',')
            # Filter one at a time
            try:
                h = int(h)
                print(f'Horizontal: {h}')
                to_keep = [
                    all(t) for t in
                    zip(to_keep, input_csv['Tile_Grid_Horizontal']==h)
                ]
            except ValueError:
                pass
            try:
                v = int(v)
                print(f'Vertical: {v}')
                to_keep = [
                    all(t) for t in
                    zip(to_keep, input_csv['Tile_Grid_Vertical']==v)
                ]
            except ValueError:
                pass
        if args.region:
            print(f'Filtering on region {args.region}')
            to_keep = [
                all(t) for t in
                zip(to_keep, input_csv['Tile_Grid_Region']==args.region)
            ]
        if args.sensor:
            print(f'Filtering on sensor(s) {args.sensor}')
            sensors: List[str] = args.sensor.split(',')
            to_keep = [
                all(t) for t in
                zip(to_keep, input_csv['sensor'] in sensors)
            ]
        # TODO: Actually filter the results
    # Now write out the scene IDs


def main() -> None:
    args: Namespace = parse_args()
    parse_csv(args)


if __name__ == '__main__':
    main()
