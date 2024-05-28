from pathlib import Path
import datetime
import pandas as pd
import numpy as np
import scipy
import kremboxer.dualband.dualband_utils as db_utils
import kremboxer.dualband.dualband_clean as db_clean
import kremboxer.ufm.ufm_utils as ufm_utils
import kremboxer.ufm.ufm_clean as ufm_clean
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
        return header_dicts, data_dfs
    elif sensor == "Fiveband":
        pass
    elif sensor == "UFM":
        header_dicts, data_dfs, ir_image_cubes = ufm_clean.extract_ufm_datasets_from_raw_file(file)
        return header_dicts, data_dfs, ir_image_cubes
    else:
        print("Unknown sensor: ", sensor)
        exit(1)


def create_dataset_archive(params: dict):
    print("Creating dataset archive")
    output_dir = Path(params["output_dir"])
    data_source_directories = params["data_source_directories"]
    data_dates = [datetime.datetime.fromisoformat(x).date() for x in params["data_dates"]]

    unknown_sensor_file = []
    metadatas = {
        "Dualband": [],
        "UFM": [],
        "Fiveband": []
    }
    for data_source_directory in data_source_directories:
        print(f"Processing directory: {data_source_directory}")
        data_source_directory = Path(data_source_directory)
        for file in data_source_directory.glob('**/*.CSV'):
            sensor = id_sensor_from_raw_file(file)
            print(f'{file} -> {sensor}')
            if sensor == "UNKNOWN":
                print("Unknown sensor type for file: ", file)
                unknown_sensor_file.append(file)
                continue
            if sensor == "Dualband":
                header_dicts, data_dfs = extract_datasets_from_raw_file(file, sensor)
                db_output_dir = output_dir.joinpath(sensor)
                db_output_dir.mkdir(exist_ok=True)
                datafiles = []
                for i, (header_dict, data_df) in enumerate(zip(header_dicts, data_dfs)):
                    unit = header_dict['UNIT']
                    dt = header_dict['DATETIME_START'].isoformat().replace(":", "-")
                    output_file = db_output_dir.joinpath(f'{sensor}_{unit}_{dt}.csv')
                    data_df.to_csv(output_file, index=False)
                    metadatas[sensor].append(header_dict)
                    metadatas[sensor][-1]['FOLDER'] = sensor
                    metadatas[sensor][-1]['DATAFILE'] = output_file.name
                    metadatas[sensor][-1]['TYPE'] = "Raw"
                    metadatas[sensor][-1]['DURATION'] = len(data_df) / header_dict['SAMPLE-RATE(Hz)']
                print(header_dicts)
            elif sensor == "UFM":
                header_dicts, data_dfs, ir_image_cubes = extract_datasets_from_raw_file(file, sensor)
                ufm_output_dir = output_dir.joinpath(sensor)
                ufm_output_dir.mkdir(exist_ok=True)
                datafiles = []
                for i, (header_dict, data_df, ir_image_cube) in enumerate(zip(header_dicts, data_dfs, ir_image_cubes)):
                    unit = header_dict['UNIT']
                    dt = header_dict['DATETIME_START'].isoformat().replace(":", "-")
                    output_file = ufm_output_dir.joinpath(f'{sensor}_{unit}_{dt}.csv')
                    data_df.to_csv(output_file, index=False)
                    metadatas[sensor].append(header_dict)
                    metadatas[sensor][-1]['FOLDER'] = sensor
                    metadatas[sensor][-1]['DATAFILE'] = output_file.name
                    metadatas[sensor][-1]['TYPE'] = "Raw"
                    metadatas[sensor][-1]['DURATION'] = len(data_df) / header_dict['SAMPLE-RATE(Hz)']

                    numpy_output_file = ufm_output_dir.joinpath(f'{sensor}_{unit}_{dt}_ir_images.npy')
                    matlab_output_file = ufm_output_dir.joinpath(f'{sensor}_{unit}_{dt}_ir_images.mat')
                    np.save(numpy_output_file, ir_image_cube)
                    scipy.io.savemat(matlab_output_file, {'ir_images': ir_image_cube})
                    metadatas[sensor][-1]['IR_IMAGE_NUMPY'] = numpy_output_file.name
                    metadatas[sensor][-1]['IR_IMAGE_MATLAB'] = matlab_output_file.name

                print(header_dicts)
            elif sensor == "Fiveband":
                pass

    for key, metadata in metadatas.items():
        print(key)
        df = pd.DataFrame(metadata)
        df.to_csv(output_dir.joinpath(f'{key}_raw_metadata.csv'), index=False)

    return 0
