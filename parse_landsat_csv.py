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
from datetime import datetime
from pathlib import Path
from typing import Any, List

import pandas as pd  # type: ignore

# The type Any is only used because pandas doesn't currently have full typing
# support. There are technically efforts to do so, especially on user-facing
# interfaces such as dataframes, but the effort is still ongoing.
# A stop-gap is used below.

# Global constants
# These probably *could* be programmatically determined from some sort of fuzzy
# matching, but also it's unlikely that the USGS is going to change the file
# format anytime soon.
# The main danger here is that any slight change in either how USGS names the
# columns, or how pandas processes the header strings, will basically break it.
DATE_COLS: List[str] = [
    'Tile_Production_Date',
    'acquisitionDate',
    'dateUpdated'
]
USE_COLS: List[str] = [
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

# Common types
Filter = List[bool]
DataFrame = Any  # Until pandas is ready


def _str_to_datetime(date: str) -> datetime:
    """
    Convert string of Y-M-D into proper datetime object

    :param date: str
    :return: datetime
    """
    if isinstance(date, datetime):
        return date
    elif isinstance(date, str):
        try:
            return datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return datetime.strptime(date, '%Y/%m/%d')
    raise ValueError(f'Cannot parse \'{date}\'')


def parse_args() -> Namespace:
    """
    Parse CLI arguments

    :return: Namespace  # of argparse
    """
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
        default=Path('./scene_ids.txt'),
        help='filename of output text file'
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='automatically overwrite output file'
    )
    parser.add_argument(
        '-sd', '--start-date',
        type=_str_to_datetime,
        action='store',
        required=False,
        help='starting/minimum date (YYYY-MM-DD) of the desired scenes'
    )
    parser.add_argument(
        '-ed', '--end-date',
        type=_str_to_datetime,
        action='store',
        required=False,
        help='ending/maximum date (YYYY-MM-DD) of the desired scenes'
    )
    parser.add_argument(
        '-c', '--cloud-cover',
        type=int,
        action='store',
        required=False,
        help=('maximum percentage of cloud cover'
              'e.g. "-c 80" means that cloud coverage greater than'
              '80 percent will be discarded'
              )
    )
    parser.add_argument(
        '-g', '--grid',
        type=str,
        action='store',
        required=False,
        help=('ARD tile grid horizontal and vertical value'
              'e.g. \'-g 3,12\' is the grid with a hor. 3 and vert. 12'
              'Note: most useful when specifying -r/--region below too'
              )
    )
    parser.add_argument(
        '-r', '--region',
        type=str,
        action='store',
        required=False,
        help=('region, one of CU/AK/HI for the Continental US,'
              'Alaska, or Hawaii, respectively.'
              )
    )
    parser.add_argument(
        '-s', '--sensor',
        type=str,
        action='store',
        required=False,
        help=('sensor type. Comma-separated values of:'
              'OLI/TIRS, TM, or ETM.'
              'e.g. \'-s OLI/TIRS\' will only return entries that used only'
              'the OLI/TIRS sensor (i.e., Landsat 8)'
              )
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show verbose file loading messages.'
    )
    # TODO: Add info option that won't filter the data, just show a summary.
    args: Namespace = parser.parse_args()
    return args


def __overwrite_file(output_path: Path, overwrite: bool) -> bool:
    """
    If not automatically overwriting, ask the user if they want to continue

    Either delete the file and continue, or return that choice.

    :param output_path: Path
    :param overwrite: bool
    :return: bool
    """
    if not overwrite:
        print(f'File \'{output_path.as_posix()}\' exists!')
        do_del = input('Delete/overwrite? [y/N] ')
        if do_del == 'y':
            output_path.unlink()
            output_path.touch()
        else:
            print('Not continuing.')
            return False
    else:
        output_path.unlink()
        output_path.touch()
    return True


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
    if output_path.exists():
        cont: bool = __overwrite_file(output_path, overwrite)
        if not cont:
            return cont
    else:
        output_path.touch()
    if not output_path.is_file():
        raise OSError(f'Output must be a filename')
    return True


def __start_date(input_csv: DataFrame, date: datetime) -> Filter:
    """
    Remove dates earlier than a given time

    :param input_csv: DataFrame  # until pandas supports typing
    :param date: datetime
    :return: Filter
    """
    to_keep: Filter
    if date:
        print(f'Removing entries before {date}')
        to_keep = input_csv['acquisitionDate'] >= date
    else:
        to_keep = [True] * input_csv.shape[0]
    return to_keep


def __end_date(input_csv: DataFrame, date: datetime) -> Filter:
    """
    Remove dates later than the given date

    :param input_csv: DataFrame
    :param date: datetime
    :return: Filter
    """
    to_keep: Filter
    if date:
        print(f'Removing entries after {date}')
        to_keep = input_csv['acquisitionDate'] <= date
    else:
        to_keep = [True] * input_csv.shape[0]
    return to_keep


def __cloud_cover(input_csv: DataFrame, cloud_cover: int) -> Filter:
    """
    Remove entries whose cloud cover is greater than the given percentage

    :param input_csv: DataFrame
    :param cloud_cover: int
    :return: Filter
    """
    to_keep: Filter
    if cloud_cover:
        print(f'Removing entries with more than {cloud_cover}% CC')
        to_keep = input_csv['cloudCover'] <= cloud_cover
    else:
        to_keep = [True] * input_csv.shape[0]
    return to_keep


def __grid(input_csv: DataFrame, grid: str) -> Filter:
    """
    Remove entries whose grid values are anything but the supplied hor/vert

    :param input_csv: DataFrame
    :param grid: str
    :return: Filter
    """
    to_keep: Filter = [True] * input_csv.shape[0]
    if grid:
        print(f'Filtering on grid values {grid}')
        # Parse grid value
        h, v = grid.split(',')
        # Filter one at a time
        try:
            hi: int = int(h)
            print(f'Horizontal: {h}')
            to_keep = [all(t) for t in
                       zip(to_keep, input_csv['Tile_Grid_Horizontal'] == hi)]
        except ValueError:
            pass
        try:
            vi: int = int(v)
            print(f'Vertical: {v}')
            to_keep = [all(t) for t in
                       zip(to_keep, input_csv['Tile_Grid_Vertical'] == vi)]
        except ValueError:
            pass
    return to_keep


def __region(input_csv: DataFrame, region: str) -> Filter:
    """
    Remove entries that aren't the given region

    :param input_csv: DataFrame
    :param region: str
    :return: Filter
    """
    to_keep: Filter
    if region:
        print(f'Filtering on region {region}')
        to_keep = input_csv['Tile_Grid_Region'] == region
    else:
        to_keep = [True] * input_csv.shape[0]
    return to_keep


def __sensor(input_csv: DataFrame, sensor: str) -> Filter:
    """
    Remove entries that don't use the given sensor(s)

    :param input_csv: DataFrame
    :param sensor: str
    :return: Filter
    """
    to_keep: Filter = [True] * input_csv.shape[0]
    if sensor:
        print(f'Filtering on sensor(s) {sensor}')
        sensors: List[str] = sensor.split(',')
        for sen in sensors:
            to_keep = [all(t) for t in zip(to_keep, input_csv['sensor'] == sen)]
    return to_keep


def _filter_csv(input_csv: DataFrame, args: Namespace) -> DataFrame:
    """
    Remove entries based on supplied arguments

    args should come from parse_args() and have the following methods:
        start_date
        end_date
        cloud_cover
        grid
        region
        sensor

    :param input_csv: DataFrame
    :param args: Namespace
    :return: DataFrame  # The filtered input_csv
    """
    print(f'Filtering on {input_csv.shape[0]} entries')
    to_keep: Filter = [all(t) for t in
                       zip(__start_date(input_csv, args.start_date),
                           __end_date(input_csv, args.end_date),
                           __cloud_cover(input_csv, args.cloud_cover),
                           __grid(input_csv, args.grid),
                           __region(input_csv, args.region),
                           __sensor(input_csv, args.sensor))]
    print(f'Keeping {sum(to_keep)} entries')
    return input_csv[to_keep]


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
    input_csv: DataFrame = pd.read_csv(input_file,
                                       # nrows=10000,  # 10,000 for testing
                                       parse_dates=DATE_COLS,
                                       date_parser=_str_to_datetime,
                                       usecols=USE_COLS,
                                       verbose=args.verbose
                                       )
    # Start filtering
    if any([args.start_date,
            args.end_date,
            args.cloud_cover,
            args.grid,
            args.region,
            args.sensor]):
        input_csv = _filter_csv(input_csv, args)
    # Now write out the scene IDs
    with output_file.open(mode='w') as out:
        print(f'Writing scenes to {output_file.as_posix()}')
        out.write('\n'.join(input_csv['Entity_ID']))
        print('Done writing')


def main() -> None:
    args: Namespace = parse_args()
    parse_csv(args)


if __name__ == '__main__':
    main()
