import csv
from pathlib import Path
import numpy as np
import pandas as pd
import datetime
import kremboxer.dualband.dualband_utils as kddu


def read_dualband_dataset(file: Path, csvreader, first_row):
    header_titles = first_row
    header_values = next(csvreader, None)
    header_dict = kddu.construct_dualband_header_dict(header_titles, header_values)
    data_columns = next(csvreader, None)

    data_dict = {}
    for data_column in data_columns:
        data_dict[data_column] = []
    data_dict["DATETIME"] = []

    sample = 0
    sample_time: datetime.datetime = header_dict["DATETIME_START"]
    return_row = None
    while True:
        row = next(csvreader, None)
        if row is None:
            break
        elif row[0] == "DAY":
            return_row = row
            break
        else:
            for i, data_column in enumerate(data_columns):
                data_dict[data_column].append(float(row[i]))
            data_dict["DATETIME"].append(sample_time.isoformat())

        # Increment sample count and time
        sample += 1
        sample_time += datetime.timedelta(seconds=1)

    data_df = pd.DataFrame(data_dict)

    return return_row, header_dict, data_df


def extract_dualband_datasets_from_raw_file(file: Path):
    header_dicts = []
    data_dfs = []
    unit = file.stem.split("_")[1]
    with open(file, 'r') as csvfile:
        csvreader = csv.reader(csvfile)

        # Find first dataset header
        row = next(csvreader, None)
        while not row[0] == 'DAY':
            row = next(csvreader, None)

        row, header_dict, data_df = read_dualband_dataset(file, csvreader, row)
        header_dict['UNIT'] = unit
        header_dicts.append(header_dict)
        data_dfs.append(data_df)
        while not row is None:
            row, header_dict, data_df = read_dualband_dataset(file, csvreader, row)
            header_dict['UNIT'] = unit
            header_dicts.append(header_dict)
            data_dfs.append(data_df)

        print("Finished processing file: ", file)
    return header_dicts, data_dfs
