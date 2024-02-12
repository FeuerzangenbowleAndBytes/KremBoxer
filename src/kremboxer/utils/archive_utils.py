from pathlib import Path
import datetime
import kremboxer.dualband.dualband_utils as db_utils
import kremboxer.dualband.dualband_clean as db_clean
import kremboxer.ufm.ufm_utils as ufm_utils
import kremboxer.fiveband.fiveband_utils as fb_utils


def id_sensor_from_raw_file(file: Path) -> str:
    if db_utils.is_dualband_file(file):
        return "Dualband"
    elif ufm_utils.is_ufm_file(file):
        return "UFM"
    elif fb_utils.is_fiveband_file(file):
        return "Fiveband"
    else:
        return "UNKNOWN"


def extract_datasets_from_raw_file(file: Path, sensor: str):
    if sensor == "Dualband":
        header_dicts, data_dfs = db_clean.extract_dualband_datasets_from_raw_file(file)
    elif sensor == "Fiveband":
        pass
    elif sensor == "UFM":
        pass
    else:
        print("Unknown sensor: ", sensor)
        exit(1)

    return header_dicts, data_dfs


def create_dataset_archive(params: dict):
    print("Creating dataset archive")
    data_source_directories = params["data_source_directories"]
    data_dates = [datetime.datetime.fromisoformat(x).date() for x in params["data_dates"]]

    unknown_sensor_file = []
    for data_source_directory in data_source_directories:
        print(f"Processing directory: {data_source_directory}")
        data_source_directory = Path(data_source_directory)
        for file in data_source_directory.glob('**/*.CSV'):
            sensor = id_sensor_from_raw_file(file)
            if sensor == "UNKNOWN":
                print("Unknown sensor type for file: ", file)
                unknown_sensor_file.append(file)
                continue
            print(f'{file} -> {sensor}')
            if sensor == "Dualband":
                header_dicts, data_dfs = extract_datasets_from_raw_file(file, sensor)
                print(header_dicts)

    return 0
