from pathlib import Path
import datetime


def create_dataset_archive(params: dict):
    data_source_directories = params["data_source_directories"]
    data_dates = [datetime.datetime.fromisoformat(x).date() for x in params["data_dates"]]

    for data_source_directory in data_source_directories:
        print(f"Creating dataset archive for {data_source_directory}")
        data_source_directory = Path(data_source_directory)
        for file in data_source_directory.glob('**/*.CSV'):
            print(file)
    return 0
