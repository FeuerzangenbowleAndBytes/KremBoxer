import csv
from pathlib import Path
import datetime
from PIL import Image
import numpy as np
import pandas as pd
import geopandas as gpd
import datetime


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


def construct_ufm_header_dict(header_titles, header_values):
    header_dict = {}
    header_dict['UNIT'] = str(header_values[0])
    header_dict['DAY'] = int(header_values[1])
    header_dict['MONTH'] = int(header_values[2])
    header_dict['YEAR'] = int(header_values[3])
    header_dict['HOURS(UTC)'] = int(header_values[4])
    header_dict['MINUTES'] = int(header_values[5])
    header_dict['SECONDS'] = int(header_values[6])
    header_dict['SAMPLE-RATE(Hz)'] = float(header_values[7])
    header_dict['LATITUDE'] = float(header_values[8]) / 100000
    header_dict['LONGITUDE'] = float(header_values[9]) / 100000
    header_dict['GPS-TYPE'] = str(header_values[10])
    header_dict["DATETIME_START"] = construct_datetime(header_dict["YEAR"],
                                                       header_dict["MONTH"],
                                                       header_dict["DAY"],
                                                       header_dict["HOURS(UTC)"],
                                                       header_dict["MINUTES"],
                                                       header_dict["SECONDS"])
    return header_dict


def read_ufm_dataset(file: Path, output_directory: Path, csvreader: csv.reader, first_row: list):
    header_titles = first_row
    header_values = next(csvreader, None)
    header_dict = construct_ufm_header_dict(header_titles, header_values)
    data_columns = next(csvreader, None)
    data_dict = {}

    for data_column in data_columns:
        data_dict[data_column] = []
    data_dict["DATETIME"] = []
    data_dict["IR_IMAGE"] = []

    num_ir_rows = 24
    num_ir_cols = 32

    sample = 0
    sample_time: datetime.datetime = header_dict["DATETIME_START"]
    return_row = None
    while True:
        # Read next image data
        ir_data_array = np.zeros(shape=(num_ir_rows, num_ir_cols), dtype=float)
        row = next(csvreader, None)
        if row is None:
            break
        elif row[0] == 'UNIT':
            return_row = row
            break
        else:
            ir_data_array[0, :] = row[0:num_ir_cols]
        for i in range(1, num_ir_rows):
            row = next(csvreader, None)
            if row is None:
                print(f"IR image data incomplete at sample {sample}")
                exit()
            assert (len(row) == num_ir_cols + 1)
            ir_data_array[i, :] = row[0:num_ir_cols]
        ir_image = Image.fromarray(ir_data_array).convert("L")
        image_name = file.stem + '_' + header_dict["DATETIME_START"].isoformat()+f'_ir_image_{sample}.png'
        ir_image_dir = output_directory.joinpath(file.stem + '_' + header_dict["DATETIME_START"].isoformat()+'_ir_images')
        ir_image_dir.mkdir(parents=True, exist_ok=True)
        ir_image.save(ir_image_dir.joinpath(image_name))

        # Read next radiometer / wind data
        row = next(csvreader, None)
        for i, data_column in enumerate(data_columns):
            data_dict[data_column].append(float(row[i]))
        data_dict["IR_IMAGE"].append(image_name)
        data_dict["DATETIME"].append(sample_time.isoformat())

        # Read blank line between samples or end of file
        blank_row = next(csvreader, None)
        if blank_row is None:
            break
        if len(blank_row) > 0:
            print(f"Blank break line between samples not present at sample {sample}")
            exit()

        # Increment sample count and time
        sample += 1
        sample_time += datetime.timedelta(seconds=1)

    data_df = pd.DataFrame(data_dict)
    for key, item in header_dict.items():
        data_df.attrs[key] = item

    csv_file = file.stem + '_' + header_dict["DATETIME_START"].isoformat() + '.csv'
    data_df.to_csv(output_directory.joinpath(csv_file), index=False)
    return return_row


def process_ufm_raw_file(file: Path, output_directory: Path):
    csvreader = csv.reader(open(file, 'r'))
    row = next(csvreader, None)
    while not row[0] == 'UNIT':
        row = next(csvreader, None)

    row = read_ufm_dataset(file, output_directory, csvreader, row)
    while not row is None:
        row = read_ufm_dataset(file, output_directory, csvreader, row)

    print("Finished processing file: ", file)


def run_ufm_cleaner():
    return 0


if __name__ == "__main__":
    #test_path = Path("/home/jepaki/Projects/Objects/FortStewart2024/RadiometerTesting/test3/DATLOG8.CSV")
    test_path = Path("/home/jepaki/Projects/Objects/FortStewart2024/RadiometerData/2024-02-10/UFM/DATLOG6.CSV")
    output_dir = Path("/home/jepaki/Projects/Objects/FortStewart2024/RadiometerTesting/datalog6_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    process_ufm_raw_file(test_path, output_dir)
    run_ufm_cleaner()
