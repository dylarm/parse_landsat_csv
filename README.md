# Parse Bulk Landsat Metadata
This project is inspired by [parse_landsat_xml](https://github.com/and-viceversa/parse_landsat_xml), but provides a CLI interface to process the csv metadata file.

**Table of Contents**
- [Description](#description)
- [Usage](#usage)
  - [Simple Example](#simple-example)
  - [Flags](#flags)
  - [More Examples](#more-examples)

---

## Description
The US Geological Survey provides [single files](https://www.usgs.gov/land-resources/nli/landsat/bulk-metadata-service) that contain all of the metadata regarding Landsat scenes.
Unfortunately, this is a file that, when uncompressed, is several gigabytes in size.

The separate project [parse_landsat_xml](https://github.com/and-viceversa/parse_landsat_xml) by Github user *and-viceversa* already provides a method of parsing the xml file.

This project deals with csv file instead, focusing primarily on the Analysis Ready Data (ARD) scenes.
It takes in the decrompressed csv, optionally filtering out certain scenes, and then writes out a txt file of the entity IDs.

A separate tool will be needed to actually download the scenes.
I may or may not be working on one, or just incorporating it into this project.
But you can likely use the `usgs` python module to do so.

---

## Usage
##### Simple Example
Just output all entity IDs, no filtering.
```bash
foo@bar:~$ python parse_landsat_csv.py -f ARD_TILE.csv

ARD_TILE.csv -> scene_ids.txt
Writing scenes to scene_ids.txt
Done writing

foo@bar:~$
```

##### Flags
Every flag except `-f` is optional, and all can be used independently of each other.

| Flag               | Arg         | Description                                                        |
|--------------------|-------------|--------------------------------------------------------------------|
|`-f`                | FILENAME    | Path to the input CSV file                                         |
|`-o`                | OUTPUT      | Path to output txt file                                            |
|`--overwrite`       |             | Auto-overwrite output file                                         |
|`-sd`/`--start-date`| START_DATE  | Earliest desired date, YYYY-MM-DD                                  |
|`-ed`/`--end-date`  | END_DATE    | Lateset desired date, YYYY-MM-DD                                   |
|`-c`/`--cloud-cover`| CLOUD_COVER | Maximum allowable cloud cover                                      |
|`-g`/`--grid`       | GRID        | Comma-separated horizontal & vertical ARD Tile Grid                |
|`-r`/`--region`     | REGION      | ARD region, either CU, AK, or HI                                   |
|`-s`/`--sensor`     | SENSOR      | Landsat sensor used\*, one or more of OLI/TIRS, ETM, or TM           |
|`-v`/`--verbose`    |             | Increase verbosity (show `pandas` progress loading the input file) |
\* Currently not working correctly, will not return any scenes.

##### More Examples
Specify output file:
```bash
foo@bar:~$ python parse_landsat_csv.py -f ARD_TILE.csv -o ../../all_tiles.txt

ARD_TILE.csv -> ../../all_tiles.txt
Writing scenes to all_tiles.txt
Done writing
```

Only return the last three years of scenes (today: 11-July-2019):
```bash
foo@bar:~$ python parse_landsat_csv.py -f ARD_TILE.csv -sd 2016-07-11

ARD_TILE.csv -> scene_ids.txt
Filtering on 1515075 entries
Removing entries before 2016-07-11 00:00:00
Keeping 217648 entries
Writing scenes to scene_ids.txt
Done writing
```

Only show dates before 2001:
```bash
foo@bar:~$ python parse_landsat_csv.py -f ARD_TILE.csv -ed 2000-12-31

ARD_TILE.csv -> scene_ids.txt
Filtering on 1515075 entries
Removing entries after 2000-12-31 00:00:00
Keeping 406336 entries
Writing scenes to scene_ids.txt
Done writing
```

Cloud cover under 80%:
```bash
foo@bar:~$ python parse_landsat_csv.py -f ARD_TILE.csv -c 80

ARD_TILE.csv -> scene_ids.txt
Filtering on 1515075 entries
Removing entries with more than 80% CC
Keeping 1166115 entries
Writing scenes to scene_ids.txt
Done writing
```

ARD Tile Grid horizontal 3, vertical 10 in Alaska for the year 2017:
```bash
foo@bar:~$ python parse_landsat_csv.py -f ARD_TILE.csv -g 3,10 -r AK -sd 2017-01-01 -ed 2017-12-31

ARD_TILE.csv -> scene_ids.txt
Filtering on 1515075 entries
Removing entries before 2017-01-01 00:00:00
Removing entries after 2017-12-31 00:00:00
Filtering on grid values 3,10
Horizontal: 3
Vertical: 10
Filtering on region AK
Keeping 115 entries
Writing scenes to scene_ids.txt
Done writing
```

~~Return only OLI/TIRS or ETM data:~~ (Currently broken)
```bash
foo@bar:~$ python parse_landsat_csv.py -f ARD_TILE.csv -s OLI/TIRS,ETM

ARD_TILE.csv -> scene_ids.txt
Filtering on 1515075 entries
```

Output file already exists:
```bash
foo@bar:~$ python parse_landsat_csv.py -f ARD_TILE.csv

File 'scene_ids.txt' exists!
Delete/overwrite? [y/N] n
Not continuing.
```
