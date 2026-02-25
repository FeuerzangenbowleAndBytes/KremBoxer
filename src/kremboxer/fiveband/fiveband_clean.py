import re
import csv
from pathlib import Path
import datetime
from PIL import Image
import numpy as np
import pandas as pd
import geopandas as gpd
import datetime
import scipy
import matplotlib.pyplot as plt
import kremboxer.fiveband.fiveband_utils as fb_utils


def construct_datetime(year, month, day, hours_utc, minutes, seconds):
    if int(year) == 0:
        return datetime.datetime.min
    dt = datetime.datetime(year=int(year),
                           month=int(month),
                           day=int(day),
                           hour=int(hours_utc),
                           minute=int(minutes),
                           second=int(seconds),
                           tzinfo=datetime.timezone.utc)
    return dt

def construct_fiveband_header_dict(data_file_path: Path, fb_df: pd.DataFrame):
    datalog_file = data_file_path.stem
    datalog_parent_folder = data_file_path.parent.stem

    unit = None
    found_numbers = re.findall(r'\d+', datalog_file)
    if len(found_numbers) == 1:
        unit = int(found_numbers[0])
    elif len(datalog_parent_folder.split('FB')) > 1:
        unit = int(datalog_parent_folder.split('FB')[1])
    else:
        print(f'Unable to determine the unit for fiveband dataset: {data_file_path}')
    print(datalog_file, datalog_parent_folder)
    print(f'unit={unit}')

    header_dict = {}
    header_dict['UNIT'] = str(unit)
    start_dt: pd.Timestamp = fb_df['DATETIME'].min()
    header_dict['DAY'] = start_dt.day
    header_dict['MONTH'] = start_dt.month
    header_dict['YEAR'] = start_dt.year
    header_dict['HOURS(UTC)'] = start_dt.hour
    header_dict['MINUTES'] = start_dt.minute
    header_dict['SECONDS'] = start_dt.second
    header_dict['SAMPLE-RATE(Hz)'] = 1.0
    ave_lat = fb_df['LAT'].mean() / 100
    ave_lon = -fb_df['LONG'].mean() / 100
    header_dict['LATITUDE'] = ave_lat
    header_dict['LONGITUDE'] = ave_lon
    header_dict["DATETIME_START"] = start_dt
    return header_dict


def extract_fiveband_datasets_from_raw_file(file: Path):

    fb_data_cols = {
        'TIME': float,
        'STATUS': str,
        'LAT': float,
        'N|S': str,
        'LONG': float,
        'E|W': str,
        'SPEED': float,
        'COURSE': float,
        'DATE': float,
        'TH1': float,
        '3.95': float,
        '10.95': float,
        'TH2': float,
        'MW': float,
        'LW': float,
        'WIDE': float
    }

    csvreader = csv.reader(open(file, 'r'))
    header_dicts = []
    data_dfs = []
    optical_image_cubes = []
    ir_image_cubes = []

    # Read until beginning of first dataset, look for column titles
    row = next(csvreader, None)
    while not row is None and not row[0] == 'TIME':
        row = next(csvreader, None)

    # This would mean there is no header line in the datafile
    if row is None:
        return header_dicts, data_dfs, optical_image_cubes, ir_image_cubes

    while not row is None:
        col_labels = row
        data_dict = {}
        for col_label in col_labels:
            data_dict[col_label] = []
        row = next(csvreader, None)
        while not row is None and not row[0] == 'TIME':
            for i, col_label in enumerate(col_labels):
                if row[i]=='':
                    data_dict[col_label].append(None)
                else:
                    data_dict[col_label].append(row[i])
            row = next(csvreader, None)
        fb_df = pd.DataFrame.from_dict(data_dict, orient='columns')
        for col_label, col_type in fb_data_cols.items():
            fb_df[col_label] = fb_df[col_label].astype(col_type)

        # Figure out when the onboard GPS gets a lock and starts
        # reporting the time (HHMMSS) and date (DDMMYY)
        # Construct the datetime for that index, and then compute the
        # datetime series for the whole dataset by assuming all rows
        # are offset by 1 second
        mask = fb_df['TIME'].notna() & fb_df['DATE'].notna()
        first_datetime_index = mask.idxmax()
        dt_row = fb_df.iloc[first_datetime_index]
        date_str = str(int(dt_row['DATE']))
        time_str = str(int(dt_row['TIME']))
        day = int(date_str[0:2])
        month = int(date_str[2:4])
        year = int(date_str[4:6])
        time_str = '0' * (6 - len(time_str)) + time_str
        hour = int(time_str[0:2])
        minute = int(time_str[2:4])
        second = int(time_str[4:6])
        dt_str = f'20{year}-{month}-{day}T{hour:02}:{minute:02}:{second:02}'
        dt = pd.to_datetime(dt_str, utc=True)
        start_data_time = dt - pd.to_timedelta(first_datetime_index, unit='s')
        end_data_time = dt + pd.to_timedelta(len(fb_df)-first_datetime_index-1, unit='s')
        #print(first_datetime_index, dt, start_data_time, end_data_time)
        dt_range = pd.date_range(start=start_data_time, end=end_data_time, freq='s')
        #print(dt_range, len(dt_range), len(fb_df))
        fb_df['DATETIME'] = dt_range

        output_dir = Path("/home/oryx/Projects/Objects/RadiometerTesting/")
        fb_utils.plot_fb_df(fb_df, file.stem, output_dir)
        header_dict = construct_fiveband_header_dict(file, fb_df)
        header_dicts.append(header_dict)
        data_dfs.append(fb_df)

    return header_dicts, data_dfs, optical_image_cubes, ir_image_cubes


if __name__ == "__main__":
    #test_path = Path("/home/oryx/Projects/Objects/UNR_BurnTable/MediumLoading/DATALOG_MediumLoading_Unit1.CSV")
    test_path = Path("/home/oryx/Projects/Objects/UNR_BurnTable/LowLoading/DATALOG_LowLoading_Unit3.CSV")
    output_dir = Path("/home/oryx/Projects/Objects/RadiometerTesting/")
    output_dir.mkdir(parents=True, exist_ok=True)
    header_dicts, data_dfs, optical_image_cubes, ir_image_cubes = extract_fiveband_datasets_from_raw_file(test_path)
    #print(header_dicts)
    #print(data_dfs)
    #print(len(ir_image_cubes), ir_image_cubes[0].shape)
